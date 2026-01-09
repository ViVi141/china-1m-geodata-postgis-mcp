#!/bin/bash
# Supergateway 部署验证脚本
# 用于验证 Linux Docker 环境下的 Supergateway 配置是否正确

set -e

echo "=========================================="
echo "🔍 Supergateway 部署验证"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
echo "📋 检查 Docker 状态..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker 服务"
    exit 1
fi
echo "✅ Docker 正在运行"
echo ""

# 检查 docker-compose 是否可用
echo "📋 检查 Docker Compose..."
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi
echo "✅ Docker Compose 可用"
echo ""

# 检查服务状态
echo "📊 检查服务状态..."
if ! docker-compose ps >/dev/null 2>&1; then
    echo "❌ 无法获取服务状态，可能项目目录不正确"
    echo "请确保在项目根目录运行此脚本"
    exit 1
fi

SERVICES=$(docker-compose ps --services --filter "status=running")
echo "运行中的服务："
echo "$SERVICES"
echo ""

# 检查关键服务
REQUIRED_SERVICES=("postgres" "mcp-server" "supergateway")
for service in "${REQUIRED_SERVICES[@]}"; do
    if echo "$SERVICES" | grep -q "$service"; then
        echo "✅ $service 服务正在运行"
    else
        echo "❌ $service 服务未运行"
        MISSING_SERVICES+=("$service")
    fi
done

if [ ${#MISSING_SERVICES[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  以下服务未运行："
    printf '   - %s\n' "${MISSING_SERVICES[@]}"
    echo ""
    echo "启动命令："
    echo "  docker-compose --profile gateway up -d"
    exit 1
fi
echo ""

# 检查端口监听
echo "🔌 检查端口监听..."
GATEWAY_PORT=${GATEWAY_SSE_PORT:-8000}

if netstat -tuln 2>/dev/null | grep -q ":$GATEWAY_PORT "; then
    echo "✅ 端口 $GATEWAY_PORT 正在监听"
else
    echo "❌ 端口 $GATEWAY_PORT 未监听"
    echo "检查 Supergateway 日志："
    echo "  docker-compose logs supergateway"
    exit 1
fi
echo ""

# 测试 SSE 端点
echo "🌐 测试 SSE 端点..."
SSE_URL="http://localhost:$GATEWAY_PORT/sse"

if curl -s --max-time 5 "$SSE_URL" >/dev/null 2>&1; then
    echo "✅ SSE 端点可访问: $SSE_URL"
else
    echo "❌ SSE 端点不可访问: $SSE_URL"
    echo "可能的原因："
    echo "  - Supergateway 未正确启动"
    echo "  - 端口配置错误"
    echo "  - 防火墙阻止访问"
fi
echo ""

# 检查容器日志
echo "📝 检查 Supergateway 日志（最近10行）..."
if docker-compose logs --tail=10 supergateway 2>/dev/null; then
    echo ""
else
    echo "❌ 无法获取 Supergateway 日志"
fi

# 检查数据库连接
echo "💾 检查数据库连接..."
if docker-compose exec -T postgres pg_isready -U postgres -d gis_data >/dev/null 2>&1; then
    echo "✅ PostgreSQL 数据库可连接"
else
    echo "❌ PostgreSQL 数据库连接失败"
fi
echo ""

# 检查网络配置
echo "🌐 检查 Docker 网络..."
if docker network ls | grep -q "geodata-network"; then
    echo "✅ geodata-network 网络存在"
else
    echo "❌ geodata-network 网络不存在"
fi
echo ""

echo "=========================================="
echo "🎯 验证完成"
echo "=========================================="
echo ""
echo "如果所有检查都通过 ✅，Supergateway 部署成功！"
echo ""
echo "MCP 客户端配置示例："
echo "  URL: http://localhost:$GATEWAY_PORT/sse"
echo "  Transport: streamable_http"
echo ""
echo "查看实时日志："
echo "  docker-compose logs -f supergateway"
echo ""
echo "停止服务："
echo "  docker-compose --profile gateway down"