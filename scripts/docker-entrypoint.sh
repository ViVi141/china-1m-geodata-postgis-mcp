#!/bin/bash
# Docker 容器入口脚本
# 自动生成数据库配置文件（如果不存在）

set -e

CONFIG_DIR="/app/config"
CONFIG_FILE="${CONFIG_DIR}/database.ini"

# 创建配置目录
mkdir -p "${CONFIG_DIR}"

# 检查是否需要更新配置文件
# 如果配置文件不存在，或host为localhost，或环境变量已设置，则更新
NEED_UPDATE=false

if [ ! -f "${CONFIG_FILE}" ]; then
    NEED_UPDATE=true
    echo "配置文件不存在，将生成..."
elif grep -q "host = localhost" "${CONFIG_FILE}" 2>/dev/null; then
    NEED_UPDATE=true
    echo "检测到配置文件使用localhost，将更新为容器环境配置..."
elif [ -n "${DB_HOST}" ] || [ -n "${DB_PASSWORD}" ] || [ -n "${DB_NAME}" ] || [ -n "${DB_USER}" ]; then
    # 如果环境变量已设置，检查配置是否需要更新
    # 读取当前配置中的密码（如果有）
    CURRENT_PASSWORD=$(grep "^password" "${CONFIG_FILE}" 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo "")
    ENV_PASSWORD="${DB_PASSWORD:-postgres}"
    
    # 如果密码不匹配，需要更新
    if [ "${CURRENT_PASSWORD}" != "${ENV_PASSWORD}" ]; then
        NEED_UPDATE=true
        echo "检测到配置文件密码与环境变量不一致，将更新..."
    elif [ -n "${DB_HOST}" ]; then
        CURRENT_HOST=$(grep "^host" "${CONFIG_FILE}" 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo "")
        if [ "${CURRENT_HOST}" != "${DB_HOST}" ]; then
            NEED_UPDATE=true
            echo "检测到配置文件主机名与环境变量不一致，将更新..."
        fi
    fi
fi

# 在Docker容器中，总是从环境变量更新配置以确保一致性
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
    # 验证配置文件内容（显示密码前3个字符用于调试）
    CONFIG_PASSWORD=$(grep '^password' "${CONFIG_FILE}" | cut -d'=' -f2 | tr -d ' ')
    if [ -n "${CONFIG_PASSWORD}" ]; then
        PASSWORD_PREVIEW="${CONFIG_PASSWORD:0:3}***"
        echo "验证: host=$(grep '^host' "${CONFIG_FILE}" | cut -d'=' -f2 | tr -d ' '), password=${PASSWORD_PREVIEW}"
    fi
fi

# 显示配置信息（不显示密码）
echo "数据库配置:"
echo "  主机: ${DB_HOST:-postgres}"
echo "  端口: ${DB_PORT:-5432}"
echo "  数据库: ${DB_NAME:-gis_data}"
echo "  用户: ${DB_USER:-postgres}"
echo "  密码: ${DB_PASSWORD:+***已设置***}"
if [ -z "${DB_PASSWORD}" ]; then
    echo "  警告: 密码未设置，使用默认值 'postgres'"
    echo "  提示: 如果PostgreSQL使用不同密码，请设置环境变量 DB_PASSWORD 或 POSTGRES_PASSWORD"
fi

# 执行传入的命令
exec "$@"

