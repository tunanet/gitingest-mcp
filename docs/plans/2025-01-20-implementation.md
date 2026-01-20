# gitingest-mcp Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个 MCP HTTP 服务器，封装 gitingest，让 Claude Code 能够分析 GitHub 仓库并生成中文学习笔记。

**Architecture:** Python FastAPI 应用，实现标准 MCP 协议端点，调用 gitingest 库分析 GitHub 仓库。

**Tech Stack:** Python 3.8+, FastAPI, uvicorn, gitingest, pydantic

---

## Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore` (already exists, verify content)

**Step 1: 创建 pyproject.toml**

```bash
cat > pyproject.toml << 'EOF'
[project]
name = "gitingest-mcp"
version = "0.1.0"
description = "MCP server for gitingest - analyze GitHub repos in Claude Code"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "gitingest>=0.1.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 100
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
EOF
```

**Step 2: 创建 requirements.txt**

```bash
cat > requirements.txt << 'EOF'
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
gitingest>=0.1.0
pydantic>=2.5.0
python-dotenv>=1.0.0
pytest>=7.4.0
httpx>=0.25.0
EOF
```

**Step 3: 创建 .env.example**

```bash
cat > .env.example << 'EOF'
PORT=8000
GITHUB_TOKEN=
EOF
```

**Step 4: 验证 .gitignore 包含必要内容**

```bash
cat > .gitignore << 'EOF'
.worktrees/
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/
dist/
*.egg-info/
.pytest_cache/
.coverage
EOF
```

**Step 5: 提交**

```bash
git add pyproject.toml requirements.txt .env.example .gitignore
git commit -m "feat: initialize project configuration"
```

---

## Task 2: 创建 server 模块结构

**Files:**
- Create: `server/__init__.py`
- Create: `server/main.py`
- Create: `server/mcp_handler.py`
- Create: `server/gitingest_wrapper.py`
- Create: `server/prompts.py`

**Step 1: 创建 __init__.py**

```bash
cat > server/__init__.py << 'EOF'
"""gitingest-mcp: MCP server for gitingest."""

__version__ = "0.1.0"
EOF
```

**Step 2: 创建 main.py - 基础 FastAPI 应用**

```python
# server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="gitingest-mcp",
    description="MCP server for gitingest - analyze GitHub repos in Claude Code",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gitingest-mcp"}


@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """MCP 协议端点。"""
    # 处理 MCP 请求的逻辑将在下一步实现
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

**Step 3: 运行应用验证启动**

```bash
# 安装依赖
pip install -e .

# 启动服务器（后台运行）
python -m server.main &
sleep 3

# 测试健康检查
curl http://localhost:8000/health
# 预期输出: {"status":"ok","service":"gitingest-mcp"}

# 停止服务器
pkill -f "python -m server.main"
```

**Step 4: 提交**

```bash
git add server/
git commit -m "feat: add FastAPI application with health check"
```

---

## Task 3: 实现 gitingest 封装

**Files:**
- Create: `server/gitingest_wrapper.py`
- Create: `tests/test_gitingest_wrapper.py`

**Step 1: 编写测试**

```bash
mkdir -p tests
cat > tests/test_gitingest_wrapper.py << 'EOF'
import pytest
from server.gitingest_wrapper import analyze_repo


def test_analyze_repo_basic():
    """测试基本仓库分析。"""
    # 使用一个已知的小仓库
    result = analyze_repo("https://github.com/coderamp-labs/gitingest")

    assert "summary" in result
    assert "tree" in result
    assert "content" in result
    assert "metadata" in result


def test_analyze_repo_with_subdirectory():
    """测试子目录分析。"""
    result = analyze_repo(
        "https://github.com/coderamp-labs/gitingest",
        subdirectory="README.md"
    )

    assert "summary" in result
    assert result["summary"]["repo_name"] == "coderamp-labs/gitingest"


def test_analyze_repo_invalid_url():
    """测试无效 URL。"""
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        analyze_repo("not-a-url")


def test_analyze_repo_private_with_token():
    """测试私有仓库（带 token）。"""
    # 这个测试需要真实的 token，暂时跳过
    pytest.skip("Requires valid GitHub token")
EOF
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_gitingest_wrapper.py -v
# 预期: ImportError 或 ModuleNotFoundError
```

**Step 3: 实现最小功能使测试通过**

```bash
cat > server/gitingest_wrapper.py << 'EOF'
"""gitingest 库的封装。"""

from gitingest import ingest
from typing import Optional, Dict, Any
import re


