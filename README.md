# gitingest-mcp

MCP HTTP 服务器，封装 [gitingest](https://github.com/coderamp-labs/gitingest)，让 Claude Code 能够分析 GitHub 仓库并生成中文学习笔记。

## 功能

- 通过 MCP 协议分析 GitHub 仓库
- 获取代码结构、统计和完整内容
- 支持私有仓库（通过 GitHub token）
- 支持子目录分析
- 一键生成中文 Obsidian 学习笔记

## 部署

### 云服务器部署

#### Docker Compose 部署（推荐）

项目已包含 `docker-compose.yml` 配置文件，这是最简单可靠的部署方式。

```bash
# 1. 克隆项目
git clone https://github.com/tunanet/gitingest-mcp.git
cd gitingest-mcp

# 2. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，设置 GITHUB_TOKEN 等变量

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

#### Docker 部署

如果不使用 Docker Compose，也可以直接使用 Docker 命令：

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

#### 其他部署方式

**Systemd 守护进程：**

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

**PaaS 平台：**

Railway:
```bash
npm install -g railway
railway login
railway up
```

Render:
1. 在 Render Dashboard 创建新的 Web Service
2. 连接 GitHub 仓库 `tunanet/gitingest-mcp`
3. 设置构建命令: `pip install -e . && uvicorn server.main:app --host 0.0.0.0 --port $PORT`

### 本地开发

```bash
# 安装依赖
pip install -e .

# 启动服务器
python -m server.main
```

#### 反向代理配置（推荐生产环境）

服务默认绑定 `127.0.0.1:8000`，通过 Nginx 反向代理暴露公网。

**HTTP 配置：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**HTTPS 配置（使用 Let's Encrypt）：**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
