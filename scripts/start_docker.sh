#!/bin/bash
# Linux/Mac shell脚本 - 启动PostgreSQL/PostGIS容器

echo "========================================"
echo "启动PostgreSQL/PostGIS容器"
echo "========================================"
echo ""

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker"
    exit 1
fi

echo "[1/3] 检查postgis/postgis镜像..."
if ! docker images postgis/postgis --format "{{.Repository}}:{{.Tag}}" | grep -q postgis; then
    echo "错误: 未找到postgis/postgis镜像"
    echo "请在Docker Desktop中下载镜像，或运行: docker pull postgis/postgis:latest"
    exit 1
fi

echo "[2/3] 启动容器..."
docker run -d \
  --name geodata-postgres \
  -e POSTGRES_DB=gis_data \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v geodata_postgres_data:/var/lib/postgresql/data \
  postgis/postgis:latest

if [ $? -ne 0 ]; then
    echo ""
    echo "警告: 容器可能已存在，尝试启动现有容器..."
    docker start geodata-postgres
    if [ $? -ne 0 ]; then
        echo "错误: 无法启动容器"
        exit 1
    fi
fi

echo "[3/3] 等待PostgreSQL启动..."
sleep 5

# 初始化PostGIS扩展
echo "初始化PostGIS扩展..."
docker exec geodata-postgres psql -U postgres -d gis_data -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null

echo ""
echo "========================================"
echo "容器已启动！"
echo "========================================"
echo ""
echo "容器名称: geodata-postgres"
echo "数据库: gis_data"
echo "用户: postgres"
echo "密码: postgres"
echo "端口: 5432"
echo ""
echo "查看日志: docker logs -f geodata-postgres"
echo "停止容器: docker stop geodata-postgres"
echo "删除容器: docker rm geodata-postgres"
echo ""

