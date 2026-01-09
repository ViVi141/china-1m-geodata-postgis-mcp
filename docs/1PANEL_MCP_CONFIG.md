# 1Panel MCP服务配置指南（使用项目自带Supergateway）

本指南说明如何在1Panel中使用项目自带的Supergateway网关配置MCP服务。

> **⚠️ 重要**：Supergateway 默认端口为 **8000**（SSE）和 **8001**（WebSocket）。如果使用自定义端口（如900），请相应修改配置。

## 📋 前置条件

1. ✅ 已成功导入数据到PostgreSQL
2. ✅ 已启动基础Docker服务（postgres和mcp-server）
3. ✅ 1Panel已安装并运行

## 🚀 配置步骤

### 步骤1：确认基础服务运行

```bash
# 检查容器状态
docker compose ps

# 应该看到以下容器运行中：
# - geodata-postgres (healthy)
# - geodata-mcp-server (running)
```

### 步骤2：启动项目自带的Supergateway

**方式A：使用独立脚本（推荐）⭐⭐⭐**

```bash
# 进入项目目录
cd /path/to/china-1m-geodata-postgis-mcp

# 启动Supergateway（使用默认端口8000）
./scripts/start-supergateway.sh

# 如果8000端口被占用，可以自定义端口（如900）
export GATEWAY_PORT=900
./scripts/start-supergateway.sh
```

**方式B：使用docker-compose**

```bash
# 构建包含Docker CLI的Supergateway镜像
docker compose build supergateway

# 启动Supergateway（使用默认端口8000）
docker compose --profile gateway up -d supergateway

# 如果8000端口被占用，可以自定义端口（如900）
GATEWAY_SSE_PORT=900 docker compose --profile gateway up -d supergateway
```

**方式C：手动运行Supergateway容器**

```bash
# 运行Supergateway容器（使用默认端口8000）
docker run -d \
    --name geodata-supergateway \
    --network geodata-network \
    -p 8000:8000 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v /usr/bin/docker:/usr/bin/docker:ro \
    supercorp/supergateway:latest \
    --stdio \
    sh -c "docker exec -i geodata-mcp-server python /app/mcp_server.py" \
    --port 8000 \
    --mode sse

# 如果使用自定义端口和路径（如900端口，自定义路径）
docker run -d \
    --name geodata-supergateway \
    --network geodata-network \
    -p 900:900 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v /usr/bin/docker:/usr/bin/docker:ro \
    supercorp/supergateway:latest \
    --stdio \
    sh -c "docker exec -i geodata-mcp-server python /app/mcp_server.py" \
    --port 900 \
    --mode sse \
    --baseUrl http://ai.vivi141.com \
    --ssePath /china-1m-geodata-postgis-mcp
```

### 步骤3：验证Supergateway运行

```bash
# 检查容器状态
docker ps | grep supergateway

# 查看日志
docker logs geodata-supergateway

# 注意：Supergateway 默认不提供 /health 端点，使用 /sse 验证（会保持长连接）
curl -i --max-time 2 http://localhost:8000/sse

# 如果使用自定义端口（如900），替换为相应端口
curl -i --max-time 2 http://localhost:900/sse
curl http://localhost:900/china-1m-geodata-postgis-mcp
```

### 步骤4：在1Panel中配置MCP服务（使用HTTP/SSE方式）

如果1Panel支持HTTP/SSE方式连接已运行的Supergateway：

1. **登录1Panel管理界面**

2. **进入MCP服务管理**
   - 方式A：直接进入 **MCP服务** 菜单
   - 方式B：进入 **应用商店** → **MCP服务**

3. **添加MCP服务**
   - 点击 **添加MCP服务** 或 **新建服务** 按钮

