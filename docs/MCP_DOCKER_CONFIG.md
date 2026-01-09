# Docker 部署后的 MCP 客户端配置指南

本文档说明如何在 Docker 部署成功后，配置 MCP 客户端（如 Cursor、Claude Desktop、LM Studio）连接到 MCP 服务器。

> **💡 提示**：需要快速配置？查看 [MCP Server 通用配置指南](MCP_SERVER_CONFIG.md) 获取通用配置模板。

## ⚠️ 重要提示

- **LM Studio 用户**：LM Studio 只支持 stdio 方式的 MCP 连接，请使用**方式1（直接连接 Docker 容器）**
- **其他客户端**：Cursor、Claude Desktop 等可以使用方式1或方式2

## 📋 配置方式

根据你的使用场景，有两种配置方式：

### 方式1：直接连接 Docker 容器（推荐）⭐⭐⭐

直接通过 `docker exec` 连接到运行中的 MCP 服务器容器。

### 方式2：通过 Supergateway 连接（远程访问）

如果使用 Supergateway，可以通过 HTTP/SSE 连接。

---

## 方式1：直接连接 Docker 容器

### 前置条件

1. Docker 服务已启动
2. MCP 服务器容器正在运行：
   ```powershell
   docker-compose up -d mcp-server
   ```

### 配置文件位置

#### Cursor IDE
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\mcp.json`
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/mcp.json`

#### Claude Desktop
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### LM Studio
- **Windows**: `%APPDATA%\LM Studio\mcp.json` 或通过 LM Studio 界面编辑
- **macOS**: `~/Library/Application Support/LM Studio/mcp.json`
- **Linux**: `~/.config/LM Studio/mcp.json`

**注意**：LM Studio 只支持 stdio 方式的 MCP 连接，不支持 HTTP/SSE。请使用**方式1（直接连接 Docker 容器）**。

### 配置示例

**Windows/Linux/macOS（通用配置）：**

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "geodata-mcp-server",
        "python",
        "/app/mcp_server.py"
      ]
    }
  }
}
```

### 配置说明

- **command**: `docker` - Docker CLI 命令
- **args**: 
  - `exec` - 在运行中的容器内执行命令
  - `-i` - 保持 stdin 打开（必需，MCP 需要 stdio 通信）
  - `geodata-mcp-server` - MCP 服务器容器名称
  - `python /app/mcp_server.py` - 在容器内执行的命令

### 验证配置

1. 重启 MCP 客户端（Cursor、Claude Desktop 或 LM Studio）
2. 检查 MCP 服务器是否连接成功
3. 测试工具：使用 `list_tile_codes` 查看可用的图幅代码

### LM Studio 配置步骤

1. 打开 LM Studio
2. 在右侧边栏切换到"程序"选项卡
3. 点击"安装"下的"编辑 mcp.json"
4. 使用上面的配置（方式1：直接连接 Docker 容器）
5. 保存配置文件
6. 重启 LM Studio 或重新加载 MCP 服务器

**重要**：LM Studio 只支持 stdio 方式，不支持 HTTP/SSE。必须使用方式1的配置。

---

## 方式2：通过 Supergateway 连接

> **⚠️ 注意**：LM Studio **不支持** HTTP/SSE 方式的 MCP 连接，只支持 stdio 方式。如果你使用 LM Studio，请使用**方式1（直接连接 Docker 容器）**。

### 前置条件

1. Supergateway 服务已启动：
   ```powershell
   # 方式A: 使用 Docker Compose
   docker-compose --profile gateway up -d
   
   # 方式B: 使用独立脚本（推荐）
   .\scripts\start-supergateway.bat
   ```

2. 验证 Supergateway 运行：
   ```powershell
   # Supergateway 默认不提供 /health 端点，使用 /sse 验证（会保持长连接）
   curl http://localhost:8000/sse
   ```

### 配置示例

#### 标准 SSE 配置（适用于大多数客户端）

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

#### MaxKB 配置（特殊格式）

MaxKB 的配置格式不同，`mcpServers` 下直接是 `url` 和 `transport`，不需要服务名称：

```json
{
  "mcpServers": {
    "url": "http://localhost:8000/sse",
    "transport": "streamable_http"
  }
}
```

#### 远程访问配置

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://your-server-ip:8000/sse",
      "transport": "sse"
    }
  }
}
```

#### WebSocket 配置（如果支持）

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "ws://localhost:8001/ws"
    }
  }
}
```

### 配置说明

- **url**: Supergateway 的端点地址
  - SSE: `http://localhost:8000/sse`
  - WebSocket: `ws://localhost:8001/ws`
  - 注意：默认无 `/health` 端点（日志会显示 "Health endpoints: (none)"）
- **transport**: 传输协议类型（使用SSE时必需）
  - SSE: `"sse"`
  - MaxKB 推荐: `"streamable_http"`（更好的可扩展性和可靠性）
  - WebSocket: `"ws"` 或 `"websocket"`

### 支持的客户端

