@echo off
REM Windows批处理脚本 - 启动 Supergateway
REM 用于在 Windows 上单独运行 Supergateway，连接到 Docker 中的 MCP 服务器

setlocal

REM 配置
set GATEWAY_PORT=8000
set MCP_CONTAINER=geodata-mcp-server

echo ==========================================
echo 启动 Supergateway
echo ==========================================
echo.
echo 配置:
echo   端口: %GATEWAY_PORT%
echo   MCP容器: %MCP_CONTAINER%
echo.

REM 检查 MCP 容器是否运行
docker ps | findstr "%MCP_CONTAINER%" >nul
if errorlevel 1 (
    echo 错误: MCP 容器 %MCP_CONTAINER% 未运行
    echo 请先启动 MCP 服务器: docker-compose up -d mcp-server
    pause
    exit /b 1
)

echo 启动 Supergateway...
echo 访问地址: http://localhost:%GATEWAY_PORT%
echo 按 Ctrl+C 停止
echo.

REM 运行 Supergateway
REM 注意: Windows上需要挂载Docker Desktop的Docker socket路径
docker run -it --rm ^
    --name geodata-supergateway ^
    --network geodata-network ^
    -p %GATEWAY_PORT%:%GATEWAY_PORT% ^
    -v //var/run/docker.sock:/var/run/docker.sock:ro ^
    supercorp/supergateway:latest ^
    --stdio ^
    docker exec -i %MCP_CONTAINER% python /app/mcp_server.py ^
    --port %GATEWAY_PORT% ^
    --mode sse

pause

