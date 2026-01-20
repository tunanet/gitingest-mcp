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

### 云服务器部署

#### 方案 1: Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/tunanet/gitingest-mcp.git
cd gitingest-mcp

# 2. 构建镜像
docker build -t gitingest-mcp .

# 3. 运行容器
docker run -d \
  --name gitingest-mcp \
  -p 8000:8000 \
  -e GITHUB_TOKEN=your_token_if_needed \
  --restart unless-stopped \
  gitingest-mcp
```

#### 方案 2: Docker Compose（适合管理）

创建 `docker-compose.yml`:

```yaml
version: '3.8'
services:
  gitingest-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    restart: unless-stopped
```

运行:
```bash
docker-compose up -d
```

#### 方案 3: Systemd 守护进程

```bash
# 1. 安装依赖
pip install -e .

# 2. 创建 systemd 服务
sudo nano /etc/systemd/system/gitingest-mcp.service
```

添加内容:
```ini
[Unit]
Description=Gitingest MCP Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/gitingest-mcp
Environment="PORT=8000"
ExecStart=/usr/bin/python -m server.main
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gitingest-mcp
sudo systemctl start gitingest-mcp
```

#### 方案 4: PaaS 平台（最简单）

**Railway:**
```bash
npm install -g railway
railway login
railway up
```

**Render:**
1. 在 Render Dashboard 创建新的 Web Service
2. 连接 GitHub 仓库 `tunanet/gitingest-mcp`
3. 设置构建命令: `pip install -e . && uvicorn server.main:app --host 0.0.0.0 --port $PORT`

**Fly.io:**
```bash
fly launch
fly deploy
```

#### 反向代理（可选）

如果使用域名，配置 Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

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