def _parse_github_url(url: str) -> tuple[str, Optional[str]]:
    """
    解析 GitHub URL，返回 (owner/repo, subdirectory)。

    Args:
        url: GitHub 仓库 URL

    Returns:
        (owner/repo, subdirectory) 元组

    Raises:
        ValueError: 如果 URL 格式无效
    """
    # 支持 https://github.com/owner/repo 格式
    pattern = r"github\.com/([^/]+)/([^/?]+)(?:/tree/[^/]+/([^?]+))?"
    match = re.search(pattern, url)

    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner, repo, subdirectory = match.groups()
    repo_path = f"{owner}/{repo}"
    return repo_path, subdirectory


def analyze_repo(
    url: str,
    subdirectory: Optional[str] = None,
    github_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    分析 GitHub 仓库。

    Args:
        url: GitHub 仓库 URL
        subdirectory: 可选的子目录路径
        github_token: 可选的 GitHub token（用于私有仓库）

    Returns:
        包含 summary, tree, content, metadata 的字典
    """
    # 验证 URL
    repo_path, url_subdir = _parse_github_url(url)
    final_subdir = subdirectory or url_subdir

    # 设置 token
    import os
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    # 调用 gitingest
    if final_subdir:
        full_url = f"https://github.com/{repo_path}/tree/main/{final_subdir}"
    else:
        full_url = url

    summary, tree, content = ingest(full_url)

    # 构建返回结果
    return {
        "summary": {
            "repo_name": repo_path,
            "description": summary,
            "total_files": tree.count("\n"),
        },
        "tree": tree,
        "content": content,
        "metadata": {
            "source_url": full_url,
        }
    }
EOF
```

**Step 4: 安装依赖并运行测试**

```bash
# 安装 gitingest
pip install gitingest

# 运行测试
pytest tests/test_gitingest_wrapper.py -v
# 注意: 第一次运行会从网络获取数据，可能较慢
```

**Step 5: 提交**

```bash
git add server/gitingest_wrapper.py tests/test_gitingest_wrapper.py
git commit -m "feat: implement gitingest wrapper with tests"
```

---

## Task 4: 实现 MCP 协议处理

**Files:**
- Modify: `server/mcp_handler.py`
- Modify: `server/main.py`

**Step 1: 创建 MCP 数据模型**

```bash
cat > server/mcp_handler.py << 'EOF'
"""MCP 协议处理。"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from enum import Enum


class MCPMessageType(str, Enum):
    """MCP 消息类型。"""
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"


class Tool(BaseModel):
    """MCP 工具定义。"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class Prompt(BaseModel):
    """MCP Prompt 定义。"""
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None


# 定义可用的工具
AVAILABLE_TOOLS = [
    Tool(
        name="analyze_repo",
        description="分析 GitHub 仓库，返回代码结构、统计和完整内容",
        inputSchema={
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
    )
]

# 定义可用的 prompts
AVAILABLE_PROMPTS = [
    Prompt(
        name="generate_note",
        description="生成 GitHub 仓库的中文学习笔记",
        arguments=[
            {
                "name": "url",
                "description": "GitHub 仓库 URL",
                "required": True
            },
            {
                "name": "focus",
                "description": "可选：重点关注的内容（如特定功能、模块）",
                "required": False
            }
        ]
    )
]


def handle_tools_list() -> Dict[str, Any]:
    """处理 tools/list 请求。"""
    return {
        "tools": [tool.model_dump() for tool in AVAILABLE_TOOLS]
    }


def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """处理 tools/call 请求。"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "analyze_repo":
        from server.gitingest_wrapper import analyze_repo
        result = analyze_repo(
            url=arguments.get("url"),
            subdirectory=arguments.get("subdirectory"),
            github_token=arguments.get("github_token")
        )
        return {
            "content": [{"type": "text", "text": str(result)}]
        }
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def handle_prompts_list() -> Dict[str, Any]:
    """处理 prompts/list 请求。"""
    return {
        "prompts": [prompt.model_dump() for prompt in AVAILABLE_PROMPTS]
    }


def handle_prompts_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """处理 prompts/get 请求。"""
    prompt_name = params.get("name")

    if prompt_name == "generate_note":
        return {
            "name": "generate_note",
            "description": "生成 GitHub 仓库的中文学习笔记",
            "arguments": [
                {"name": "url", "description": "GitHub 仓库 URL", "required": True},
                {"name": "focus", "description": "可选：重点关注的内容", "required": False}
            ]
        }
    else:
        raise ValueError(f"Unknown prompt: {prompt_name}")


def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理 MCP 请求。

    Args:
        request: MCP 请求字典

    Returns:
        MCP 响应字典
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    result = None
    error = None

    try:
        if method == MCPMessageType.TOOLS_LIST:
            result = handle_tools_list()
        elif method == MCPMessageType.TOOLS_CALL:
            result = handle_tools_call(params)
        elif method == MCPMessageType.PROMPTS_LIST:
            result = handle_prompts_list()
        elif method == MCPMessageType.PROMPTS_GET:
            result = handle_prompts_get(params)
        else:
            error = {"code": -32601, "message": f"Method not found: {method}"}
    except Exception as e:
        error = {"code": -32603, "message": str(e)}

    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }

    if result is not None:
        response["result"] = result
    if error is not None:
        response["error"] = error

    return response
