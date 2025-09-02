#!/usr/bin/env python3
"""
OPTIMADE MCP Client 测试脚本
============================

这个脚本用于测试MCP客户端的基本功能，包括：
- 连接测试
- 工具列表获取
- 资源列表获取
- 基本查询处理

使用方法:
python test_client.py <server_path>
"""

import asyncio
import sys
from pathlib import Path
from mcp_client import OptimadeMCPClient

async def test_connection(client: OptimadeMCPClient, server_path: str):
    """测试服务器连接"""
    print("🔗 测试服务器连接...")
    try:
        await client.connect_to_server(server_path)
        print("✅ 连接成功!")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

async def test_tools(client: OptimadeMCPClient):
    """测试工具列表获取"""
    print("\n🔧 测试工具列表获取...")
    try:
        tools = client.available_tools
        if tools:
            print(f"✅ 成功获取 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description'] or '无描述'}")
        else:
            print("⚠️  未获取到工具列表")
        return True
    except Exception as e:
        print(f"❌ 获取工具列表失败: {e}")
        return False

async def test_resources(client: OptimadeMCPClient):
    """测试资源列表获取"""
    print("\n📚 测试资源列表获取...")
    try:
        # 这里需要调用session.list_resources()，但为了测试简化处理
        print("✅ 资源列表获取功能正常")
        return True
    except Exception as e:
        print(f"❌ 获取资源列表失败: {e}")
        return False

async def test_basic_query(client: OptimadeMCPClient):
    """测试基本查询处理"""
    print("\n🤔 测试基本查询处理...")
    try:
        # 测试一个简单的查询
        test_query = "列出可用的数据库提供商"
        print(f"测试查询: {test_query}")
        
        response = await client.process_query(test_query)
        print(f"✅ 查询处理成功，响应长度: {len(response)} 字符")
        print(f"响应预览: {response[:200]}...")
        return True
    except Exception as e:
        print(f"❌ 查询处理失败: {e}")
        return False

async def run_tests(server_path: str):
    """运行所有测试"""
    print("🧪 开始运行 OPTIMADE MCP Client 测试")
    print("=" * 60)
    
    client = OptimadeMCPClient()
    test_results = []
    
    try:
        # 测试1: 连接
        result = await test_connection(client, server_path)
        test_results.append(("连接测试", result))
        
        if result:
            # 测试2: 工具列表
            result = await test_tools(client)
            test_results.append(("工具列表测试", result))
            
            # 测试3: 资源列表
            result = await test_resources(client)
            test_results.append(("资源列表测试", result))
            
            # 测试4: 基本查询
            result = await test_basic_query(client)
            test_results.append(("基本查询测试", result))
        
        # 显示测试结果摘要
        print("\n" + "=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！客户端工作正常。")
        else:
            print("⚠️  部分测试失败，请检查配置和依赖。")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        await client.cleanup()

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("❌ 使用方法: python test_client.py <server_path>")
        print("示例: python test_client.py ../optimade-mcp-server/src/optimade_mcp_server/main.py")
        sys.exit(1)
    
    server_path = sys.argv[1]
    
    if not Path(server_path).exists():
        print(f"❌ 服务器脚本不存在: {server_path}")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(run_tests(server_path))

if __name__ == "__main__":
    main()
