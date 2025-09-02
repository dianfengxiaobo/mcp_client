#!/usr/bin/env python3
"""
OPTIMADE MCP Client 查询示例
============================

这个脚本展示了如何使用OPTIMADE MCP Client进行各种类型的查询。
可以作为用户学习和参考的示例。

使用方法:
1. 确保已安装并配置好客户端
2. 修改下面的SERVER_PATH为你的服务器路径
3. 运行: python examples/example_queries.py
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到路径，以便导入mcp_client
sys.path.append(str(Path(__file__).parent.parent))

from mcp_client import OptimadeMCPClient

# 配置区域 - 请根据你的环境修改
SERVER_PATH = "../optimade-mcp-server/src/optimade_mcp_server/main.py"

# 示例查询列表
EXAMPLE_QUERIES = [
    "列出可用的数据库提供商",
    "查找所有包含银元素的材料",
    "查询带隙大于2.0 eV的半导体材料",
    "验证过滤器语法: elements HAS 'Si' AND nelements>=2",
    "查找密度小于5 g/cm³的轻质材料",
    "查询具有立方晶系的材料",
    "查找包含稀土元素的材料",
    "查询带隙在1.0到3.0 eV之间的材料",
    "查找具有高对称性的材料",
    "查询包含过渡金属的材料"
]

async def run_example_queries():
    """运行示例查询"""
    print("🧪 OPTIMADE MCP Client 查询示例")
    print("=" * 60)
    
    # 创建客户端
    client = OptimadeMCPClient()
    
    try:
        # 连接到服务器
        print("🔗 正在连接到服务器...")
        await client.connect_to_server(SERVER_PATH)
        print("✅ 连接成功!")
        
        print(f"\n📊 发现 {len(client.available_tools)} 个可用工具:")
        for tool in client.available_tools:
            print(f"  - {tool['name']}: {tool['description'] or '无描述'}")
        
        print("\n" + "=" * 60)
        print("🚀 开始运行示例查询...")
        print("=" * 60)
        
        # 运行示例查询
        for i, query in enumerate(EXAMPLE_QUERIES, 1):
            print(f"\n📝 示例 {i}/{len(EXAMPLE_QUERIES)}")
            print(f"查询: {query}")
            print("-" * 40)
            
            try:
                # 执行查询
                response = await client.process_query(query)
                
                # 显示结果摘要
                print("结果摘要:")
                if len(response) > 200:
                    print(f"{response[:200]}...")
                    print(f"[完整响应长度: {len(response)} 字符]")
                else:
                    print(response)
                    
            except Exception as e:
                print(f"❌ 查询失败: {e}")
            
            print("-" * 40)
            
            # 添加延迟，避免API限制
            if i < len(EXAMPLE_QUERIES):
                print("⏳ 等待3秒后继续下一个查询...")
                await asyncio.sleep(3)
        
        print("\n" + "=" * 60)
        print("🎉 所有示例查询完成!")
        print("=" * 60)
        
        # 显示查询历史
        print(f"\n📚 查询历史记录: {len(client.query_history)} 条")
        
    except Exception as e:
        print(f"❌ 运行示例时发生错误: {e}")
        
    finally:
        # 清理资源
        await client.cleanup()

def main():
    """主函数"""
    if not Path(SERVER_PATH).exists():
        print(f"❌ 服务器脚本不存在: {SERVER_PATH}")
        print("请修改 SERVER_PATH 为正确的路径")
        sys.exit(1)
    
    # 运行示例
    asyncio.run(run_example_queries())

if __name__ == "__main__":
    main()
