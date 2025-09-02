#!/usr/bin/env python3
"""
OPTIMADE MCP Client
===================

这是一个专门为OPTIMADE MCP Server设计的客户端程序，基于MCP协议实现。
支持与OPTIMADE数据库进行自然语言交互，查询材料科学数据。

主要功能：
- 连接到OPTIMADE MCP Server（支持本地脚本或HTTP/SSE URL）
- 支持自然语言查询转换为OPTIMADE过滤器
- 执行OPTIMADE查询并展示结果
- 提供交互式聊天界面
- 支持OpenAI和OpenRouter API

作者: 基于MCP协议开发
版本: 1.0.1
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

# MCP相关导入
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.http import HttpClientTransport
from mcp.client.sse import SseClientTransport

# OpenAI SDK导入
import openai
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("optimade_mcp_client")

# 加载环境变量
load_dotenv()

class OptimadeMCPClient:
    """
    OPTIMADE MCP客户端类
    
    负责管理与OPTIMADE MCP Server的连接，处理用户查询，
    并将自然语言转换为OPTIMADE查询过滤器。
    支持OpenAI和OpenRouter API，以及本地脚本或HTTP/SSE连接。
    """
    
    def __init__(self):
        """
        初始化OPTIMADE MCP客户端
        
        设置OpenAI/OpenRouter客户端、MCP会话管理和资源清理
        """
        # 初始化API客户端
        api_provider = os.getenv("API_PROVIDER", "openai").lower()
        api_key = os.getenv("OPENAI_API_KEY") if api_provider == "openai" else os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            raise ValueError(f"请设置 {'OPENAI_API_KEY' if api_provider == 'openai' else 'OPENROUTER_API_KEY'} 环境变量")
        
        # 配置OpenAI或OpenRouter客户端
        self.openai_client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1" if api_provider == "openrouter" else None
        )
        logger.info(f"使用 {api_provider.capitalize()} API 初始化客户端")
        
        # MCP会话管理
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # 可用的工具列表
        self.available_tools: List[Dict[str, Any]] = []
        
        # 查询历史记录
        self.query_history: List[Dict[str, Any]] = []
        
        logger.info("OPTIMADE MCP客户端初始化完成")

    async def connect_to_server(self, server: str, transport: str = "stdio") -> None:
        """
        连接到OPTIMADE MCP Server
        
        Args:
            server: 服务器脚本路径或URL地址（例如 http://localhost:8080/mcp）
            transport: 连接方式（stdio, http, sse），默认stdio
            
        Raises:
            ValueError: 当服务器脚本或URL格式不支持时
            Exception: 连接失败时
        """
        try:
            if transport == "stdio":
                # 验证服务器脚本类型
                is_python = server.endswith('.py')
                is_js = server.endswith('.js')
                
                if not (is_python or is_js):
                    raise ValueError("服务器脚本必须是.py或.js文件")
                
                # 确定执行命令
                command = "python" if is_python else "node"
                server_params = StdioServerParameters(
                    command=command,
                    args=[server],
                    env=None
                )
                
                logger.info(f"通过stdio连接到本地服务器脚本: {server}")
                
                # 建立stdio传输连接
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                self.stdio, self.stdin = stdio_transport
                
                # 创建MCP会话
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(self.stdio, self.stdin)
                )
                
            elif transport in ("http", "sse"):
                # 验证URL格式
                if not re.match(r'^https?://', server):
                    raise ValueError("服务器地址必须以 http:// 或 https:// 开头")
                
                logger.info(f"通过{transport.upper()}连接到服务器: {server}")
                
                # 根据传输方式选择客户端
                if transport == "http":
                    transport_obj = await self.exit_stack.enter_async_context(
                        HttpClientTransport(server)
                    )
                else:  # sse
                    transport_obj = await self.exit_stack.enter_async_context(
                        SseClientTransport(server)
                    )
                
                # 创建MCP会话
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(transport_obj, None)
                )
                
            else:
                raise ValueError("不支持的传输方式: 必须是 stdio、http 或 sse")
            
            # 初始化会话
            await self.session.initialize()
            
            # 获取可用工具列表
            await self._load_available_tools()
            
            # 获取可用资源列表
            await self._load_available_resources()
            
            logger.info(f"成功连接到OPTIMADE MCP Server ({transport.upper()} 模式)")
            
        except Exception as e:
            logger.error(f"连接服务器失败: {str(e)}")
            raise

    async def _load_available_tools(self) -> None:
        """
        加载服务器提供的可用工具列表
        
        获取所有可用的工具，包括query_optimade、list_providers等
        """
        try:
            response = await self.session.list_tools()
            self.available_tools = [{
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in response.tools]
            
            logger.info(f"发现可用工具: {[tool['name'] for tool in self.available_tools]}")
            
        except Exception as e:
            logger.error(f"加载工具列表失败: {str(e)}")
            self.available_tools = []

    async def _load_available_resources(self) -> None:
        """
        加载服务器提供的可用资源列表
        
        获取所有可用的资源，包括文档、配置等
        """
        try:
            response = await self.session.list_resources()
            resources = [resource.uri for resource in response.resources]
            logger.info(f"发现可用资源: {resources}")
            
        except Exception as e:
            logger.error(f"加载资源列表失败: {str(e)}")

    async def process_query(self, query: str) -> str:
        """
        处理用户查询，使用OpenAI/OpenRouter模型和MCP工具
        
        Args:
            query: 用户的自然语言查询
            
        Returns:
            处理结果的文本表示
        """
        try:
            logger.info(f"处理查询: {query}")
            
            # 构建消息历史
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user", 
                    "content": query
                }
            ]
            
            # 将MCP工具转换为OpenAI工具格式
            openai_tools = self._convert_mcp_tools_to_openai()
            
            # 调用API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4" if os.getenv("API_PROVIDER", "openai").lower() == "openai" else "openai/gpt-4o",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                max_tokens=2000
            )
            
            # 处理响应和工具调用
            final_text = []
            assistant_message_content = []
            
            for content in response.choices[0].message.content or []:
                if hasattr(content, 'text'):
                    final_text.append(content.text)
                    assistant_message_content.append(content)
                elif hasattr(content, 'tool_calls'):
                    # 处理工具调用
                    for tool_call in content.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"调用工具: {tool_name}, 参数: {tool_args}")
                        
                        # 执行MCP工具调用
                        result = await self._execute_mcp_tool(tool_name, tool_args)
                        
                        final_text.append(f"[工具调用: {tool_name}]")
                        final_text.append(f"参数: {json.dumps(tool_args, ensure_ascii=False, indent=2)}")
                        final_text.append(f"结果: {result}")
                        
                        # 将工具结果添加到消息历史
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message_content
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result)
                        })
                        
                        # 获取后续响应
                        follow_up_response = await self.openai_client.chat.completions.create(
                            model="gpt-4" if os.getenv("API_PROVIDER", "openai").lower() == "openai" else "openai/gpt-4o",
                            messages=messages,
                            max_tokens=1000
                        )
                        
                        if follow_up_response.choices[0].message.content:
                            final_text.append(follow_up_response.choices[0].message.content)
            
            # 记录查询历史
            self._record_query_history(query, final_text)
            
            return "\n".join(final_text)
            
        except Exception as e:
            error_msg = f"处理查询时发生错误: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _get_system_prompt(self) -> str:
        """
        获取系统提示词，指导AI如何与OPTIMADE系统交互
        
        Returns:
            系统提示词文本
        """
        return """你是一个专业的材料科学助手，专门帮助用户查询OPTIMADE数据库。

