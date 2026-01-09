# MCP Server 通用配置指南

本文档提供通用的 MCP Server 配置示例，适用于所有 MCP 客户端。

> **⚠️ 重要**：
> - MaxKB 的配置格式与其他客户端不同，请查看 [MaxKB 特殊配置](#maxkb-特殊配置-)部分
> - Supergateway 默认端口：**8000**（SSE），**8001**（WebSocket）
> - 如果使用自定义端口，请相应修改配置中的端口号

## 📋 配置方式

根据部署方式，有两种配置方式：

### 方式1：直接连接 Docker 容器（推荐）⭐⭐⭐

适用于：所有支持 stdio 的 MCP 客户端（Cursor、Claude Desktop、LM Studio 等）

### 方式2：通过 Supergateway 连接（远程访问）

适用于：支持 HTTP/SSE 的 MCP 客户端（某些 Web 应用、自定义客户端）

---

## 方式1：直接连接 Docker 容器

### 通用配置模板

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

- **command**: `"docker"` - Docker CLI 命令
- **args**: 
  - `"exec"` - 在运行中的容器内执行命令
  - `"-i"` - **必需**，保持 stdin 打开，MCP 需要 stdio 通信
  - `"geodata-mcp-server"` - MCP 服务器容器名称（必须与 docker-compose.yml 中一致）
  - `"python"` - Python 命令
  - `"/app/mcp_server.py"` - MCP 服务器脚本路径

### 平台特定配置

#### Windows

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

#### Linux/macOS

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

### 如果容器内使用 python3

如果容器内 Python 命令是 `python3`，修改配置：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "geodata-mcp-server",
        "python3",
        "/app/mcp_server.py"
      ]
    }
  }
}
```

---

## 方式2：通过 Supergateway 连接

### 通用配置模板（SSE）

**标准格式**（适用于大多数客户端，如 Cursor、Claude Desktop 等）：

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

**MaxKB 格式**（MaxKB 使用不同的配置格式，不需要服务名称）：

```json
{
  "mcpServers": {
    "url": "http://localhost:8000/sse",
    "transport": "sse"
  }
}
```

### 配置说明

- **url**: Supergateway 的 SSE 端点地址
  - 本地：`http://localhost:8000/sse`
  - 远程：`http://your-server-ip:8000/sse`
  - 自定义端口和路径示例：`http://your-server-ip:900/china-1m-geodata-postgis-mcp`（如果使用自定义端口）
- **transport**: **必需**，传输协议类型
  - 标准 SSE：`"sse"`
  - MaxKB 推荐：`"streamable_http"`（更好的可扩展性和可靠性）
  - WebSocket：`"ws"` 或 `"websocket"`

### MaxKB 特殊配置 ⭐

MaxKB 的配置格式可能因版本而异。如果遇到 "MCP configuration is invalid" 错误，请尝试以下配置格式：

**方式1：标准格式（带服务名称）⭐⭐⭐ 推荐先尝试**

某些 MaxKB 版本需要服务名称，格式与其他客户端相同：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://ai.vivi141.com:8000/sse",
      "transport": "streamable_http"
    }
  }
}
```

或使用 `sse`：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://ai.vivi141.com:8000/sse",
      "transport": "sse"
    }
  }
}
```

**方式2：简化格式（不带服务名称）**

某些 MaxKB 版本支持简化格式，`mcpServers` 下直接是 `url` 和 `transport`：

```json
{
  "mcpServers": {
    "url": "http://ai.vivi141.com:8000/sse",
    "transport": "streamable_http"
  }
}
```

或使用 `sse`：

```json
{
  "mcpServers": {
    "url": "http://ai.vivi141.com:8000/sse",
    "transport": "sse"
  }
}
```

**方式3：带 name 和 description（如果 MaxKB 要求）**

