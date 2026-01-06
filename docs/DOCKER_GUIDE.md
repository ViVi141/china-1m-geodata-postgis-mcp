# Docker 编排使用指南

本文档介绍如何使用 Docker Compose 编排和运行 1:100万基础地理信息PostGIS MCP服务。

## 📋 目录结构

项目包含以下 Docker 相关文件：

- `Dockerfile` - MCP 服务器镜像构建文件
- `Dockerfile.importer` - 数据导入服务镜像构建文件
- `Dockerfile.supergateway` - Supergateway网关服务镜像构建文件
- `docker-compose.yml` - 主编排文件（包含所有服务，使用profiles控制）
- `docker-compose.alpine.yml` - Alpine版本配置（轻量级变体）
- `docker-compose.override.yml.example` - 覆盖配置示例
- `.dockerignore` - Docker 构建忽略文件

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Docker Desktop（Windows/Mac）或 Docker Engine（Linux）
- Docker Compose（通常包含在 Docker Desktop 中）

### 2. 配置环境变量

创建 `.env` 文件（在项目根目录）：

```bash
# PostgreSQL 数据库配置
POSTGRES_DB=gis_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432
```

### 3. 启动服务

#### 启动所有服务（数据库 + MCP服务器）

```bash
docker-compose up -d
```

#### 查看服务状态

```bash
docker-compose ps
```

#### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f mcp-server
```

### 4. 停止服务

```bash
# 停止服务（保留数据）
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除容器和数据卷（⚠️ 会删除所有数据）
docker-compose down -v
```

## 📦 服务说明

### PostgreSQL/PostGIS 服务

- **服务名**: `postgres`
- **容器名**: `geodata-postgres`
- **镜像**: `postgis/postgis:16-3.4`
- **端口**: `5432`（可通过环境变量 `POSTGRES_PORT` 修改）
- **数据卷**: `postgres_data`（持久化存储）

**功能**:
- 提供 PostgreSQL 数据库服务
- 自动安装 PostGIS 扩展
- 健康检查确保服务就绪

**连接信息**:
- 主机: `localhost`（宿主机）或 `postgres`（容器内）
- 端口: `5432`（默认）
- 数据库: `gis_data`（默认）
- 用户: `postgres`（默认）
- 密码: 通过环境变量 `POSTGRES_PASSWORD` 设置

### MCP 服务器服务

- **服务名**: `mcp-server`
- **容器名**: `geodata-mcp-server`
- **构建**: 基于 `Dockerfile`
- **依赖**: 等待 PostgreSQL 服务健康检查通过

**功能**:
- 提供 MCP 协议服务
- 通过 stdio 与客户端通信
- 自动连接到 PostgreSQL 数据库

**配置**:
- 数据库连接通过环境变量自动配置
- 配置文件挂载在 `/app/config`
- 规格文件挂载在 `/app/specs`

### 数据导入服务（可选）

- **服务名**: `data-importer`
- **容器名**: `geodata-importer`
- **构建**: 基于 `Dockerfile.importer`
- **默认**: 不自动启动（使用 `profiles: importer`）

**功能**:
- 用于一次性数据导入任务
- 支持导入 GDB 文件到 PostgreSQL

**使用方法**:

```bash
# 启动导入服务并执行导入
docker-compose --profile importer run --rm data-importer \
  python main.py --reset-and-import --gdb-dir /app/data

# 查看导入帮助
docker-compose --profile importer run --rm data-importer \
  python main.py --help
```

## 🔧 高级配置

### 自定义配置

创建 `docker-compose.override.yml` 文件来自定义配置：

```yaml
version: '3.8'

services:
  mcp-server:
    environment:
      DEBUG: "true"
      LOG_LEVEL: "DEBUG"
    volumes:
      # 开发模式：挂载源代码
      - .:/app:rw
```

Docker Compose 会自动加载此文件（如果存在）。

### 网络配置

所有服务连接到 `geodata-network` 网络，服务间可以通过服务名相互访问。

### 数据持久化

PostgreSQL 数据存储在 Docker 卷 `postgres_data` 中，即使删除容器，数据也会保留。

**备份数据**:
```bash
# 备份
docker-compose exec postgres pg_dump -U postgres gis_data > backup.sql

# 恢复
docker-compose exec -T postgres psql -U postgres gis_data < backup.sql
```

## 📝 常用命令

### 构建镜像

```bash
# 构建所有服务镜像
docker-compose build

# 构建特定服务镜像
docker-compose build mcp-server

# 强制重新构建（不使用缓存）
docker-compose build --no-cache
```

### 进入容器

```bash
# 进入 MCP 服务器容器
docker-compose exec mcp-server bash

# 进入 PostgreSQL 容器
docker-compose exec postgres psql -U postgres -d gis_data
```

### 查看资源使用

```bash
# 查看容器资源使用情况
docker-compose top

# 查看容器统计信息
docker stats
```

### 清理

```bash
# 清理未使用的镜像、容器、网络
docker system prune

# 清理所有未使用的资源（包括卷）
docker system prune -a --volumes
```

## 🐛 故障排除

### 数据库连接失败

1. 检查 PostgreSQL 服务是否健康：
   ```bash
   docker-compose ps postgres
   ```

2. 查看 PostgreSQL 日志：
   ```bash
   docker-compose logs postgres
   ```

3. 检查环境变量配置：
   ```bash
   docker-compose config
   ```

### MCP 服务器无法启动

1. 检查依赖关系：
   ```bash
   docker-compose ps
   ```
   确保 PostgreSQL 服务状态为 `healthy`

2. 查看 MCP 服务器日志：
   ```bash
   docker-compose logs mcp-server
   ```

3. 检查配置文件：
   ```bash
   docker-compose exec mcp-server ls -la /app/config
   ```

### 端口冲突

如果端口 5432 已被占用，修改 `.env` 文件中的 `POSTGRES_PORT`：

```bash
POSTGRES_PORT=5433
```

然后重新启动服务。

### 权限问题

如果遇到权限问题，检查挂载的目录权限：

```bash
# Windows: 确保目录可访问
# Linux/Mac: 检查目录权限
chmod -R 755 ./config ./specs
```

## 🔒 安全建议

1. **密码安全**: 使用强密码，不要使用默认密码
2. **网络隔离**: 生产环境建议使用自定义网络
3. **数据备份**: 定期备份数据库
4. **日志管理**: 配置日志轮转，避免日志文件过大
5. **资源限制**: 生产环境建议设置资源限制：

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 📚 相关文档

- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [PostGIS 官方文档](https://postgis.net/documentation/)
- [MCP 协议文档](https://modelcontextprotocol.io/)

