# Docker 快速开始指南

适用于 **Windows** 和 **Linux** 系统。

## 🚀 快速启动

### 1. 创建环境变量文件

在项目根目录创建 `.env` 文件：

```bash
POSTGRES_DB=gis_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5432

# Supergateway 配置（可选）
GATEWAY_SSE_PORT=8000
GATEWAY_WS_PORT=8001
GATEWAY_LOG_LEVEL=info
```

### 2. 启动服务

#### 基础版（不使用 Supergateway）

```bash
docker-compose up -d
```

#### 完整版（使用 Supergateway，支持远程访问）

```bash
docker-compose --profile gateway up -d
```

#### 使用独立脚本启动 Supergateway（推荐）

**Linux:**
```bash
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
./scripts/start-supergateway.sh
```

**Windows:**
```powershell
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
.\scripts\start-supergateway.bat
```

### 3. 查看服务状态

```bash
docker-compose ps
```

### 4. 查看日志

```bash
docker-compose logs -f
```

## 📦 服务说明

- **postgres**: PostgreSQL/PostGIS 数据库服务
  - **重要**：端口说明
    - 宿主机访问端口：`${POSTGRES_PORT:-5432}`（从宿主机连接时使用，如 `localhost:5234`）
    - 容器内部端口：`5432`（**固定值**，容器间通信必须使用此端口）
    - 端口映射格式：`宿主机端口:容器内部端口`，例如 `5234:5432`
- **mcp-server**: MCP 服务器服务（stdio 模式，自动连接数据库）
  - 通过容器网络连接到 `postgres:5432`（使用容器内部端口）
- **supergateway**: MCP 网关服务（可选，将 stdio 转换为 SSE/WebSocket，使用 `--profile gateway` 启动）
- **data-importer**: 数据导入服务（可选，使用 `--profile importer` 启动）
  - 通过容器网络连接到 `postgres:5432`（使用容器内部端口）

## 🌐 Supergateway 使用

Supergateway 可以将 stdio 模式的 MCP 服务器转换为 HTTP/SSE/WebSocket 服务，支持远程访问。

### 访问端点

**默认端口**：
- **SSE**: `http://localhost:8000/sse`
- **WebSocket**: `ws://localhost:8001/ws`

**注意**：Supergateway 默认不提供 `/health` 端点，使用 `/sse` 验证服务可用性。

## 🔧 常用命令

```bash
# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 重建镜像
docker-compose build --no-cache

# 进入容器
docker-compose exec mcp-server bash
docker-compose exec postgres psql -U postgres -d gis_data

# 查看特定服务日志
docker-compose logs -f supergateway
```

## 📚 详细文档

- **Linux Docker 部署**: 查看 [docs/DOCKER_LINUX_DEPLOY.md](docs/DOCKER_LINUX_DEPLOY.md)
- **Windows Docker 部署**: 查看 [docs/DOCKER_WINDOWS_DEPLOY.md](docs/DOCKER_WINDOWS_DEPLOY.md)
- **Docker 部署后的 MCP 配置**: 查看 [docs/MCP_DOCKER_CONFIG.md](docs/MCP_DOCKER_CONFIG.md)
- **1Panel MCP 配置**: 查看 [docs/1PANEL_MCP_CONFIG.md](docs/1PANEL_MCP_CONFIG.md)