你的主要职责：
1. 理解用户的材料科学查询需求
2. 将自然语言转换为合适的OPTIMADE查询过滤器
3. 使用可用的工具来获取数据
4. 以清晰易懂的方式解释结果

可用的工具：
- query_optimade: 执行OPTIMADE查询
- list_providers: 列出可用的数据库提供商
- lint_filter: 验证查询过滤器的语法

请始终：
- 使用准确的科学术语
- 提供清晰的解释
- 在需要时使用工具获取最新数据
- 以中文回复用户"""

    def _convert_mcp_tools_to_openai(self) -> List[Dict[str, Any]]:
        """
        将MCP工具格式转换为OpenAI工具格式
        
        Returns:
            OpenAI格式的工具列表
        """
        openai_tools = []
        
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"] or "",
                    "parameters": tool["input_schema"] or {}
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools

    async def _execute_mcp_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """
        执行MCP工具调用
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if not self.session:
                raise RuntimeError("MCP会话未建立")
            
            # 调用MCP工具
            result = await self.session.call_tool(tool_name, tool_args)
            
            # 处理结果内容
            if hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
                
        except Exception as e:
            error_msg = f"执行工具 {tool_name} 失败: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _record_query_history(self, query: str, response: List[str]) -> None:
        """
        记录查询历史
        
        Args:
            query: 用户查询
            response: 系统响应
        """
        history_entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "query": query,
            "response": response
        }
        self.query_history.append(history_entry)
        
        # 保持历史记录在合理范围内
        if len(self.query_history) > 100:
            self.query_history.pop(0)

    async def chat_loop(self) -> None:
        """
        运行交互式聊天循环
        
        提供命令行界面，让用户与OPTIMADE系统进行对话
        """
        print("\n" + "="*60)
        print("🎯 OPTIMADE MCP 客户端已启动!")
        print("="*60)
        print("💡 你可以用自然语言查询材料科学数据")
        print("🔧 支持的工具:", [tool['name'] for tool in self.available_tools])
        print("📚 输入 'help' 查看帮助，'quit' 退出程序")
        print("="*60)

        while True:
            try:
                query = input("\n🤔 请输入你的查询: ").strip()
                
                if not query:
                    continue
                    
                if query.lower() == 'quit':
                    print("👋 再见！")
                    break
                    
                if query.lower() == 'help':
                    self._show_help()
                    continue
                    
                if query.lower() == 'history':
                    self._show_history()
                    continue
                    
                if query.lower() == 'tools':
                    self._show_tools()
                    continue
                
                print("\n🔄 正在处理查询...")
                response = await self.process_query(query)
                
                print("\n" + "="*60)
                print("📝 查询结果:")
                print("="*60)
                print(response)
                print("="*60)
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断，正在退出...")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {str(e)}")
                logger.error(f"聊天循环错误: {str(e)}")

    def _show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
