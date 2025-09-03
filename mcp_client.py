#!/usr/bin/env python3
"""
OPTIMADE MCP Client
- 兼容 stdio / streamable-http / sse
- OpenAI / OpenRouter / DeepSeek 官方 API（OpenAI 兼容）驱动（函数调用）
"""

import asyncio
import json
import logging
import os
import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack

# ✅ 官方 Python SDK（正确的导入路径）
from mcp import ClientSession, StdioServerParameters, types as mcp_types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client

from dotenv import load_dotenv
import openai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("optimade_mcp_client")

load_dotenv()

class OptimadeMCPClient:
    def __init__(self, default_model: Optional[str] = None):
        provider = os.getenv("API_PROVIDER", "openai").lower()

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")  # 可留空
            if not api_key:
                raise ValueError("请设置 OPENAI_API_KEY")
            self.llm = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
            self.model = default_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        elif provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("请设置 OPENROUTER_API_KEY")
            self.llm = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            )
            configured = default_model or os.getenv("OPENROUTER_MODEL")
            self.model = self._pick_openrouter_tools_model(configured)

        elif provider == "deepseek":
            # ✅ 直接走 DeepSeek 官方 API（OpenAI 兼容）
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            if not api_key:
                raise ValueError("请设置 DEEPSEEK_API_KEY")
            # 与 OpenAI 兼容的 Chat Completions 接口；工具调用同格式
            self.llm = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            # 官方文档示例使用 deepseek-chat；deepseek-reasoner（V3.1思考模式）也可用
            self.model = default_model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        else:
            raise ValueError(f"不支持的 API_PROVIDER: {provider}")

        self.provider = provider
        logger.info(f"使用 {provider.capitalize()}，模型：{self.model}")

        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[Dict[str, Any]] = []
        self.query_history: List[Dict[str, Any]] = []

    # —— OpenRouter: 自动选择支持 tools 的路由 —— #
    def _pick_openrouter_tools_model(self, configured: Optional[str]) -> str:
        """
        尊重用户配置的 OpenRouter 路由；如果未配置就用一个常见且支持 tools 的默认值。
        如果该路由后续真的不支持工具，会在首轮请求抛 404，再在异常里回退。
        """
        return configured or "openai/gpt-4o-mini"


    async def connect_to_server(self, server: str, transport: str = "stdio") -> None:
        logger.info(f"连接服务器：{server}，传输：{transport}")

        if transport == "stdio":
            is_python = server.endswith(".py")
            is_js = server.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("STDIO 模式下服务器脚本必须是 .py 或 .js")
            command = "python" if is_python else "node"
            params = StdioServerParameters(command=command, args=[server], env=None)
            read_stream, write_stream = await self.exit_stack.enter_async_context(stdio_client(params))

        elif transport == "http":
            cm = streamablehttp_client(server)
            result = await self.exit_stack.enter_async_context(cm)
            if isinstance(result, tuple) and len(result) == 3:
                read_stream, write_stream, _ = result
            else:
                read_stream, write_stream = result

        elif transport == "sse":
            cm = sse_client(server)
            result = await self.exit_stack.enter_async_context(cm)
            if isinstance(result, tuple) and len(result) == 3:
                read_stream, write_stream, _ = result
            else:
                read_stream, write_stream = result

        else:
            raise ValueError("不支持的传输方式")

        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()

        await self._load_available_tools()
        await self._load_available_resources()
        logger.info(f"已连接到 MCP Server（{transport.upper()}）")

    async def _load_available_tools(self) -> None:
        try:
            response = await self.session.list_tools()
            self.available_tools = [{
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema
            } for t in response.tools]
            logger.info("发现工具：%s", [t["name"] for t in self.available_tools])
        except Exception as e:
            logger.error("加载工具失败：%s", e)
            self.available_tools = []

    async def _load_available_resources(self) -> None:
        try:
            response = await self.session.list_resources()
            logger.info("发现资源：%s", [r.uri for r in response.resources])
        except Exception as e:
            logger.error("加载资源失败：%s", e)

    # —— MCP 工具映射到 OpenAI 函数调用 —— #
    def _convert_mcp_tools_to_openai(self) -> List[Dict[str, Any]]:
        tools = []
        for t in self.available_tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description") or "",
                    "parameters": t.get("input_schema") or {"type": "object", "properties": {}}
                }
            })
        return tools

    # —— 格式化 MCP 工具返回 —— #
    def _format_tool_result(self, result: Any) -> str:
        try:
            parts = []
            if getattr(result, "structuredContent", None):
                parts.append(json.dumps(result.structuredContent, ensure_ascii=False, indent=2))
            for c in getattr(result, "content", []) or []:
                if isinstance(c, mcp_types.TextContent):
                    parts.append(c.text)
                elif isinstance(c, mcp_types.ImageContent):
                    size = len(c.data) if getattr(c, "data", None) else 0
                    parts.append(f"[image {c.mimeType} {size} bytes]")
                else:
                    parts.append(str(c))
            return "\n".join([p for p in parts if p]) or str(result)
        except Exception:
            return str(result)

    async def _execute_mcp_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        try:
            if not self.session:
                raise RuntimeError("MCP 会话未建立")
            return await self.session.call_tool(tool_name, tool_args)
        except Exception as e:
            logger.error("执行工具 %s 失败：%s", tool_name, e)
            return f"<<tool {tool_name} failed: {e}>>"

    # —— 主处理：自然语言 -> 模型 -> 工具调用 —— #
    async def process_query(self, query: str) -> str:
        logger.info("处理查询：%s", query)

        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": query},
        ]
        tools = self._convert_mcp_tools_to_openai()

        async def _call_with_tools():
            return await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=1200
            )

        # 首次调用（OpenRouter 如不支持 tools，会在这里抛 404，我们在 except 里回退）
        try:
            resp = await _call_with_tools()
        except openai.NotFoundError as e:
            if self.provider == "openrouter" and "support tool use" in str(e).lower():
                fallback = "openai/gpt-4o-mini"
                logger.warning("OpenRouter 路由不支持工具，回退到 %s", fallback)
                self.model = fallback
                resp = await _call_with_tools()
            else:
                raise

        final_chunks: List[str] = []
        msg = resp.choices[0].message

        if msg.content:
            final_chunks.append(msg.content)

        if getattr(msg, "tool_calls", None):
            # 把带 tool_calls 的 assistant 原样放入消息历史
            assistant_msg = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
            messages.append(assistant_msg)

            # 执行每个工具，并把 tool 结果加进去
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                logger.info("调用工具：%s %s", name, args)

                result = await self._execute_mcp_tool(name, args)
                result_text = self._format_tool_result(result)
                final_chunks.append(
                    f"[工具调用 {name}]\n参数: {json.dumps(args, ensure_ascii=False)}\n结果:\n{result_text}"
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text
                })

            # 二次总结（通常不再传 tools，以免继续走工具）
            follow = await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000
            )
            if follow.choices[0].message.content:
                final_chunks.append(follow.choices[0].message.content)

        self._record_history(query, final_chunks)
        return "\n".join(ch for ch in final_chunks if ch)


    def _system_prompt(self) -> str:
        return (
            "你是材料科学助手，帮助用户对接 OPTIMADE。\n"
            "1) 将中文需求转换为 OPTIMADE 过滤器；2) 必要时调用工具获取数据；3) 返回清晰解释。\n"
            "可用工具：query_optimade / list_providers / lint_filter。\n"
            "优先使用准确术语；输出中文。"
        )

    def _record_history(self, query: str, chunks: List[str]) -> None:
        self.query_history.append({
            "query": query,
            "response": chunks
        })
        if len(self.query_history) > 100:
            self.query_history.pop(0)

    async def chat_loop(self) -> None:
        print("\n================ MCP Client ================")
        print("输入 natural language 查询（help/history/tools/quit）")
        while True:
            try:
                q = input("\n> ").strip()
                if not q:
                    continue
                if q.lower() == "quit":
                    print("bye.")
                    break
                if q.lower() == "help":
                    print("help: history/tools/quit；示例：查询带隙>2eV 的材料")
                    continue
                if q.lower() == "history":
                    print(json.dumps(self.query_history[-5:], ensure_ascii=False, indent=2))
                    continue
                if q.lower() == "tools":
                    print([t["name"] for t in self.available_tools])
                    continue
                print("\n[处理中] ...")
                ans = await self.process_query(q)
                print("\n=== 结果 ===\n" + ans + "\n============")
            except KeyboardInterrupt:
                print("\n中断，退出。")
                break
            except Exception as e:
                print(f"\n❌ 错误：{e}")
                logger.exception("chat_loop error")

    async def cleanup(self) -> None:
        try:
            await self.exit_stack.aclose()
            logger.info("清理完成")
        except Exception as e:
            logger.error("清理异常：%s", e)


# 可单独运行
async def main():
    if len(sys.argv) < 2:
        print("❌ 用法: python mcp_client.py <MCP_Server_脚本路径或URL>")
        print("   例:  python mcp_client.py http://localhost:8080/mcp")
        sys.exit(1)

    server = sys.argv[1]
    transport = "stdio"
    if server.startswith(("http://", "https://")):
        transport = "http" if "/mcp" in server else "sse" if "/sse" in server else "http"

    if transport == "stdio" and not Path(server).exists():
        print(f"❌ 服务器脚本不存在: {server}")
        sys.exit(1)

    client = OptimadeMCPClient()
    try:
        await client.connect_to_server(server, transport)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
