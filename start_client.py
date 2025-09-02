#!/usr/bin/env python3
"""
OPTIMADE MCP Client 启动脚本
============================

简化启动入口，负责加载环境配置并启动客户端。
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio

# 默认的 OPTIMADE MCP Server 路径
SERVER_PATH = "../optimade-mcp-server/src/optimade_mcp_server/main.py"
ENV_FILE = ".env"

def check_env():
    """检查环境变量文件"""
    if not Path(ENV_FILE).exists():
        print("❌ 未找到 .env 文件，请复制 config.env.example 为 .env 并填入你的 OpenAI API 密钥")
        sys.exit(1)
    load_dotenv(ENV_FILE)

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 未设置 OPENAI_API_KEY，请在 .env 文件或系统环境变量中配置")
        sys.exit(1)

def check_server_path():
    """检查 MCP Server 路径"""
    if not Path(SERVER_PATH).exists():
        print(f"❌ 服务器脚本不存在: {SERVER_PATH}")
        sys.exit(1)
    return SERVER_PATH

async def main():
    check_env()
    server_path = check_server_path()

    # 延迟导入，避免无关 ImportError
    from mcp_client import OptimadeMCPClient

    client = OptimadeMCPClient()
    try:
        await client.connect_to_server(server_path)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
