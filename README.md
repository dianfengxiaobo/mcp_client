# OPTIMADE MCP Client

## 🚀 快速开始

### 安装步骤

1. **克隆或下载项目**
   ```bash
   # 如果从GitHub克隆
   git clone <repository-url>
   cd optimade-mcp-client
   
   # 或者直接下载文件到本地目录
   ```

2. **安装依赖**
   ```bash
   uv sync
   ```

3. **配置环境变量**
   项目文件中有.env示例文件需要添加大模型的api供应商等信息。


4. **启动客户端**
   ```bash
   # 方式1: 使用启动脚本（推荐）
   python start_client.py
   
   # 方式2: 直接运行
   python mcp_client.py path/to/your/server.py
   ```

## 📖 使用方法

### 基本命令

启动客户端后，你可以使用以下命令：

- `help` - 显示帮助信息
- `history` - 显示查询历史
- `tools` - 显示可用工具
- `quit` - 退出程序


### 工具功能

客户端自动集成了以下MCP工具：

- **`query_optimade`**: 执行OPTIMADE查询
- **`list_providers`**: 列出可用的数据库提供商
- **`lint_filter`**: 验证查询过滤器的语法


## 🔧 开发指南

### 项目结构

```
optimade-mcp-client/
├── mcp_client.py          # 主客户端程序
├── start_client.py        # 启动脚本
├── config.env.example     # 环境变量模板
└── README.md             # 说明文档
```

## 📚 相关资源

- [MCP协议官方文档](https://modelcontextprotocol.io/)
- [OPTIMADE标准](https://www.optimade.org/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [Python异步编程指南](https://docs.python.org/3/library/asyncio.html)


## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件