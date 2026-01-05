#!/bin/bash
# Linux/Mac shell脚本 - 在虚拟环境中启动MCP服务器

echo "========================================"
echo "启动MCP服务器"
echo "========================================"
echo ""

# 检查虚拟环境是否存在
if [ ! -f ".venv/bin/activate" ]; then
    echo "错误: 虚拟环境不存在"
    echo "请先创建虚拟环境: python -m venv .venv"
    exit 1
fi

echo "[1/2] 激活虚拟环境..."
source .venv/bin/activate

echo "[2/2] 启动MCP服务器..."
echo ""
echo "注意: MCP服务器通过stdio通信，可能没有输出"
echo "按 Ctrl+C 停止服务器"
echo ""

python mcp_server.py

