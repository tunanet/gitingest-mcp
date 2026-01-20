# gitingest-mcp 设计文档

## 项目概述

创建一个 MCP (Model Context Protocol) HTTP 服务器，封装 [gitingest](https://github.com/coderamp-labs/gitingest) 项目，使其能够在 Claude Code 中注册使用。通过 MCP 获取 GitHub 仓库的分析结果，由 Claude Code 整理成中文后，调用 Obsidian skill 生成学习笔记。

**使用场景**: 个人学习开源项目代码，生成结构化的中文笔记。

## 整体架构

```
┌─────────────┐      ┌──────────────┐      ┌──────────┐      ┌──────────┐
│ Claude Code │ ───> │ MCP Server   │ ───> │ gitingest│ ───> │GitHub API│
└─────────────┘      │ (FastAPI)    │      └──────────┘      └──────────┘
                      └──────────────┘
                            │
                            ↓
                      返回分析结果
                            │
                            ↓
                     Claude 翻译成中文
                            │
                            ↓
                   调用 Obsidian skill
                            │
                            ↓
                      生成笔记
```

### 核心组件

1. **MCP HTTP 服务器** (基于 Python FastAPI)
   - 部署在云平台（Railway/Render/Fly.io）
   - 实现标准 MCP 协议端点
   - 作为 gitingest 的封装层

2. **工具定义**
   - `analyze_repo`: 分析 GitHub 仓库，返回结构化结果

3. **Prompt 定义**
   - `generate_note`: 完整的"分析→翻译→生成笔记"流程

## MCP 协议实现

### HTTP 端点

```
POST /mcp
Content-Type: application/json
```

实现标准 MCP 协议端点：
- `tools/list`: 列出可用工具
- `tools/call`: 调用 analyze_repo 工具
- `prompts/list`: 列出可用 prompts
- `prompts/get`: 获取 generate_note prompt

### analyze_repo 工具

**输入参数：**

```json
{
  "name": "analyze_repo",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "GitHub 仓库 URL，如 https://github.com/owner/repo"
      },
      "subdirectory": {
        "type": "string",
        "description": "可选：只分析指定子目录"
      },
      "github_token": {
        "type": "string",
        "description": "可选：用于私有仓库的 GitHub token"
      }
    },
    "required": ["url"]
  }
}
```

**返回结构：**

```json
{
  "summary": {
    "repo_name": "coderamp-labs/gitingest",
    "description": "项目的简要描述",
    "language_stats": {"Python": 85, "HTML": 10},
    "total_files": 123,
    "total_tokens": 45000
  },
  "tree": "目录树结构（可视化）",
  "content": "完整的代码内容文本（LLM 友好格式）",
  "metadata": {
    "ingested_at": "2025-01-20T12:00:00Z",
    "commit_hash": "abc123"
  }
}
```

### generate_note Prompt

引导 Claude 完成以下流程：
1. 调用 `analyze_repo` 获取仓库分析
2. 理解项目结构和核心功能
3. 翻译成中文
4. 调用 Obsidian skill 生成结构化笔记

## 项目结构

```
gitingest-mcp/
├── server/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── mcp_handler.py       # MCP 协议处理
│   ├── gitingest_wrapper.py # gitingest 封装
│   └── prompts.py           # Prompt 模板定义
├── docs/
│   └── plans/
│       └── 2025-01-20-gitingest-mcp-design.md
├── pyproject.toml           # 项目配置
├── requirements.txt         # 依赖
├── Dockerfile               # 云端部署
├── .env.example             # 环境变量示例
└── README.md                # 使用文档
```

### 核心依赖

- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `gitingest` - 核心分析功能
- `pydantic` - 数据验证

## 使用流程

### 1. 部署并注册

```bash
# 部署到 Railway/Render 后，获取 URL
export GITINGEST_MCP_URL="https://your-app.example.com/mcp"

# 在 Claude Code 中注册
claude mcp add --transport http gitingest $GITINGEST_MCP_URL
```

### 2. 使用示例

```
用户: "帮我分析一下 https://github.com/coderamp-labs/gitingest 这个项目，生成中文笔记"

Claude Code 执行：
1. 调用 gitingest.analyze_repo(url="...")
2. 获取分析结果（summary + tree + content）
3. 理解项目结构和功能
4. 翻译关键内容为中文
5. 调用 obsidian:obsidian-markdown skill
6. 生成结构化的 Obsidian 笔记
```

### 3. 生成的笔记结构

```markdown
# [项目名称]

## 项目概述
[翻译后的摘要]

## 技术栈
- Python
- FastAPI
- ...

## 目录结构
[翻译后的目录树]

## 核心功能
[翻译后的功能说明]
...
```

## 技术考虑点

### 超时处理
- gitingest 分析大型仓库可能需要较长时间
- 设置合理的超时时间（5 分钟）
- 返回部分结果 + 进度提示

### 错误处理
- 私有仓库认证失败
- 仓库不存在或无法访问
- 网络超时重试机制

### 安全考虑
- GitHub token 不应记录在日志中
- 请求频率限制防止滥用
- CORS 配置允许 Claude Code 访问

## 部署平台

支持以下云平台：
- Railway
- Render
- Fly.io
- Vercel（需配置服务器）

通过环境变量配置：
- `PORT`: 服务器端口（默认 8000）
- `GITHUB_TOKEN`: 可选的默认 GitHub token
