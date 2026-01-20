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
