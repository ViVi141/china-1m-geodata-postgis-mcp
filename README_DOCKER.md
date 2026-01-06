# Docker 快速开始指南

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
- **mcp-server**: MCP 服务器服务（stdio 模式，自动连接数据库）
- **supergateway**: MCP 网关服务（可选，将 stdio 转换为 SSE/WebSocket，使用 `--profile gateway` 启动）
- **data-importer**: 数据导入服务（可选，使用 `--profile importer` 启动）

## 🌐 Supergateway 使用

Supergateway 可以将 stdio 模式的 MCP 服务器转换为 HTTP/SSE/WebSocket 服务，支持远程访问。

### 启动 Supergateway

#### 方式1：使用 Docker Compose（需要先构建自定义镜像）

```bash
# 先构建包含 Docker CLI 的自定义镜像
docker-compose build supergateway

# 启动所有服务（包括Supergateway）
docker-compose --profile gateway up -d
```

#### 方式2：使用独立脚本（推荐，避免 Docker CLI 问题）⭐⭐

**Windows:**
```powershell
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
.\scripts\start-supergateway.bat
```

**Linux:**
```bash
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
./scripts/start-supergateway.sh
```

### 访问端点

- **SSE**: `http://localhost:8000/sse`
- **WebSocket**: `ws://localhost:8001/ws`
- **健康检查**: `http://localhost:8000/health`

### ⚠️ 故障排除

如果遇到 "docker: not found" 错误，请查看 [Supergateway 故障排除指南](docs/SUPERGATEWAY_TROUBLESHOOTING.md)

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

- **基础使用**: 查看 [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md)
- **Linux 完整部署（含 Supergateway）**: 查看 [docs/DOCKER_LINUX_DEPLOY.md](docs/DOCKER_LINUX_DEPLOY.md)
- **Windows Docker 部署（含 Supergateway）**: 查看 [docs/DOCKER_WINDOWS_DEPLOY.md](docs/DOCKER_WINDOWS_DEPLOY.md)