- ✅ **支持 HTTP/SSE 的客户端**：某些 Web 应用、自定义 MCP 客户端
- ❌ **不支持 HTTP/SSE 的客户端**：LM Studio、大多数桌面 MCP 客户端

### 远程访问

如果 Supergateway 部署在远程服务器上，将 `localhost` 替换为服务器 IP 或域名：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://your-server-ip:8000/sse",
      "transport": "sse"
    }
  }
}
```

---

## 🔧 完整配置示例

### 方式1：直接连接 Docker 容器（推荐）

**Windows/Linux/macOS（通用配置）：**

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "geodata-mcp-server",
        "python",
        "/app/mcp_server.py"
      ]
    }
  }
}
```

### 方式2：通过 Supergateway 连接

**标准 SSE 配置：**

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

---

## 🐛 故障排除

### 问题1: 无法连接到容器

**错误**: `Error: Cannot connect to the Docker daemon`

**解决方案**:
1. 确保 Docker Desktop 正在运行
2. 检查容器是否运行：
   ```powershell
   docker ps | findstr geodata-mcp-server
   ```
3. 如果容器未运行，启动它：
   ```powershell
   docker-compose up -d mcp-server
   ```

### 问题2: 权限错误

**错误**: `permission denied while trying to connect to the Docker daemon socket`

**解决方案**:
- Windows: 确保 Docker Desktop 正在运行，并且当前用户有权限访问 Docker
- Linux: 将用户添加到 docker 组：
  ```bash
  sudo usermod -aG docker $USER
  # 重新登录后生效
  ```

### 问题3: 容器内找不到 Python

**错误**: `exec: "python": executable file not found in $PATH`

**解决方案**:
检查容器内 Python 路径，可能需要使用 `python3`：
```json
{
  "args": [
    "exec",
    "-i",
    "geodata-mcp-server",
    "python3",
    "/app/mcp_server.py"
  ]
}
```

### 问题4: Supergateway 连接失败

**错误**: `Failed to connect to http://localhost:8000/sse`

**解决方案**:
1. 检查 Supergateway 是否运行：
   ```powershell
   docker ps | findstr supergateway
   ```
2. 检查端口是否被占用：
   ```powershell
   netstat -ano | findstr :8000
   ```
3. 查看 Supergateway 日志：
   ```powershell
   docker-compose logs supergateway
   ```

### 问题5: MaxKB 提示 "Only support transport=sse or transport=streamable_http"

**错误**: MaxKB 提示只支持 `transport=sse` 或 `transport=streamable_http`

**解决方案**:
1. **检查配置格式**：MaxKB 的配置格式与其他客户端不同，`mcpServers` 下直接是 `url` 和 `transport`，**不需要服务名称**：
   ```json
   {
     "mcpServers": {
       "url": "http://localhost:8000/sse",
       "transport": "streamable_http"
     }
   }
   ```
2. **使用 streamable_http**（推荐）：
   ```json
   {
     "mcpServers": {
       "url": "http://localhost:8000/sse",
       "transport": "streamable_http"
     }
   }
   ```
3. **或使用 sse**：
   ```json
   {
     "mcpServers": {
       "url": "http://localhost:8000/sse",
       "transport": "sse"
     }
   }
   ```
4. **检查 JSON 格式**：确保 JSON 格式正确，没有语法错误
5. **重启 MaxKB**：修改配置后，重启 MaxKB 服务

---

## 📝 快速检查清单

配置完成后，按以下步骤验证：

- [ ] Docker 服务正在运行
- [ ] MCP 服务器容器正在运行 (`docker ps`)
- [ ] 配置文件格式正确（JSON 语法）
- [ ] 配置文件路径正确
- [ ] 已重启 MCP 客户端
- [ ] 可以调用 MCP 工具（如 `list_tile_codes`）

---

## 🔄 切换配置方式

### 从本地 Python 切换到 Docker

如果你之前使用本地 Python 环境，切换到 Docker：

1. 停止本地 MCP 服务器（如果有）
2. 启动 Docker 容器：
   ```powershell
   docker-compose up -d mcp-server
   ```
3. 更新 MCP 配置文件（使用方式1的配置）
4. 重启 MCP 客户端

### 从 Docker 切换到 Supergateway

1. 启动 Supergateway：
   ```powershell
   docker-compose --profile gateway up -d
   ```
2. 更新 MCP 配置文件（使用方式2的配置）
3. 重启 MCP 客户端

---

## 📚 相关文档

- [MCP Server 通用配置指南](MCP_SERVER_CONFIG.md) - 通用配置模板
- [MCP 服务完整指南](MCP_GUIDE.md) - 工具使用和查询工作流程
- [Docker 快速开始指南](../README_DOCKER.md) - Docker 快速启动
- [Linux Docker 部署指南](DOCKER_LINUX_DEPLOY.md) - Linux 部署步骤
- [Windows Docker 部署指南](DOCKER_WINDOWS_DEPLOY.md) - Windows 部署步骤

