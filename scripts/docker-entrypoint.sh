#!/bin/bash
# Docker 容器入口脚本
# 自动生成数据库配置文件（如果不存在）

set -e

CONFIG_DIR="/app/config"
CONFIG_FILE="${CONFIG_DIR}/database.ini"

# 创建配置目录
mkdir -p "${CONFIG_DIR}"

# 在Docker容器中，总是从环境变量更新配置以确保一致性
# 这样可以避免挂载的配置文件（可能指向其他数据库）覆盖容器环境变量的问题
NEED_UPDATE=false

# 检查是否在Docker环境中（通过检查环境变量或容器标识）
# 如果环境变量已设置，或者配置文件不存在，或者host不是postgres，都需要更新
if [ ! -f "${CONFIG_FILE}" ]; then
    NEED_UPDATE=true
    echo "配置文件不存在，将生成..."
elif [ -n "${DB_HOST}" ] || [ -n "${DB_PASSWORD}" ] || [ -n "${DB_NAME}" ] || [ -n "${DB_USER}" ]; then
    # 环境变量已设置，强制使用环境变量（避免挂载的配置文件覆盖）
    NEED_UPDATE=true
    echo "检测到环境变量已设置，将使用环境变量更新配置文件..."
    
    # 读取当前配置用于对比（仅用于日志）
    if [ -f "${CONFIG_FILE}" ]; then
        CURRENT_HOST=$(grep "^host" "${CONFIG_FILE}" 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo "")
        CURRENT_PASSWORD=$(grep "^password" "${CONFIG_FILE}" 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo "")
        ENV_HOST="${DB_HOST:-postgres}"
        ENV_PASSWORD="${DB_PASSWORD:-postgres}"
        
        if [ "${CURRENT_HOST}" != "${ENV_HOST}" ] || [ "${CURRENT_PASSWORD}" != "${ENV_PASSWORD}" ]; then
            echo "  当前配置: host=${CURRENT_HOST}, password=${CURRENT_PASSWORD:0:3}***"
            echo "  环境变量: host=${ENV_HOST}, password=${ENV_PASSWORD:0:3}***"
            echo "  将更新配置文件以匹配环境变量"
        fi
    fi
elif grep -q "host = localhost" "${CONFIG_FILE}" 2>/dev/null; then
    # 配置文件使用localhost，在Docker环境中应该使用服务名
    NEED_UPDATE=true
    echo "检测到配置文件使用localhost，将更新为容器环境配置（postgres）..."
else
    # 检查配置文件中的host是否为postgres（Docker服务名）
    CURRENT_HOST=$(grep "^host" "${CONFIG_FILE}" 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo "")
    if [ "${CURRENT_HOST}" != "postgres" ] && [ -n "${CURRENT_HOST}" ]; then
        # 如果host不是postgres，可能是挂载的本地配置文件，需要更新
        NEED_UPDATE=true
        echo "检测到配置文件host为 '${CURRENT_HOST}'，在Docker环境中应使用 'postgres'，将更新..."
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
        echo "验证: host=$(grep '^host' "${CONFIG_FILE}" | cut -d'=' -f2 | tr -d ' '), password=${PASSWORD_PREVIEW} (长度: ${PASSWORD_LEN})"
    fi
fi

# 显示配置信息（显示密码长度用于调试）
echo "数据库配置:"
echo "  主机: ${DB_HOST:-postgres}"
echo "  端口: ${DB_PORT:-5432}"
echo "  数据库: ${DB_NAME:-gis_data}"
echo "  用户: ${DB_USER:-postgres}"
if [ -n "${DB_PASSWORD}" ]; then
    PASSWORD_LEN=${#DB_PASSWORD}
    PASSWORD_PREVIEW="${DB_PASSWORD:0:3}***"
    echo "  密码: ${PASSWORD_PREVIEW} (长度: ${PASSWORD_LEN})"
else
    echo "  密码: 未设置，将使用默认值 'postgres'"
    echo "  警告: 如果PostgreSQL使用不同密码，请设置环境变量 DB_PASSWORD 或 POSTGRES_PASSWORD"
fi

# 执行传入的命令
exec "$@"