4. **填写配置信息**

   | 配置项 | 配置值 | 说明 |
   |--------|--------|------|
   | **类型** | `http` 或 `sse` | 使用HTTP/SSE方式连接 |
   | **外部访问路径** | `http://your-server-ip:8000/sse` | Supergateway的SSE端点URL<br>默认端口：8000<br>自定义端口示例：`http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp` |
   | **端口** | `8000` | Supergateway的端口（默认8000，如果自定义了端口则使用自定义端口） |
   | **输出类型** | `sse` | 使用SSE（Server-Sent Events）输出 |
   | **transport** | `sse` | **必需**，传输协议类型，必须设置为 `sse` |

   **注意**：
   - Supergateway已独立运行，1Panel只需要配置连接方式
   - 外部访问路径应该是完整的SSE端点URL
   - **transport参数**：如果1Panel支持JSON配置，必须添加 `"transport": "sse"`
   - 如果1Panel不支持HTTP/SSE方式，可以跳过此步骤，直接使用Supergateway的端点
   
   **JSON配置示例**（如果1Panel支持）：
   
   **标准格式**（大多数客户端）：
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
   
   **MaxKB格式**（MaxKB使用不同的配置格式）：
   ```json
   {
     "mcpServers": {
       "url": "http://your-server-ip:8000/sse",
       "transport": "sse"
     }
   }
   ```
   
   **自定义端口示例**（如果使用自定义端口，如900）：
   ```json
   {
     "mcpServers": {
       "url": "http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp",
       "transport": "sse"
     }
   }
   ```

## 🔧 使用systemd服务（生产环境推荐）

为了确保Supergateway在系统重启后自动启动：

```bash
# 创建服务文件
sudo tee /etc/systemd/system/geodata-supergateway.service > /dev/null <<EOF
[Unit]
Description=GeoData Supergateway Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
ExecStart=/usr/bin/docker run --rm \
    --name geodata-supergateway \
    --network geodata-network \
    -p 8000:8000 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v /usr/bin/docker:/usr/bin/docker:ro \
    supercorp/supergateway:latest \
    --stdio \
    sh -c "docker exec -i geodata-mcp-server python /app/mcp_server.py" \
    --port 8000 \
    --mode sse

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable geodata-supergateway
sudo systemctl start geodata-supergateway
sudo systemctl status geodata-supergateway
```

## 📝 配置说明

### 端口配置

- **默认端口**：8000（SSE），8001（WebSocket）
- **自定义端口**：如果8000被占用，可以自定义端口（如900）
- 确保端口未被占用且防火墙已开放

### 访问端点

**默认端口（8000）**：
- **SSE端点**：`http://your-server-ip:8000/sse`
- **说明**：默认无 `/health` 端点

**自定义端口和路径示例**（如果使用自定义配置）：
- **SSE端点**：`http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp`
- **消息端点**：`http://ai.vivi141.com:900/china-1m-geodata-postgis-mcp/messages`

### 环境变量（可选）

如果需要自定义配置，可以在启动Supergateway时设置环境变量：

```bash
# 默认配置（端口8000）
export GATEWAY_PORT=8000

# 自定义端口示例（如果8000被占用）
export GATEWAY_PORT=900
export BASE_URL=http://ai.vivi141.com
export SSE_PATH=/china-1m-geodata-postgis-mcp
```

## ⚠️ 常见问题

### 问题1：docker: not found 错误

**症状**：Supergateway日志显示 `docker: not found`

**解决方案**：
1. 确保宿主机已安装Docker CLI：
   ```bash
   # CentOS/RHEL/OpenCloudOS
   sudo yum install -y docker
   ```
2. 使用方式C（手动运行）时，确保挂载了Docker CLI：
   ```bash
   -v /usr/bin/docker:/usr/bin/docker:ro
   ```

### 问题2：容器无法连接到geodata-mcp-server

**症状**：Supergateway无法连接到MCP服务器容器

**解决方案**：
1. 确保两个容器在同一网络：
   ```bash
   --network geodata-network
   ```
2. 检查MCP服务器容器是否运行：
   ```bash
   docker ps | grep geodata-mcp-server
   ```

### 问题3：端口被占用

**症状**：启动Supergateway时提示端口被占用

**解决方案**：
1. 检查端口占用：
   ```bash
   netstat -tuln | grep 900
   ```
2. 使用其他端口或停止占用端口的服务

## 🎯 优势

使用项目自带的Supergateway的优势：

- ✅ **完全控制**：可以自定义所有配置参数
- ✅ **稳定可靠**：不依赖1Panel的Supergateway实现
- ✅ **易于调试**：可以直接查看容器日志
- ✅ **灵活配置**：支持自定义端口、路径、域名等
- ✅ **生产就绪**：支持systemd服务，自动重启

## 📚 相关文档

- [Docker快速开始指南](../README_DOCKER.md) - 基础服务启动
- [MCP客户端配置指南](MCP_DOCKER_CONFIG.md) - 如何配置MCP客户端连接
- [MCP服务完整指南](MCP_GUIDE.md) - MCP工具使用和查询工作流程

---

**更新日期**：2026-01-07
