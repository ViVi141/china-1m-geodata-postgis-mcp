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

#### 方式3：基础版 + 1Panel MCP服务（推荐用于1Panel用户）⭐⭐

使用1Panel的可视化MCP服务管理，基于Supergateway实现。

**步骤1：启动基础服务**

```bash
docker-compose up -d
```

**步骤2：在1Panel中配置MCP服务**

1. 登录1Panel管理界面
2. 进入 **MCP服务** 或 **应用商店** → **MCP服务**
3. 点击 **添加MCP服务** 或 **新建服务**
4. 按以下配置填写：

| 配置项 | 配置值 | 说明 |
|--------|--------|------|
| **类型** | `npx` | 使用npx类型 |
| **启动命令** | `docker exec -i geodata-mcp-server python /app/mcp_server.py` | 在MCP容器中执行Python脚本 |
| **端口** | `8000` | SSE服务端口（可根据需要修改） |
| **外部访问路径** | `http://192.168.1.1:8000` | 完整的基础URL（替换为您的服务器IP和端口）<br>示例：`http://192.168.1.1:8000` 或 `http://your-domain.com:8000` |
| **容器名称** | `geodata-mcp-server` | MCP服务器容器名称（必须与docker-compose.yml中一致） |
| **输出类型** | `sse` | 使用SSE（Server-Sent Events）输出 |
| **SSE路径** | `/sse` | SSE端点路径（默认为/sse） |

**配置说明**：
- **外部访问路径**：填写完整的访问URL，例如：
  - 内网访问：`http://192.168.1.1:8000`
  - 公网访问：`http://your-domain.com:8000`
  - 本地访问：`http://localhost:8000`
- 确保端口号与"端口"配置项一致

**重要提示**：
- 确保 `geodata-mcp-server` 容器已运行（通过 `docker-compose ps` 检查）
- 端口 `8000` 必须未被占用，且防火墙已开放该端口
- 如果需要同时使用WebSocket，可以在1Panel中配置第二个MCP服务，使用 `ws` 输出类型和端口 `8001`
- 1Panel的MCP服务会自动处理Docker容器的连接，无需手动配置Docker socket
- 如果使用公网访问，请确保服务器安全配置正确

**步骤3：验证服务**

在1Panel中查看MCP服务状态，或访问：
- SSE端点：`http://192.168.1.1:8000/sse`（替换为您配置的外部访问路径 + /sse）
- 健康检查：`http://192.168.1.1:8000/health`（替换为您配置的外部访问路径 + /health）

**优势**：
- ✅ 可视化配置，操作简单
- ✅ 1Panel自动管理服务生命周期
- ✅ 支持服务监控和日志查看
- ✅ 无需手动管理Supergateway容器

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

#### 方式1：使用 1Panel MCP服务（推荐用于1Panel用户）⭐⭐⭐

详见上面的 **方式3：基础版 + 1Panel MCP服务** 部分。

#### 方式2：使用 Docker Compose（需要先构建自定义镜像）

```bash
# 先构建包含 Docker CLI 的自定义镜像
docker-compose build supergateway

# 启动所有服务（包括Supergateway）
docker-compose --profile gateway up -d
```

#### 方式3：使用独立脚本（推荐，避免 Docker CLI 问题）⭐⭐

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

#### 方式对比

| 方式 | 适用场景 | 优势 | 缺点 |
|------|---------|------|------|
| **1Panel MCP服务** | 使用1Panel管理服务器 | ✅ 可视化配置<br>✅ 自动管理生命周期<br>✅ 内置监控和日志 | ❌ 需要1Panel环境 |
| **Docker Compose** | 熟悉Docker Compose | ✅ 一键部署<br>✅ 配置集中管理 | ❌ 需要构建镜像<br>❌ 可能遇到Docker CLI问题 |
| **独立脚本** | 灵活部署场景 | ✅ 简单直接<br>✅ 避免Docker CLI问题 | ❌ 需手动管理进程 |

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

