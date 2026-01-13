@echo off
REM 性能测试批处理脚本（Windows）
REM 用于快速运行性能测试

echo ========================================
echo MCP服务性能测试工具
echo ========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 切换到项目根目录
cd /d "%~dp0\.."

echo 当前目录: %CD%
echo.

REM 显示菜单
echo 请选择测试类型:
echo 1. 基本性能测试
echo 2. 并发压测 (10并发, 100请求)
echo 3. 高并发压测 (20并发, 500请求)
echo 4. 持续压测 (10并发, 60秒)
echo 5. Docker资源监控
echo 6. 自定义测试
echo 0. 退出
echo.

set /p choice=请输入选项 (0-6): 

if "%choice%"=="0" exit /b 0
if "%choice%"=="1" (
    echo.
    echo 运行基本性能测试...
    python scripts/performance_test.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 运行并发压测 (10并发, 100请求)...
    python scripts/docker_load_test.py --concurrent 10 --requests 100
    goto end
)

if "%choice%"=="3" (
    echo.
    echo 运行高并发压测 (20并发, 500请求)...
    python scripts/docker_load_test.py --concurrent 20 --requests 500
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 运行持续压测 (10并发, 60秒)...
    python scripts/docker_load_test.py --concurrent 10 --duration 60
    goto end
)

if "%choice%"=="5" (
    echo.
    echo 启动Docker资源监控...
    python scripts/monitor_docker.py
    goto end
)

if "%choice%"=="6" (
    echo.
    echo 自定义测试参数:
    set /p concurrent=并发数 (默认10): 
    set /p requests=请求数 (默认100): 
    set /p tool=测试工具 (list_tile_codes/list_tables/query_data/execute_sql, 默认query_data): 
    
    if "%concurrent%"=="" set concurrent=10
    if "%requests%"=="" set requests=100
    if "%tool%"=="" set tool=query_data
    
    echo.
    echo 运行自定义测试: 并发=%concurrent%, 请求=%requests%, 工具=%tool%
    python scripts/docker_load_test.py --concurrent %concurrent% --requests %requests% --tool %tool%
    goto end
)

echo 无效选项
goto end

:end
echo.
echo 测试完成
pause