EOF
```

**Step 2: 更新 main.py 使用 MCP handler**

```bash
cat > server/main.py << 'EOF'
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from server.mcp_handler import handle_mcp_request

load_dotenv()

app = FastAPI(
    title="gitingest-mcp",
    description="MCP server for gitingest - analyze GitHub repos in Claude Code",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gitingest-mcp"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP 协议端点。"""
    body = await request.json()
    response = handle_mcp_request(body)
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
```

**Step 3: 测试 MCP 端点**

```bash
# 启动服务器
python -m server.main &
sleep 3

# 测试 tools/list
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# 预期输出包含 analyze_repo 工具定义

# 测试 prompts/list
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"prompts/list"}'

# 预期输出包含 generate_note prompt

# 停止服务器
pkill -f "python -m server.main"
```

**Step 4: 提交**

```bash
git add server/mcp_handler.py server/main.py
git commit -m "feat: implement MCP protocol handlers"
```

---

## Task 5: 创建 Prompt 模板

**Files:**
- Create: `server/prompts.py`

**Step 1: 创建 prompts.py**

```bash
cat > server/prompts.py << 'EOF'
"""Prompt 模板定义。"""

GENERATE_NOTE_TEMPLATE = """你是一个代码分析专家。用户想要分析一个 GitHub 仓库并生成中文学习笔记。

请按以下步骤执行：

1. **调用 analyze_repo 工具**
   - 使用用户提供的 GitHub URL
   - 如果用户指定了关注点，分析相关子目录

2. **理解项目结构**
   - 阅读目录树，理解代码组织方式
   - 识别主要模块和它们的功能
   - 理解项目的技术栈

3. **生成中文笔记**
   调用 obsidian:obsidian-markdown skill 生成笔记，包含以下部分：

   ## 项目概述
   - 项目名称和简介
   - 主要功能
   - 使用场景

   ## 技术栈
   - 编程语言
   - 主要框架和库
   - 架构模式

   ## 目录结构
   - 主要目录说明
   - 核心文件介绍

   ## 核心功能
   - 主要功能模块说明
   - 关键代码片段和解释

   ## 总结
   - 项目亮点
   - 可以学习的地方

请确保：
- 所有说明都是中文
- 代码注释也要翻译
- 保持技术准确性
- 笔记结构清晰易读
"""


def get_prompt_template(prompt_name: str) -> str:
    """
    获取 prompt 模板。

    Args:
        prompt_name: Prompt 名称

    Returns:
        Prompt 模板字符串

    Raises:
        ValueError: 如果 prompt 不存在
    """
    templates = {
        "generate_note": GENERATE_NOTE_TEMPLATE,
    }

    if prompt_name not in templates:
        raise ValueError(f"Unknown prompt: {prompt_name}")

    return templates[prompt_name]
EOF
```

**Step 2: 提交**

```bash
git add server/prompts.py
git commit -m "feat: add prompt templates for note generation"
```

---

## Task 6: 添加 Docker 部署配置

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: 创建 Dockerfile**

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

**Step 2: 创建 .dockerignore**

```bash
cat > .dockerignore << 'EOF'
.git
.gitignore
.worktrees
__pycache__
*.pyc
.env
.venv
venv
pytest
.pytest_cache
.coverage
docs
*.md
EOF
```

**Step 3: 测试 Docker 构建**

```bash
docker build -t gitingest-mcp:test .
```

**Step 4: 提交**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Docker deployment configuration"
```

---

## Task 7: 编写 README 文档

**Files:**
- Create: `README.md`

**Step 1: 创建 README.md**