如果 MaxKB 要求额外的元数据字段：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "name": "China 1M GeoData PostGIS MCP",
      "description": "1:100万基础地理信息PostGIS MCP服务",
      "url": "http://ai.vivi141.com:8000/sse",
      "transport": "streamable_http"
    }
  }
}
```

**远程访问配置**（默认端口8000）：

```json
{
  "mcpServers": {
    "url": "http://your-server-ip:8000/sse",
    "transport": "sse"
  }
}
```

**自定义端口和路径示例**（如果使用自定义配置，如900端口）：

```json
{
  "mcpServers": {
    "url": "http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp",
    "transport": "sse"
  }
}
```

**重要区别**：
- **MaxKB 配置格式**：`mcpServers` 下直接是 `url` 和 `transport`，**没有服务名称**
- **其他客户端格式**：`mcpServers` 下有服务名称对象，如 `"china-1m-geodata-postgis-mcp": { ... }`
- 即使使用 `streamable_http`，URL 仍然指向 SSE 端点（`/sse`）
- `streamable_http` 是 MaxKB 推荐的传输方式，提供更好的可扩展性和可靠性

### 远程访问配置

如果 Supergateway 部署在远程服务器上：

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

**自定义端口和路径示例**（如果使用自定义配置，如900端口和自定义路径）：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp",
      "transport": "sse"
    }
  }
}
```

### WebSocket 配置（如果支持）

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "ws://localhost:8001/ws",
      "transport": "ws"
    }
  }
}
```

---

## 📁 配置文件位置

### Cursor IDE

- **Windows**: `%APPDATA%\Cursor\User\globalStorage\mcp.json`
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/mcp.json`

### Claude Desktop

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### LM Studio

- **Windows**: `%APPDATA%\LM Studio\mcp.json`
- **macOS**: `~/Library/Application Support/LM Studio/mcp.json`
- **Linux**: `~/.config/LM Studio/mcp.json`

**注意**：LM Studio 只支持 stdio 方式，不支持 HTTP/SSE。必须使用**方式1（直接连接 Docker 容器）**。

### MaxKB

MaxKB 的 MCP 配置通常在 Web 界面中配置，或通过配置文件设置。

**配置要求**：
- 只支持 `transport: "sse"` 或 `transport: "streamable_http"`
- 推荐使用 `transport: "streamable_http"`
- URL 指向 Supergateway 的 SSE 端点

---

## 🔧 完整配置示例

### 示例1：Cursor IDE（Windows，Docker方式）

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
      ],
      "env": {
        "DOCKER_HOST": "unix:///var/run/docker.sock"
      }
    }
  }
}
```

### 示例2：Claude Desktop（Windows，Docker方式）

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

### 示例3：LM Studio（Windows，Docker方式）⭐⭐

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

**LM Studio 配置位置**：
- 通过 LM Studio 界面：右侧边栏 → "程序" → "安装" → "编辑 mcp.json"
- 或直接编辑文件：`%APPDATA%\LM Studio\mcp.json`

### 示例4：使用 Supergateway（SSE方式）

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

### 示例5：使用 Supergateway（远程访问，默认端口）

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

### 示例5b：使用 Supergateway（自定义端口和路径）

如果使用自定义端口（如900）和自定义路径：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "url": "http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp",
      "transport": "sse"
    }
  }
}
```

### 示例6：MaxKB 配置 ⭐⭐

MaxKB 的配置格式与其他客户端不同，`mcpServers` 下直接是 `url` 和 `transport`，不需要服务名称：

**使用 sse transport**：

```json
{
  "mcpServers": {
    "url": "http://localhost:8000/sse",
    "transport": "sse"
  }
}
```

**使用 streamable_http transport**（推荐）：

```json
{
  "mcpServers": {
    "url": "http://localhost:8000/sse",
    "transport": "streamable_http"
  }
}
```

**远程访问配置**（默认端口8000）：

```json
{
  "mcpServers": {
    "url": "http://your-server-ip:8000/sse",
    "transport": "sse"
  }
}
```

