@echo off
REM Windows批处理脚本 - 在虚拟环境中启动MCP服务器

echo ========================================
echo 启动MCP服务器
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在
    echo 请先创建虚拟环境: python -m venv .venv
    pause
    exit /b 1
)

echo [1/2] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo [2/2] 启动MCP服务器...
echo.
echo 注意: MCP服务器通过stdio通信，可能没有输出
echo 按 Ctrl+C 停止服务器
echo.

python mcp_server.py

pause