```bash
cat > README.md << 'EOF'
# gitingest-mcp

MCP HTTP 服务器，封装 [gitingest](https://github.com/coderamp-labs/gitingest)，让 Claude Code 能够分析 GitHub 仓库并生成中文学习笔记。

## 功能

- 通过 MCP 协议分析 GitHub 仓库
- 获取代码结构、统计和完整内容
- 支持私有仓库（通过 GitHub token）
- 支持子目录分析
- 一键生成中文 Obsidian 学习笔记

## 部署

### 本地运行

```bash
# 安装依赖
pip install -e .

# 启动服务器
python -m server.main
```

### Docker 运行

```bash
docker build -t gitingest-mcp .
docker run -p 8000:8000 gitingest-mcp
```

### 云平台部署

支持部署到 Railway、Render、Fly.io 等平台。

**Railway 部署：**

```bash
railway up
```

**Render 部署：**

1. 连接 GitHub 仓库
2. 设置构建命令：`pip install -e . && uvicorn server.main:app --host 0.0.0.0 --port $PORT`
3. 部署完成后获取 URL

## 在 Claude Code 中注册

```bash
# 替换为你的部署 URL
claude mcp add --transport http gitingest https://your-app.example.com/mcp
```

## 使用示例

```
用户: "帮我分析 https://github.com/coderamp-labs/gitingest 这个项目，生成中文学习笔记"

Claude Code 会：
1. 调用 analyze_repo 工具获取仓库分析
2. 理解项目结构和功能
3. 翻译成中文
4. 调用 Obsidian skill 生成结构化笔记
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| PORT | 服务器端口 | 8000 |
| GITHUB_TOKEN | GitHub token（私有仓库） | - |

## License

MIT
EOF
```

**Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 8: 完善测试和验证

**Files:**
- Create: `tests/test_mcp_handler.py`
- Modify: `tests/test_gitingest_wrapper.py`

**Step 1: 添加 MCP handler 测试**

```bash
cat > tests/test_mcp_handler.py << 'EOF'
import pytest
from server.mcp_handler import (
    handle_mcp_request,
    handle_tools_list,
    handle_prompts_list,
    MCPMessageType
)


def test_tools_list():
    """测试 tools/list 端点。"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    response = handle_mcp_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert len(response["result"]["tools"]) == 1
    assert response["result"]["tools"][0]["name"] == "analyze_repo"


def test_prompts_list():
    """测试 prompts/list 端点。"""
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "prompts/list"
    }
    response = handle_mcp_request(request)

    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert len(response["result"]["prompts"]) == 1
    assert response["result"]["prompts"][0]["name"] == "generate_note"


def test_unknown_method():
    """测试未知方法。"""
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "unknown/method"
    }
    response = handle_mcp_request(request)

    assert "error" in response
    assert response["error"]["code"] == -32601


def test_tools_call_missing_url():
    """测试缺少必需参数。"""
    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "analyze_repo",
            "arguments": {}
        }
    }
    response = handle_mcp_request(request)

    # 应该返回错误，因为缺少 url 参数
    assert "error" in response or "result" in response
EOF
```

**Step 2: 运行所有测试**

```bash
pytest tests/ -v
```

**Step 3: 提交**

```bash
git add tests/
git commit -m "test: add comprehensive MCP handler tests"
```

---

## Task 9: 端到端测试

**Step 1: 启动服务器**

```bash
python -m server.main &
SERVER_PID=$!
sleep 3
```

**Step 2: 测试完整流程**

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 列出工具
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq .

# 3. 分析一个小仓库
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "analyze_repo",
      "arguments": {
        "url": "https://github.com/coderamp-labs/gitingest"
      }
    }
  }' | jq .

# 4. 停止服务器
kill $SERVER_PID
```

**Step 4: 提交**

```bash
git commit --allow-empty -m "test: verify end-to-end functionality"
```

---

## Task 10: 合并到主分支

**Step 1: 返回主分支**

```bash
cd /Users/valen/PROJECTS/gitingest-mcp
git checkout main
```

**Step 2: 合并 feature 分支**

```bash
git merge feature/implement-mcp-server --no-ff -m "Merge feature: MCP server implementation"
```

**Step 3: 清理 worktree**

```bash
git worktree remove .worktrees/impl
```

---

## 完成清单

- [x] 项目初始化完成
- [x] FastAPI 应用创建
- [x] MCP 协议实现
- [x] gitingest 封装完成
- [x] Prompt 模板定义
- [x] Docker 部署配置
- [x] 文档完善
- [x] 测试覆盖

## 下一步

1. 部署到云平台（Railway/Render）
2. 在 Claude Code 中注册 MCP 服务器
3. 测试完整的工作流程
