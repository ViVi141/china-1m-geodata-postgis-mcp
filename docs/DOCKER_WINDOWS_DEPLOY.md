# Windows Docker 部署指南（含 Supergateway）

适用于 Windows 10/11，使用 Docker Desktop + WSL2。默认使用 PowerShell 示例命令（无 `&&`）。

## 前置要求

- Windows 10/11，已启用 **WSL2**（推荐）。
- 安装 **Docker Desktop**，并在 Settings 中开启：
  - Use the WSL 2 based engine
  - （可选）Expose daemon on tcp://localhost:2375 without TLS 如果需要远程调试。
- 确认 `docker` 与 `docker-compose`（或 `docker compose`）可用：
  ```powershell
  docker --version
  docker-compose --version
  ```

## 快速部署

1) 克隆或解压项目，进入目录：
```powershell
cd C:\path\to\gdb_mcp
```

2) 创建 `.env`（也可复制 `.env.example` 后修改）：
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
务必修改 `POSTGRES_PASSWORD`。

3) 启动（基础版，不含 Supergateway）：
```powershell
docker-compose up -d
```

4) 启动（完整版，含 Supergateway，支持远程访问）：
```powershell
docker-compose --profile gateway up -d
```

5) 查看状态与日志：
```powershell
docker-compose ps
docker-compose logs --tail 100
docker-compose logs --tail 100 supergateway
```

6) 停止：
```powershell
docker-compose down
```
如需清空数据卷：
```powershell
docker-compose down -v
```

## 数据导入（可选）

将 GDB 数据放在项目根目录（或自行挂载目录），运行：

```powershell
docker-compose --profile importer run --rm data-importer `
  python main.py --reset-and-import --gdb-dir /app/data
```

**命令解释：**

- `docker-compose` - Docker Compose 命令
- `--profile importer` - 启用 `importer` 配置档（data-importer 服务默认不启动，需要此参数）
- `run` - 运行一次性任务（不常驻运行）
- `--rm` - 任务完成后自动删除容器
- `data-importer` - 服务名称（对应 docker-compose.yml 中的 data-importer 服务）
- `` ` `` - PowerShell 行继续符（反引号），用于将长命令分成多行
- `python main.py --reset-and-import --gdb-dir /app/data` - 在容器内执行的命令
  - `--reset-and-import` - 重置数据库并导入数据
  - `--gdb-dir /app/data` - 指定 GDB 文件目录（容器内的路径）

**等价的单行命令：**

```powershell
docker-compose --profile importer run --rm data-importer python main.py --reset-and-import --gdb-dir /app/data
```

## 端口与路径提示

- 如 5432/8000/8001 被占用，修改 `.env` 中对应端口后重新 `up -d`。
- 如果在 WSL2 里使用路径，建议将代码放在 WSL2 分发版的 Linux 路径（如 `/home/<user>/gdb_mcp`），避免跨盘性能问题；Docker Desktop 会自动挂载。
- Supergateway 依赖挂载 Docker socket（`/var/run/docker.sock`），在 Docker Desktop 默认开启的情况下可正常工作。

## 快速验证

```powershell
# 检查 PostgreSQL
docker-compose exec postgres psql -U postgres -d gis_data -c "SELECT PostGIS_Version();"

# 检查 Supergateway（启用 gateway profile 时）
Invoke-WebRequest -Uri http://localhost:8000/health
```

## 常见问题

### Supergateway 不断重启，提示 "docker: not found"

**症状：**
```
[supergateway] Child exited: code=127, signal=null
[supergateway] Child stderr: /bin/sh: docker: not found
```

**解决方案（推荐）：**

使用独立脚本启动 Supergateway，避免容器内 Docker CLI 问题：

```powershell
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动 Supergateway
.\scripts\start-supergateway.bat
```

**或者构建自定义镜像：**

```powershell
# 构建包含 Docker CLI 的自定义镜像
docker-compose build supergateway

# 启动服务
docker-compose --profile gateway up -d
```

**详细说明：** 查看 [Supergateway 故障排除指南](SUPERGATEWAY_TROUBLESHOOTING.md)

### 其他常见问题

- **权限或路径问题**：确保项目目录已在 Docker Desktop 的文件共享列表中（Settings -> Resources -> File Sharing）。
- **WSL2 未启用**：在 PowerShell（管理员）执行 `wsl --install` 并重启。
- **端口冲突**：修改 `.env` 端口后重新启动。