📖 帮助信息
==========

基本命令:
- help: 显示此帮助信息
- history: 显示查询历史
- tools: 显示可用工具
- quit: 退出程序

查询示例:
- "查找所有包含银元素的材料"
- "查询带隙大于2.0 eV的半导体材料"
- "列出可用的数据库提供商"
- "验证过滤器语法: elements HAS 'Si' AND nelements>=2"

提示:
- 使用清晰的材料科学术语
- 可以询问具体的材料属性
- 系统会自动选择合适的查询策略
"""
        print(help_text)

    def _show_history(self) -> None:
        """显示查询历史"""
        if not self.query_history:
            print("📚 暂无查询历史")
            return
            
        print(f"\n📚 查询历史 (共{len(self.query_history)}条):")
        print("="*60)
        
        for i, entry in enumerate(self.query_history[-10:], 1):  # 显示最近10条
            print(f"{i}. 查询: {entry['query'][:50]}...")
            print(f"   时间: {entry['timestamp']:.1f}s")
            print()

    def _show_tools(self) -> None:
        """显示可用工具"""
        if not self.available_tools:
            print("🔧 暂无可用工具")
            return
            
        print(f"\n🔧 可用工具 (共{len(self.available_tools)}个):")
        print("="*60)
        
        for tool in self.available_tools:
            print(f"📌 {tool['name']}")
            if tool['description']:
                print(f"   描述: {tool['description']}")
            print()

    async def cleanup(self) -> None:
        """
        清理资源
        
        关闭MCP会话和清理相关资源
        """
        try:
            await self.exit_stack.aclose()
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理时发生错误: {str(e)}")

async def main():
    """
    主函数
    
    程序入口点，处理命令行参数并启动客户端
    """
    if len(sys.argv) < 2:
        print("❌ 使用方法: python mcp_client.py <MCP_Server_脚本路径或URL>")
        print("   示例: python mcp_client.py ../optimade-mcp-server/src/optimade_mcp_server/main.py")
        print("   或: python mcp_client.py http://localhost:8080/mcp")
        sys.exit(1)
    
    server = sys.argv[1]
    
    # 确定连接方式
    transport = "stdio"
    if server.startswith("http://") or server.startswith("https://"):
        transport = "http" if "/mcp" in server else "sse" if "/sse" in server else "http"
    
    # 检查服务器脚本是否存在（仅对stdio模式）
    if transport == "stdio" and not Path(server).exists():
        print(f"❌ 服务器脚本不存在: {server}")
        sys.exit(1)
    
    client = OptimadeMCPClient()
    
    try:
        # 连接到服务器
        await client.connect_to_server(server, transport)
        
        # 启动聊天循环
        await client.chat_loop()
        
    except Exception as e:
        print(f"❌ 程序运行失败: {str(e)}")
        logger.error(f"主程序错误: {str(e)}")
        sys.exit(1)
        
    finally:
        # 清理资源
        await client.cleanup()

if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())