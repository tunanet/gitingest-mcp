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
