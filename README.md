# OPTIMADE MCP Client

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🎯 **专门为OPTIMADE MCP Server设计的智能客户端程序**

这是一个基于MCP（Model Context Protocol）协议的Python客户端，专门用于与OPTIMADE数据库进行自然语言交互。通过集成OpenAI等大语言模型，用户可以用自然语言查询材料科学数据，系统会自动转换为OPTIMADE查询过滤器并执行查询。

## ✨ 主要特性

- 🔗 **MCP协议支持**: 完全兼容MCP协议，支持所有MCP功能
- 🤖 **AI驱动查询**: 集成OpenAI模型，自然语言转OPTIMADE查询
- 🧪 **材料科学专用**: 针对材料科学查询优化的系统提示词
- 🛠️ **工具集成**: 支持query_optimade、list_providers、lint_filter等工具
- 📚 **资源管理**: 自动加载和展示可用的MCP资源
- 💬 **交互式界面**: 友好的命令行聊天界面
- 📝 **查询历史**: 记录和查看查询历史
- 🔧 **易于配置**: 简单的环境变量配置

## 🚀 快速开始

### 系统要求

- Python 3.8 或更高版本
- OpenAI API密钥
- OPTIMADE MCP Server

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
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 复制配置模板
   cp config.env.example .env
   
   # 编辑.env文件，填入你的OpenAI API密钥
   OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **配置服务器路径**
   
   编辑 `start_client.py` 文件，修改 `SERVER_PATH` 为你的OPTIMADE MCP Server路径：
   ```python
   SERVER_PATH = "path/to/your/optimade-mcp-server/main.py"
   ```

5. **启动客户端**
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

### 查询示例

客户端支持各种自然语言查询，例如：

```
🤔 请输入你的查询: 查找所有包含银元素的材料
🤔 请输入你的查询: 查询带隙大于2.0 eV的半导体材料
🤔 请输入你的查询: 列出可用的数据库提供商
🤔 请输入你的查询: 验证过滤器语法: elements HAS 'Si' AND nelements>=2
```

### 工具功能

客户端自动集成了以下MCP工具：

- **`query_optimade`**: 执行OPTIMADE查询
- **`list_providers`**: 列出可用的数据库提供商
- **`lint_filter`**: 验证查询过滤器的语法

## 🏗️ 架构设计

### 核心组件

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   用户界面      │    │   MCP客户端      │    │  OPTIMADE      │
│  (聊天循环)     │◄──►│   (会话管理)     │◄──►│  MCP Server    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAI API    │    │   工具转换器      │    │   OPTIMADE      │
│  (自然语言处理) │    │  (MCP→OpenAI)    │    │   数据库        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 工作流程

1. **连接建立**: 客户端连接到OPTIMADE MCP Server
2. **工具发现**: 自动发现服务器提供的工具和资源
3. **查询处理**: 用户输入自然语言查询
4. **AI分析**: OpenAI模型分析查询并决定使用的工具
5. **工具执行**: 通过MCP协议执行相应的工具
6. **结果处理**: 处理工具执行结果并返回给用户

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API密钥 | `sk-...` |
| `HTTP_PROXY` | ❌ | HTTP代理设置 | `http://127.0.0.1:7890` |
| `HTTPS_PROXY` | ❌ | HTTPS代理设置 | `http://127.0.0.1:7890` |

### 模型配置

在 `mcp_client.py` 中可以修改使用的OpenAI模型：

```python
# 默认使用gpt-4，可以修改为其他模型
response = await self.openai_client.chat.completions.create(
    model="gpt-4",  # 修改这里
    # ... 其他参数
)
```

## 🧪 测试和验证

### 运行测试

使用测试脚本验证客户端功能：

```bash
python test_client.py path/to/your/server.py
```

测试包括：
- 服务器连接测试
- 工具列表获取测试
- 资源列表获取测试
- 基本查询处理测试

### 故障排除

常见问题及解决方案：

1. **连接失败**
   - 检查服务器路径是否正确
   - 确认服务器脚本可执行
   - 检查Python环境

2. **API密钥错误**
   - 确认OPENAI_API_KEY已正确设置
   - 检查API密钥是否有效
   - 确认账户有足够余额

3. **依赖安装失败**
   - 升级pip: `pip install --upgrade pip`
   - 使用虚拟环境
   - 检查Python版本兼容性

## 🔧 开发指南

### 项目结构

```
optimade-mcp-client/
├── mcp_client.py          # 主客户端程序
├── start_client.py        # 启动脚本
├── test_client.py         # 测试脚本
├── requirements.txt       # Python依赖
├── config.env.example     # 环境变量模板
└── README.md             # 说明文档
```

### 扩展功能

要添加新功能，可以：

1. **添加新的MCP工具支持**
   - 在`_convert_mcp_tools_to_openai()`中添加工具转换逻辑
   - 在`_execute_mcp_tool()`中添加工具执行逻辑

2. **自定义系统提示词**
   - 修改`_get_system_prompt()`方法
   - 添加领域特定的指导

3. **增强用户界面**
   - 修改`chat_loop()`方法
   - 添加新的命令和功能

### 代码规范

- 使用类型提示（Type Hints）
- 添加详细的中文注释
- 遵循PEP 8代码风格
- 使用异步编程模式

## 📚 相关资源

- [MCP协议官方文档](https://modelcontextprotocol.io/)
- [OPTIMADE标准](https://www.optimade.org/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [Python异步编程指南](https://docs.python.org/3/library/asyncio.html)

## 🤝 贡献指南

欢迎贡献代码和提出建议！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- MCP协议开发团队
- OPTIMADE标准制定者
- OpenAI提供的AI服务
- 所有贡献者和用户

---

**如有问题或建议，请提交Issue或联系开发者。**

**享受使用OPTIMADE MCP Client探索材料科学数据的乐趣！** 🎉 