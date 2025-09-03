#!/usr/bin/env python3
"""
OPTIMADE MCP Client 启动脚本
- 支持三种传输：stdio / http(=Streamable HTTP) / sse
- 自动根据 --server / --server-url 猜测传输方式
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

DEFAULT_SERVER_SCRIPT = "../optimade-mcp-server/src/optimade_mcp_server/main.py"

def parse_args():
    p = argparse.ArgumentParser(description="OPTIMADE MCP Client Starter")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--server", help="本地服务器脚本路径（.py/.js），使用 STDIO 连接")
    g.add_argument("--server-url", help="远程服务器 URL（/mcp 或 /sse）")
    p.add_argument("--transport", choices=["auto", "stdio", "http", "sse"], default="auto",
                   help="强制指定传输类型（默认 auto）")
    p.add_argument("--model", default=None, help="覆盖默认模型（OpenAI/OpenRouter）")
    return p.parse_args()

# start_client.py — 只展示差异关键段

def check_env():
    load_dotenv(".env")
    api_provider = os.getenv("API_PROVIDER", "openai").lower()

    if api_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 未设置 OPENAI_API_KEY")
            sys.exit(1)

    elif api_provider == "openrouter":
        if not os.getenv("OPENROUTER_API_KEY"):
            print("❌ 未设置 OPENROUTER_API_KEY")
            sys.exit(1)

    elif api_provider == "deepseek":
        if not os.getenv("DEEPSEEK_API_KEY"):
            print("❌ 未设置 DEEPSEEK_API_KEY")
            sys.exit(1)
        # 可选提示：base_url 缺失则采用默认
        if not os.getenv("DEEPSEEK_BASE_URL"):
            print("ℹ️ 未设置 DEEPSEEK_BASE_URL，将使用默认：https://api.deepseek.com")

    else:
        print(f"❌ 不支持的 API_PROVIDER: {api_provider}")
        sys.exit(1)


def infer_transport(server: str, transport: str) -> str:
    if transport != "auto":
        return transport
    if server.startswith("http://") or server.startswith("https://"):
        # /mcp -> Streamable HTTP, /sse -> SSE，默认优先 HTTP
        if "/sse" in server:
            return "sse"
        return "http"
    # 否则认为是本地脚本
    return "stdio"

async def main():
    check_env()
    args = parse_args()

    server = args.server or args.server_url or DEFAULT_SERVER_SCRIPT
    transport = infer_transport(server, args.transport)

    if transport == "stdio" and not Path(server).exists():
        print(f"❌ 本地服务器脚本不存在: {server}")
        sys.exit(1)

    # 延迟导入，避免无关 ImportError
    from mcp_client import OptimadeMCPClient

    client = OptimadeMCPClient(default_model=args.model)
    try:
        await client.connect_to_server(server, transport=transport)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
