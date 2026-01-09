# Windows Docker 部署指南

适用于 Windows 10/11，使用 Docker Desktop + WSL2。默认使用 PowerShell 示例命令。

## 📋 前置要求

- **Windows 10/11**，已启用 **WSL2**（推荐）
- 安装 **Docker Desktop**，并在 Settings 中开启：
  - Use the WSL 2 based engine
- 确认 `docker` 与 `docker-compose`（或 `docker compose`）可用：
  ```powershell
  docker --version
  docker-compose --version
  ```

## 🚀 快速部署

### 1. 克隆或解压项目

```powershell
cd C:\path\to\gdb_mcp
```

### 2. 创建环境变量文件

创建 `.env` 文件：

```powershell
Set-Content .env @"
POSTGRES_DB=gis_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432
GATEWAY_SSE_PORT=8000
GATEWAY_WS_PORT=8001
GATEWAY_LOG_LEVEL=info
"@
```

**重要**：务必修改 `POSTGRES_PASSWORD` 为强密码。

### 3. 启动服务

#### 基础版（不使用 Supergateway）

```powershell
docker-compose up -d
```

#### 完整版（使用 Supergateway，支持远程访问）

```powershell
docker-compose --profile gateway up -d
```

#### 使用独立脚本启动 Supergateway（推荐）

```powershell
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
.\scripts\start-supergateway.bat
```

### 4. 查看服务状态

```powershell
docker-compose ps
docker-compose logs --tail 100
```

### 5. 停止服务

```powershell
# 停止服务
docker-compose down

# 停止并清空数据卷
docker-compose down -v
```

## 📝 数据导入（可选）

将 GDB 数据放在项目根目录，运行：

```powershell
docker-compose --profile importer run --rm data-importer python main.py --reset-and-import --gdb-dir /app/data
```

## 🔧 配置说明

### 端口说明

- **5432**: PostgreSQL 数据库（可通过 `POSTGRES_PORT` 修改）
- **8000**: Supergateway SSE 服务（可通过 `GATEWAY_SSE_PORT` 修改）
- **8001**: Supergateway WebSocket 服务（可通过 `GATEWAY_WS_PORT` 修改）

### 路径提示

- 如果在 WSL2 里使用路径，建议将代码放在 WSL2 分发版的 Linux 路径（如 `/home/<user>/gdb_mcp`），避免跨盘性能问题
- Docker Desktop 会自动挂载 WSL2 路径

## ✅ 验证服务

```powershell
# 检查 PostgreSQL
docker-compose exec postgres psql -U postgres -d gis_data -c "SELECT PostGIS_Version();"

# 检查 Supergateway（启用 gateway profile 时）
# Supergateway 默认不提供 /health 端点，使用 /sse 验证（会保持长连接）
curl.exe -i http://localhost:8000/sse --max-time 2
```

## 🐛 常见问题

### Supergateway 不断重启，提示 "docker: not found"

**症状：**
```
[supergateway] Child exited: code=127, signal=null
[supergateway] Child stderr: /bin/sh: docker: not found
```

**解决方案（推荐）：**

使用独立脚本启动 Supergateway：

```powershell
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
.\scripts\start-supergateway.bat
```

### 其他常见问题

- **权限或路径问题**：确保项目目录已在 Docker Desktop 的文件共享列表中（Settings -> Resources -> File Sharing）
- **WSL2 未启用**：在 PowerShell（管理员）执行 `wsl --install` 并重启
- **端口冲突**：修改 `.env` 端口后重新启动

## 📚 相关文档

- [Docker 快速开始指南](../README_DOCKER.md)
- [Docker 部署后的 MCP 配置指南](MCP_DOCKER_CONFIG.md)
- [MCP 服务完整指南](MCP_GUIDE.md)


