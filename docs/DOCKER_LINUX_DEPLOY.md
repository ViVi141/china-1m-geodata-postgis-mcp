# Linux Docker 部署指南

本指南介绍如何在 Linux 环境下使用 Docker 部署 1:100万基础地理信息PostGIS MCP服务。

## 📋 前置要求

### 系统要求

- **Linux 系统**（Ubuntu 20.04+, Debian 11+, CentOS 8+, 或其他主流发行版）
- **Docker 20.10+**
- **Docker Compose 2.0+**（或使用 `docker compose` 命令）

### 安装 Docker

#### Ubuntu/Debian

```bash
# 更新包索引
sudo apt-get update

# 安装必要的依赖
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组（可选，避免每次使用sudo）
sudo usermod -aG docker $USER
# 需要重新登录才能生效
```

#### CentOS/RHEL

```bash
# 安装必要的工具
sudo yum install -y yum-utils

# 添加Docker仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组
sudo usermod -aG docker $USER
```

### 验证安装

```bash
# 检查Docker版本
docker --version
docker compose version

# 测试Docker
docker run hello-world
```

## 🚀 快速部署

### 1. 克隆或下载项目

```bash
# 如果使用Git
git clone <repository-url>
cd gdb_mcp

# 或直接下载并解压项目文件
```

### 2. 创建环境变量文件

在项目根目录创建 `.env` 文件：

```bash
cat > .env <<EOF
# PostgreSQL 数据库配置
POSTGRES_DB=gis_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432

# Supergateway 配置（可选）
GATEWAY_SSE_PORT=8000
GATEWAY_WS_PORT=8001
GATEWAY_LOG_LEVEL=info
EOF
```

**重要**：修改 `POSTGRES_PASSWORD` 为强密码！

### 3. 启动服务（基础版 - 不使用Supergateway）

```bash
# 启动所有服务（不包括supergateway）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 启动服务（完整版 - 使用Supergateway）

#### 方式1：使用 Docker Compose

```bash
# 启动所有服务，包括Supergateway网关
docker-compose --profile gateway up -d

# 查看服务状态
docker-compose ps
```

#### 方式2：使用独立脚本（推荐）

```bash
# 先启动基础服务
docker-compose up -d

# 使用独立脚本启动Supergateway
chmod +x scripts/start-supergateway.sh
./scripts/start-supergateway.sh
```

### 5. 验证服务

```bash
# 检查PostgreSQL
docker-compose exec postgres psql -U postgres -d gis_data -c "SELECT PostGIS_Version();"

# 检查Supergateway（如果启用）
# Supergateway 默认不提供 /health 端点，使用 /sse 验证（会保持长连接）
curl -i --max-time 2 http://localhost:8000/sse

# 查看所有服务日志
docker-compose logs -f
```

## 📦 服务架构

### 服务组成

1. **postgres** - PostgreSQL/PostGIS 数据库
   - 端口: `5432`
   - 数据持久化: Docker 卷 `postgres_data`

2. **mcp-server** - MCP 服务器（stdio 模式）
   - 通过 stdio 与客户端通信
   - 自动连接 PostgreSQL

3. **supergateway** - MCP 网关服务（可选）
   - SSE 端口: `8000`
   - WebSocket 端口: `8001`
   - 将 stdio 模式转换为 HTTP/SSE/WebSocket

4. **data-importer** - 数据导入服务（可选）
   - 使用 `--profile importer` 启动

### 网络架构

```
┌─────────────┐
│   Client    │
│  (MCP工具)   │
└──────┬──────┘
       │
       │ HTTP/SSE/WebSocket
       │
┌──────▼──────────┐
│  Supergateway   │  ← 可选，用于远程访问
│   (端口8000)    │
└──────┬──────────┘
       │
       │ stdio
       │
┌──────▼──────────┐
│   MCP Server    │
│  (mcp_server.py)│
└──────┬──────────┘
       │
       │ PostgreSQL协议
       │
