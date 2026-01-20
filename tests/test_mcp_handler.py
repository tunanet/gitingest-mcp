import pytest
from unittest.mock import patch, MagicMock
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
    assert "error" in response
    assert response["error"]["code"] == -32603
    assert "none" in str(response["error"]["message"]).lower() or "type" in str(response["error"]["message"]).lower()


def test_prompts_get_valid():
    """测试 prompts/get 端点 - 有效的 prompt 名称。"""
    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "prompts/get",
        "params": {
            "name": "generate_note"
        }
    }
    response = handle_mcp_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 5
    assert "result" in response
    assert response["result"]["name"] == "generate_note"
    assert response["result"]["description"] == "生成 GitHub 仓库的中文学习笔记"
    assert len(response["result"]["arguments"]) == 2
    assert response["result"]["arguments"][0]["name"] == "url"
    assert response["result"]["arguments"][0]["required"] is True
    assert response["result"]["arguments"][1]["name"] == "focus"
    assert response["result"]["arguments"][1]["required"] is False


def test_prompts_get_unknown():
    """测试 prompts/get 端点 - 未知的 prompt 名称。"""
    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "prompts/get",
        "params": {
            "name": "unknown_prompt"
        }
    }
    response = handle_mcp_request(request)

    assert "error" in response
    assert response["error"]["code"] == -32603
    assert "Unknown prompt" in response["error"]["message"]


def test_tools_call_success():
    """测试 tools/call 端点 - 成功调用。"""
    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "analyze_repo",
            "arguments": {
                "url": "https://github.com/test/repo"
            }
        }
    }

    # Mock analyze_repo function - patch it where it's imported
    with patch('server.gitingest_wrapper.analyze_repo') as mock_analyze:
        mock_analyze.return_value = {"structure": "test", "content": "test content"}

        response = handle_mcp_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 7
    assert "result" in response
    assert "content" in response["result"]
    assert len(response["result"]["content"]) == 1
    assert response["result"]["content"][0]["type"] == "text"
    mock_analyze.assert_called_once_with(url="https://github.com/test/repo", subdirectory=None, github_token=None, default_branch=None)


def test_tools_call_unknown_tool():
    """测试 tools/call 端点 - 未知的工具名称。"""
    request = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "unknown_tool",
            "arguments": {}
        }
    }
    response = handle_mcp_request(request)

    assert "error" in response
    assert response["error"]["code"] == -32603
    assert "Unknown tool" in response["error"]["message"]