或使用 streamable_http（推荐）：

```json
{
  "mcpServers": {
    "url": "http://your-server-ip:8000/sse",
    "transport": "streamable_http"
  }
}
```

**自定义端口和路径示例**（如果使用自定义配置，如900端口）：

```json
{
  "mcpServers": {
    "url": "http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp",
    "transport": "sse"
  }
}
```

或使用 streamable_http：

```json
{
  "mcpServers": {
    "url": "http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp",
    "transport": "streamable_http"
  }
}
```

**MaxKB 配置说明**：
- **配置格式**：`mcpServers` 下直接是 `url` 和 `transport`，**不需要服务名称**
- **transport**: 必须设置为 `"sse"` 或 `"streamable_http"`
- **推荐**: 使用 `"streamable_http"`（更好的可扩展性和可靠性）
- **url**: Supergateway 的 SSE 端点地址（即使使用 streamable_http，URL 仍然指向 SSE 端点）

---

## ✅ 验证配置

### 前置条件检查

1. **Docker 服务运行**：
   ```bash
   docker ps
   ```

2. **MCP 服务器容器运行**：
   ```bash
   docker ps | grep geodata-mcp-server
   ```

3. **Supergateway 运行**（如果使用方式2）：
   ```bash
   # 默认端口8000
   # Supergateway 默认不提供 /health 端点，使用 /sse 验证（会保持长连接）
   curl -i --max-time 2 http://localhost:8000/sse
   
   # 如果使用自定义端口（如900）
   curl -i --max-time 2 http://localhost:900/sse
   ```

### 配置验证步骤

1. **检查配置文件格式**：
   - 确保 JSON 格式正确
   - 使用 JSON 验证工具检查语法

2. **重启 MCP 客户端**：
   - 完全关闭客户端
   - 重新启动客户端

3. **测试连接**：
   - 在客户端中查看 MCP 服务器状态
   - 尝试调用工具（如 `list_tile_codes`）

---

## 🔄 切换配置方式

### 从 Docker 切换到 Supergateway

1. 启动 Supergateway：
   ```bash
   docker-compose --profile gateway up -d supergateway
   # 或使用独立脚本
   ./scripts/start-supergateway.sh
   ```

2. 更新配置文件：
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

3. 重启 MCP 客户端

### 从 Supergateway 切换到 Docker

1. 停止 Supergateway（如果不需要）：
   ```bash
   docker-compose stop supergateway
   ```

2. 更新配置文件：
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

3. 重启 MCP 客户端

---

## ⚠️ 常见问题

### 问题1：无法连接到容器

**错误**: `Error: Cannot connect to the Docker daemon`

**解决方案**:
1. 确保 Docker Desktop 正在运行
2. 检查容器是否运行：
   ```bash
   docker ps | grep geodata-mcp-server
   ```
3. 如果容器未运行，启动它：
   ```bash
   docker-compose up -d mcp-server
   ```

### 问题2：权限错误

**错误**: `permission denied while trying to connect to the Docker daemon socket`

**解决方案**:
- **Windows**: 确保 Docker Desktop 正在运行，并且当前用户有权限访问 Docker
- **Linux**: 将用户添加到 docker 组：
  ```bash
  sudo usermod -aG docker $USER
  # 重新登录后生效
  ```

### 问题3：容器内找不到 Python

**错误**: `exec: "python": executable file not found in $PATH`

**解决方案**:
使用 `python3` 替代 `python`：
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

### 问题4：Supergateway 连接失败

**错误**: `Failed to connect to http://localhost:8000/sse`

**解决方案**:
1. 检查 Supergateway 是否运行：
   ```bash
   docker ps | grep supergateway
   ```
2. 检查端口是否被占用：
   ```bash
   netstat -ano | grep :8000
   ```
3. 查看 Supergateway 日志：
   ```bash
   docker-compose logs supergateway
   ```