┌──────▼──────────┐
│  PostgreSQL/    │
│    PostGIS      │
│   (端口5432)    │
└─────────────────┘
```

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `POSTGRES_DB` | `gis_data` | 数据库名称 |
| `POSTGRES_USER` | `postgres` | 数据库用户 |
| `POSTGRES_PASSWORD` | `postgres` | 数据库密码（**必须修改**） |
| `POSTGRES_PORT` | `5432` | 数据库端口 |
| `GATEWAY_SSE_PORT` | `8000` | Supergateway SSE 端口 |
| `GATEWAY_WS_PORT` | `8001` | Supergateway WebSocket 端口 |
| `GATEWAY_LOG_LEVEL` | `info` | Supergateway 日志级别 |

### 端口说明

- **5432**: PostgreSQL 数据库（可通过 `POSTGRES_PORT` 修改）
- **8000**: Supergateway SSE 服务（可通过 `GATEWAY_SSE_PORT` 修改）
- **8001**: Supergateway WebSocket 服务（可通过 `GATEWAY_WS_PORT` 修改）

## 📝 使用 Supergateway

Supergateway 可以将 stdio 模式的 MCP 服务器转换为 HTTP/SSE/WebSocket 服务，支持远程访问。

### 访问端点

- **SSE**: `http://localhost:8000/sse`
- **WebSocket**: `ws://localhost:8001/ws`

**注意**：Supergateway 默认不提供 `/health` 端点，使用 `/sse` 验证服务可用性。

### 配置 MCP 客户端

如果使用 Supergateway，MCP 客户端配置示例：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

详细配置说明请查看 [Docker 部署后的 MCP 配置指南](MCP_DOCKER_CONFIG.md)

## 🛠️ 数据导入

### 导入 GDB 数据

```bash
# 使用数据导入服务
docker-compose --profile importer run --rm data-importer \
  python main.py --reset-and-import --gdb-dir /app/data

# 如果GDB文件在项目根目录
docker-compose --profile importer run --rm data-importer \
  python main.py --reset-and-import --gdb-dir /app/data --reference-tile F49
```

## 🔍 监控和调试

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f mcp-server
docker-compose logs -f supergateway

# 查看最近100行日志
docker-compose logs --tail=100 mcp-server
```

### 进入容器

```bash
# 进入MCP服务器容器
docker-compose exec mcp-server bash

# 进入PostgreSQL容器
docker-compose exec postgres psql -U postgres -d gis_data

# 进入Supergateway容器
docker-compose exec supergateway sh
```

### 检查服务健康

```bash
# 检查PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# 检查Supergateway
curl -i --max-time 2 http://localhost:8000/sse

# 检查所有服务状态
docker-compose ps
```

## 🔒 安全建议

### 1. 修改默认密码

**必须**修改 `.env` 文件中的 `POSTGRES_PASSWORD`：

```bash
# 生成强密码
openssl rand -base64 32

# 更新.env文件
POSTGRES_PASSWORD=<生成的强密码>
```

### 2. 防火墙配置

如果服务器暴露在公网，配置防火墙：

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 5432/tcp  # PostgreSQL（仅内网）
sudo ufw allow 8000/tcp  # Supergateway SSE
sudo ufw allow 8001/tcp  # Supergateway WebSocket

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload
```

### 3. 限制数据库访问

默认情况下，PostgreSQL 端口 `5432` 不应暴露到公网。如果必须暴露，使用 VPN、SSH 隧道或 IP 白名单。

## 🐛 故障排除

### 问题1: Supergateway 无法连接到 mcp-server

**症状**: Supergateway 日志显示连接失败

**解决方案**:
1. 确保 mcp-server 容器正在运行：
   ```bash
   docker-compose ps mcp-server
   ```

2. 检查 Docker socket 权限：
   ```bash
   ls -l /var/run/docker.sock
   sudo chmod 666 /var/run/docker.sock  # 临时解决方案
   ```

3. 检查网络连接：
   ```bash
   docker-compose exec supergateway ping mcp-server
   ```

### 问题2: 端口冲突

**症状**: 端口已被占用

**解决方案**:
1. 检查端口占用：
   ```bash
   sudo netstat -tulpn | grep :8000
   ```

2. 修改 `.env` 文件中的端口配置

### 问题3: 数据库连接失败

**症状**: MCP 服务器无法连接数据库

**解决方案**:
1. 检查 PostgreSQL 是否健康：
   ```bash
   docker-compose exec postgres pg_isready
   ```

2. 检查环境变量：
   ```bash
   docker-compose config
   ```

3. 查看数据库日志：
   ```bash
   docker-compose logs postgres
   ```

## 📚 相关文档

- [Docker 快速开始指南](../README_DOCKER.md)
- [Docker 部署后的 MCP 配置指南](MCP_DOCKER_CONFIG.md)
- [MCP 服务完整指南](MCP_GUIDE.md)
- [1Panel MCP 配置指南](1PANEL_MCP_CONFIG.md)

