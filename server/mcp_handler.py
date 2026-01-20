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
                },
                "default_branch": {
                    "type": "string",
                    "description": "可选：默认分支名（默认为 main）"
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
            github_token=arguments.get("github_token"),
            default_branch=arguments.get("default_branch")
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
