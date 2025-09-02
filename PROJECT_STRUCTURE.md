# OPTIMADE MCP Client 项目结构

## 📁 目录结构

```
optimade-mcp-client/
├── 📄 mcp_client.py              # 主客户端程序
├── 📄 start_client.py            # 启动脚本
├── 📄 test_client.py             # 测试脚本
├── 📄 requirements.txt           # Python依赖包列表
├── 📄 config.env.example         # 环境变量配置模板
├── 📄 README.md                  # 主要说明文档
├── 📄 PROJECT_STRUCTURE.md       # 项目结构说明（本文件）
└── 📁 examples/                  # 示例代码目录
    └── 📄 example_queries.py     # 查询示例脚本
```

## 📋 文件详细说明

### 🔧 核心程序文件

#### `mcp_client.py` - 主客户端程序
- **作用**: 核心MCP客户端实现
- **主要功能**:
  - OPTIMADE MCP Server连接管理
  - OpenAI API集成
  - 自然语言查询处理
  - MCP工具调用
  - 交互式聊天界面
- **关键类**: `OptimadeMCPClient`
- **依赖**: mcp[cli], openai, python-dotenv

#### `start_client.py` - 启动脚本
- **作用**: 简化的客户端启动入口
- **主要功能**:
  - 自动配置服务器路径
  - 环境变量检查
  - 错误处理和用户指导
- **使用方式**: `python start_client.py`
- **配置**: 修改文件中的 `SERVER_PATH` 变量

#### `test_client.py` - 测试脚本
- **作用**: 客户端功能测试和验证
- **测试内容**:
  - 服务器连接测试
  - 工具列表获取测试
  - 资源列表获取测试
  - 基本查询处理测试
- **使用方式**: `python test_client.py <server_path>`

### 📦 配置文件

#### `requirements.txt` - Python依赖
- **作用**: 列出所有必需的Python包
- **主要依赖**:
  - `mcp[cli]`: MCP协议支持
  - `openai`: OpenAI API客户端
  - `python-dotenv`: 环境变量管理
- **安装方式**: `pip install -r requirements.txt`

#### `config.env.example` - 环境变量模板
- **作用**: 环境变量配置示例
- **必需配置**:
  - `OPENAI_API_KEY`: OpenAI API密钥
- **可选配置**:
  - `HTTP_PROXY`, `HTTPS_PROXY`: 代理设置
  - `LOG_LEVEL`: 日志级别
- **使用方式**: 复制为 `.env` 并填入实际值

### 📚 文档文件

#### `README.md` - 主要说明文档
- **作用**: 项目的主要说明和使用指南
- **内容**:
  - 项目介绍和特性
  - 安装和使用方法
  - 配置说明
  - 故障排除
  - 开发指南

#### `PROJECT_STRUCTURE.md` - 项目结构说明
- **作用**: 详细说明项目文件结构和作用
- **内容**: 本文件内容

### 🎯 示例文件

#### `examples/example_queries.py` - 查询示例
- **作用**: 展示各种查询类型的使用方法
- **示例类型**:
  - 元素查询
  - 属性范围查询
  - 过滤器语法验证
  - 材料类型查询
- **使用方式**: `python examples/example_queries.py`

## 🔄 工作流程

### 1. 启动流程
```
用户运行 start_client.py
    ↓
检查环境变量 (.env)
    ↓
验证服务器路径
    ↓
导入并运行 mcp_client.main()
    ↓
建立MCP连接
    ↓
启动聊天循环
```

### 2. 查询处理流程
```
用户输入自然语言查询
    ↓
OpenAI模型分析查询
    ↓
决定使用的MCP工具
    ↓
通过MCP协议调用工具
    ↓
处理工具执行结果
    ↓
返回用户友好的响应
```

## 🛠️ 开发指南

### 添加新功能

1. **新MCP工具支持**
   - 在 `_convert_mcp_tools_to_openai()` 中添加工具转换
   - 在 `_execute_mcp_tool()` 中添加执行逻辑

2. **自定义系统提示词**
   - 修改 `_get_system_prompt()` 方法
   - 添加领域特定的指导

3. **增强用户界面**
   - 修改 `chat_loop()` 方法
   - 添加新的命令和功能

### 代码规范

- 使用类型提示（Type Hints）
- 添加详细的中文注释
- 遵循PEP 8代码风格
- 使用异步编程模式
- 适当的错误处理和日志记录

## 🔍 调试和测试

### 运行测试
```bash
# 基本功能测试
python test_client.py <server_path>

# 示例查询测试
python examples/example_queries.py
```

### 日志查看
- 客户端运行时会显示详细的日志信息
- 包括连接状态、工具调用、错误信息等

### 常见问题排查
1. 检查环境变量配置
2. 验证服务器路径
3. 确认依赖包安装
4. 检查网络连接和代理设置

## 📈 扩展建议

### 短期改进
- 添加配置文件支持
- 增强错误处理
- 添加更多示例查询

### 长期规划
- Web界面开发
- 批量查询支持
- 结果导出功能
- 多模型支持
- 插件系统

---

**这个项目结构设计遵循了模块化和可维护性的原则，每个文件都有明确的职责，便于理解和扩展。**
