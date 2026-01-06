#!/bin/bash
# Docker 容器入口脚本
# 自动生成数据库配置文件（如果不存在）

set -e

CONFIG_DIR="/app/config"
CONFIG_FILE="${CONFIG_DIR}/database.ini"

# 创建配置目录
mkdir -p "${CONFIG_DIR}"

# 如果配置文件不存在，或需要更新（检查host是否为localhost），从环境变量生成/更新
NEED_UPDATE=false
if [ ! -f "${CONFIG_FILE}" ]; then
    NEED_UPDATE=true
    echo "配置文件不存在，将生成..."
elif grep -q "host = localhost" "${CONFIG_FILE}" 2>/dev/null || [ -n "${DB_HOST}" ]; then
    NEED_UPDATE=true
    echo "检测到配置文件使用localhost或环境变量已设置，将更新..."
fi

if [ "$NEED_UPDATE" = true ]; then
    echo "生成/更新数据库配置文件..."
    cat > "${CONFIG_FILE}" <<EOF
[postgresql]
host = ${DB_HOST:-postgres}
port = ${DB_PORT:-5432}
database = ${DB_NAME:-gis_data}
user = ${DB_USER:-postgres}
password = ${DB_PASSWORD:-postgres}
EOF
    echo "配置文件已生成/更新: ${CONFIG_FILE}"
fi

# 显示配置信息（不显示密码）
echo "数据库配置:"
echo "  主机: ${DB_HOST:-postgres}"
echo "  端口: ${DB_PORT:-5432}"
echo "  数据库: ${DB_NAME:-gis_data}"
echo "  用户: ${DB_USER:-postgres}"

# 执行传入的命令
exec "$@"

