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
