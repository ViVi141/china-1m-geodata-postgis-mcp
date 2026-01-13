#!/bin/bash
# 性能测试脚本（Linux/macOS）
# 用于快速运行性能测试

echo "========================================"
echo "MCP服务性能测试工具"
echo "========================================"
echo ""

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "当前目录: $(pwd)"
echo ""

# 显示菜单
echo "请选择测试类型:"
echo "1. 基本性能测试"
echo "2. 并发压测 (10并发, 100请求)"
echo "3. 高并发压测 (20并发, 500请求)"
echo "4. 持续压测 (10并发, 60秒)"
echo "5. Docker资源监控"
echo "6. 自定义测试"
echo "0. 退出"
echo ""

read -p "请输入选项 (0-6): " choice

case $choice in
    0)
        exit 0
        ;;
    1)
        echo ""
        echo "运行基本性能测试..."
        python3 scripts/performance_test.py
        ;;
    2)
        echo ""
        echo "运行并发压测 (10并发, 100请求)..."
        python3 scripts/docker_load_test.py --concurrent 10 --requests 100
        ;;
    3)
        echo ""
        echo "运行高并发压测 (20并发, 500请求)..."
        python3 scripts/docker_load_test.py --concurrent 20 --requests 500
        ;;
    4)
        echo ""
        echo "运行持续压测 (10并发, 60秒)..."
        python3 scripts/docker_load_test.py --concurrent 10 --duration 60
        ;;
    5)
        echo ""
        echo "启动Docker资源监控..."
        python3 scripts/monitor_docker.py
        ;;
    6)
        echo ""
        echo "自定义测试参数:"
        read -p "并发数 (默认10): " concurrent
        read -p "请求数 (默认100): " requests
        read -p "测试工具 (list_tile_codes/list_tables/query_data/execute_sql, 默认query_data): " tool
        
        concurrent=${concurrent:-10}
        requests=${requests:-100}
        tool=${tool:-query_data}
        
        echo ""
        echo "运行自定义测试: 并发=$concurrent, 请求=$requests, 工具=$tool"
        python3 scripts/docker_load_test.py --concurrent $concurrent --requests $requests --tool $tool
        ;;
    *)
        echo "无效选项"
        ;;
esac

echo ""
echo "测试完成"
