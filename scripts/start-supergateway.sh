#!/bin/bash
# 启动 Supergateway 的独立脚本
# 用于在 Linux 上单独运行 Supergateway，连接到 Docker 中的 MCP 服务器

set -e

# 配置
GATEWAY_PORT=${GATEWAY_PORT:-8000}
MCP_CONTAINER=${MCP_CONTAINER:-geodata-mcp-server}

echo "=========================================="
echo "启动 Supergateway"
echo "=========================================="
echo ""
echo "配置:"
echo "  端口: ${GATEWAY_PORT}"
echo "  MCP容器: ${MCP_CONTAINER}"
echo ""

# 检查 MCP 容器是否运行
if ! docker ps | grep -q "${MCP_CONTAINER}"; then
    echo "错误: MCP 容器 ${MCP_CONTAINER} 未运行"
    echo "请先启动 MCP 服务器: docker-compose up -d mcp-server"
    exit 1
fi

echo "启动 Supergateway..."
echo "访问地址: http://localhost:${GATEWAY_PORT}"
echo "按 Ctrl+C 停止"
echo ""

# 运行 Supergateway
docker run -it --rm \
    --name geodata-supergateway \
    --network geodata-network \
    -p "${GATEWAY_PORT}:${GATEWAY_PORT}" \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    supercorp/supergateway:latest \
    --stdio \
    docker exec -i "${MCP_CONTAINER}" python /app/mcp_server.py \
    --port "${GATEWAY_PORT}" \
    --mode sse