4. **重要**：确保配置中包含 `"transport": "sse"` 或 `"transport": "streamable_http"`

### 问题5：MaxKB 提示 "MCP configuration is invalid"

**错误**: `[ErrorDetail(string='MCP configuration is invalid', code='invalid')]`

**解决方案**（按顺序尝试）：

1. **尝试标准格式（带服务名称）** ⭐⭐⭐ **优先尝试**
   
   某些 MaxKB 版本需要服务名称，格式与其他客户端相同：
   ```json
   {
     "mcpServers": {
       "china-1m-geodata-postgis-mcp": {
         "url": "http://ai.vivi141.com:8000/sse",
         "transport": "streamable_http"
       }
     }
   }
   ```

2. **检查 URL 协议**
   
   - 如果服务器未配置 HTTPS，使用 `http://` 而不是 `https://`
   - 如果服务器配置了 HTTPS，使用 `https://`
   ```json
   {
     "mcpServers": {
       "china-1m-geodata-postgis-mcp": {
         "url": "http://ai.vivi141.com:8000/sse",
         "transport": "streamable_http"
       }
     }
   }
   ```

3. **尝试简化格式（不带服务名称）**
   
   某些 MaxKB 版本支持简化格式：
   ```json
   {
     "mcpServers": {
       "url": "http://ai.vivi141.com:8000/sse",
       "transport": "streamable_http"
     }
   }
   ```

4. **检查 transport 参数**
   
   - 确保使用 `"sse"` 或 `"streamable_http"`（推荐 `streamable_http`）
   - 不要使用其他值如 `"http"`、`"https"` 等

5. **验证 Supergateway 端点**
   
   在浏览器或使用 curl 测试端点是否可访问：
   ```bash
   # Supergateway 默认无 /health 端点
   curl -i --max-time 2 http://ai.vivi141.com:8000/sse
   ```

6. **检查 JSON 格式**
   
   - 确保 JSON 格式正确，没有语法错误
   - 使用 JSON 验证工具检查（如 https://jsonlint.com/）
   - 确保所有字符串都用双引号

7. **尝试添加 name 和 description（如果 MaxKB 要求）**
   ```json
   {
     "mcpServers": {
       "china-1m-geodata-postgis-mcp": {
         "name": "China 1M GeoData PostGIS MCP",
         "description": "1:100万基础地理信息PostGIS MCP服务",
         "url": "http://ai.vivi141.com:8000/sse",
         "transport": "streamable_http"
       }
     }
   }
   ```

8. **重启 MaxKB**
   
   修改配置后，完全重启 MaxKB 服务

### 问题6：MaxKB 提示 "Only support transport=sse or transport=streamable_http"

**错误**: MaxKB 提示只支持 `transport=sse` 或 `transport=streamable_http`

**解决方案**:
1. **检查配置格式**：MaxKB 的配置格式可能因版本而异，尝试标准格式（带服务名称）：
   ```json
   {
     "mcpServers": {
       "china-1m-geodata-postgis-mcp": {
         "url": "http://localhost:8000/sse",
         "transport": "streamable_http"
       }
     }
   }
   ```
2. **检查 transport 参数**：确保配置中使用的是 `"sse"` 或 `"streamable_http"`，而不是其他值
3. **推荐使用 streamable_http**：
   ```json
   {
     "mcpServers": {
       "china-1m-geodata-postgis-mcp": {
         "url": "http://localhost:8000/sse",
         "transport": "streamable_http"
       }
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
- [ ] 如果使用 Supergateway，配置中包含 `"transport": "sse"`

---

## 📚 相关文档

- [MCP 服务完整指南](MCP_GUIDE.md) - 工具使用和查询工作流程
- [Docker 部署后的 MCP 配置指南](MCP_DOCKER_CONFIG.md) - 详细配置说明
- [Docker 部署指南](DOCKER_GUIDE.md) - Docker 编排说明

---

**更新日期**：2026-01-07
