#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docker环境压测脚本
专门用于测试Docker部署的MCP服务

使用方法:
    # 基本压测
    python scripts/docker_load_test.py

    # 指定并发数和请求数
    python scripts/docker_load_test.py --concurrent 20 --requests 500

    # 持续压测（压测60秒）
    python scripts/docker_load_test.py --duration 60
"""

import asyncio
import argparse
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys
import subprocess
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_importer import DataImporter
from core.config_manager import ConfigManager


class DockerLoadTest:
    """Docker环境压测类"""

    def __init__(
        self,
        container_name: str = "geodata-postgres",
        database_config: Dict[str, Any] = None,
    ):
        """
        初始化压测

        Args:
            container_name: PostgreSQL容器名称
            database_config: 数据库配置（如果为None则使用默认配置）
        """
        self.container_name = container_name
        self.config_manager = ConfigManager()

        # 获取数据库配置
        if database_config:
            self.database_config = database_config
        else:
            self.database_config = self.config_manager.get_default_database_config()
            # 如果在本地运行，自动将 "postgres" 替换为 "localhost"
            if self.database_config.get("host") == "postgres":
                # 检查是否在Docker容器内
                if not self._is_in_docker():
                    print(
                        "检测到在本地运行，将数据库主机从 'postgres' 改为 'localhost'"
                    )
                    self.database_config["host"] = "localhost"

        self.data_importer = DataImporter()

    def _is_in_docker(self) -> bool:
        """检查是否在Docker容器内运行"""
        try:
            import os
            import platform

            # Windows系统上通常不在Docker容器内（除非使用WSL2）
            if platform.system() == "Windows":
                return False

            # 检查是否存在 /.dockerenv 文件
            if os.path.exists("/.dockerenv"):
                return True
            # 检查 cgroup
            if os.path.exists("/proc/self/cgroup"):
                with open("/proc/self/cgroup", "r") as f:
                    content = f.read()
                    if "docker" in content or "containerd" in content:
                        return True
        except Exception:
            pass
        return False

    def get_container_stats(self) -> Dict[str, Any]:
        """获取Docker容器资源使用情况"""
        try:
            # 获取容器统计信息
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    self.container_name,
                    "--no-stream",
                    "--format",
                    "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 4:
                    return {
                        "cpu_percent": parts[0].strip(),
                        "memory": parts[1].strip(),
                        "network": parts[2].strip(),
                        "block_io": parts[3].strip(),
                    }
        except Exception as e:
            print(f"获取容器统计信息失败: {e}")
        return {}

    async def run_load_test(
        self,
        test_func,
        concurrent: int,
        requests: int,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """运行压测"""
        print(f"开始压测: 并发数={concurrent}, 总请求数={requests}")
        print()

        durations = []
        errors = []
        start_time = time.time()

        # 记录初始资源使用
        initial_stats = self.get_container_stats()

        async def run_single_request():
            """运行单个请求"""
            try:
                result = await test_func(*args, **kwargs)
                return result
            except Exception as e:
                return {"success": False, "error": str(e), "duration": 0}

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent)

        async def run_with_semaphore():
            """使用信号量控制并发"""
            async with semaphore:
                return await run_single_request()

        # 执行所有请求
        tasks = [run_with_semaphore() for _ in range(requests)]
        results = await asyncio.gather(*tasks)

        # 统计结果
        for result in results:
            if result.get("success", False):
                durations.append(result.get("duration", 0))
            else:
                errors.append(result.get("error", "未知错误"))

        total_time = time.time() - start_time

        # 记录最终资源使用
        final_stats = self.get_container_stats()

        # 计算统计信息
        if durations:
            stats = {
                "total_requests": requests,
                "successful_requests": len(durations),
                "failed_requests": len(errors),
                "success_rate": len(durations) / requests * 100,
                "total_time": total_time,
                "requests_per_second": requests / total_time if total_time > 0 else 0,
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "p95_duration": self._percentile(durations, 95),
                "p99_duration": self._percentile(durations, 99),
                "initial_stats": initial_stats,
                "final_stats": final_stats,
                "errors": errors[:10] if errors else [],  # 只保留前10个错误
            }
        else:
            stats = {
                "total_requests": requests,
                "successful_requests": 0,
                "failed_requests": len(errors),
                "success_rate": 0,
                "total_time": total_time,
                "requests_per_second": 0,
                "initial_stats": initial_stats,
                "final_stats": final_stats,
                "errors": errors[:10] if errors else [],
            }

        return stats

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def run_duration_test(
        self,
        test_func,
        concurrent: int,
        duration_seconds: int,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """运行持续压测（指定持续时间）"""
        print(f"开始持续压测: 并发数={concurrent}, 持续时间={duration_seconds}秒")
        print()

        durations = []
        errors = []
        request_count = 0
        start_time = time.time()
        end_time = start_time + duration_seconds

        # 记录初始资源使用
        initial_stats = self.get_container_stats()

        async def run_single_request():
            """运行单个请求"""
            nonlocal request_count
            try:
                result = await test_func(*args, **kwargs)
                request_count += 1
                return result
            except Exception as e:
                request_count += 1
                return {"success": False, "error": str(e), "duration": 0}

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent)

        async def run_with_semaphore():
            """使用信号量控制并发"""
            async with semaphore:
                return await run_single_request()

        # 持续发送请求直到时间到
        while time.time() < end_time:
            # 创建一批并发请求
            tasks = [run_with_semaphore() for _ in range(concurrent)]
            results = await asyncio.gather(*tasks)

            # 统计结果
            for result in results:
                if result.get("success", False):
                    durations.append(result.get("duration", 0))
                else:
                    errors.append(result.get("error", "未知错误"))

            # 短暂休息，避免过度占用CPU
            await asyncio.sleep(0.1)

        total_time = time.time() - start_time

        # 记录最终资源使用
        final_stats = self.get_container_stats()

        # 计算统计信息
        if durations:
            stats = {
                "total_requests": request_count,
                "successful_requests": len(durations),
                "failed_requests": len(errors),
                "success_rate": (
                    len(durations) / request_count * 100 if request_count > 0 else 0
                ),
                "total_time": total_time,
                "requests_per_second": (
                    request_count / total_time if total_time > 0 else 0
                ),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "p95_duration": self._percentile(durations, 95),
                "p99_duration": self._percentile(durations, 99),
                "initial_stats": initial_stats,
                "final_stats": final_stats,
                "errors": errors[:10] if errors else [],
            }
        else:
            stats = {
                "total_requests": request_count,
                "successful_requests": 0,
                "failed_requests": len(errors),
                "success_rate": 0,
                "total_time": total_time,
                "requests_per_second": 0,
                "initial_stats": initial_stats,
                "final_stats": final_stats,
                "errors": errors[:10] if errors else [],
            }

        return stats

    def print_stats(self, stats: Dict[str, Any], test_name: str = "压测"):
        """打印统计信息"""
        print("=" * 80)
        print(f"{test_name}结果")
        print("=" * 80)
        print(f"总请求数: {stats['total_requests']}")
        print(f"成功请求: {stats['successful_requests']}")
        print(f"失败请求: {stats['failed_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"总耗时: {stats['total_time']:.2f}秒")
        print(f"QPS (每秒请求数): {stats['requests_per_second']:.2f}")

        if "min_duration" in stats:
            print()
            print("响应时间统计:")
            print(f"  最小响应时间: {stats['min_duration']:.3f}秒")
            print(f"  最大响应时间: {stats['max_duration']:.3f}秒")
            print(f"  平均响应时间: {stats['avg_duration']:.3f}秒")
            print(f"  中位数响应时间: {stats['median_duration']:.3f}秒")
            print(f"  P95响应时间: {stats['p95_duration']:.3f}秒")
            print(f"  P99响应时间: {stats['p99_duration']:.3f}秒")

        if "initial_stats" in stats and stats["initial_stats"]:
            print()
            print("容器资源使用 (初始):")
            for key, value in stats["initial_stats"].items():
                print(f"  {key}: {value}")

        if "final_stats" in stats and stats["final_stats"]:
            print()
            print("容器资源使用 (最终):")
            for key, value in stats["final_stats"].items():
                print(f"  {key}: {value}")

        if stats.get("errors"):
            print()
            print(f"错误示例 (前{len(stats['errors'])}个):")
            for i, error in enumerate(stats["errors"][:5], 1):
                print(f"  {i}. {error}")

        print("=" * 80)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Docker环境MCP服务压测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本压测（10并发，100请求）
  python scripts/docker_load_test.py

  # 高并发压测（20并发，500请求）
  python scripts/docker_load_test.py --concurrent 20 --requests 500

  # 持续压测（10并发，持续60秒）
  python scripts/docker_load_test.py --concurrent 10 --duration 60

  # 测试特定工具
  python scripts/docker_load_test.py --tool query_data --concurrent 5 --requests 100
        """,
    )

    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="并发数（默认10）",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="总请求数（默认100，与--duration互斥）",
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="持续压测时间（秒），如果指定则忽略--requests参数",
    )
    parser.add_argument(
        "--tool",
        type=str,
        choices=["list_tile_codes", "list_tables", "query_data", "execute_sql"],
        default="query_data",
        help="测试工具（默认query_data）",
    )
    parser.add_argument(
        "--container",
        type=str,
        default="geodata-postgres",
        help="PostgreSQL容器名称（默认geodata-postgres）",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="数据库主机（覆盖配置文件，默认自动检测）",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="数据库端口（覆盖配置文件）",
    )

    args = parser.parse_args()

    # 构建数据库配置
    database_config = None
    if args.host or args.port:
        config_manager = ConfigManager()
        database_config = config_manager.get_default_database_config()
        if args.host:
            database_config["host"] = args.host
        if args.port:
            database_config["port"] = args.port

    # 创建压测实例
    tester = DockerLoadTest(
        container_name=args.container, database_config=database_config
    )

    # 打印数据库连接信息
    print("数据库连接配置:")
    print(f"  主机: {tester.database_config.get('host', 'N/A')}")
    print(f"  端口: {tester.database_config.get('port', 'N/A')}")
    print(f"  数据库: {tester.database_config.get('database', 'N/A')}")
    print()

    # 定义测试函数
    async def test_list_tile_codes():
        start_time = time.time()
        try:
            await tester.data_importer.list_tile_codes(
                database_config=tester.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "error": str(e), "duration": duration}

    async def test_list_tables():
        start_time = time.time()
        try:
            await tester.data_importer.list_tables(
                database_config=tester.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "error": str(e), "duration": duration}

    async def test_query_data():
        start_time = time.time()
        try:
            result = await tester.data_importer.query_data(
                table_name="boua",
                limit=100,
                database_config=tester.database_config,
            )
            duration = time.time() - start_time
            return {
                "success": True,
                "duration": result.get("query_time_seconds", duration),
            }
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "error": str(e), "duration": duration}

    async def test_execute_sql():
        start_time = time.time()
        try:
            sql = "SELECT COUNT(*) as count FROM boua LIMIT 1"
            await tester.data_importer.execute_sql(
                sql=sql, database_config=tester.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "error": str(e), "duration": duration}

    # 选择测试函数
    test_func_map = {
        "list_tile_codes": test_list_tile_codes,
        "list_tables": test_list_tables,
        "query_data": test_query_data,
        "execute_sql": test_execute_sql,
    }

    test_func = test_func_map.get(args.tool, test_query_data)

    # 运行压测
    try:
        if args.duration:
            stats = await tester.run_duration_test(
                test_func, args.concurrent, args.duration
            )
        else:
            stats = await tester.run_load_test(
                test_func, args.concurrent, args.requests
            )

        # 打印结果
        tester.print_stats(stats, f"{args.tool} 压测")
    except KeyboardInterrupt:
        print("\n\n压测被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n压测过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # 保存结果到JSON文件
    output_file = Path(
        f"load_test_{args.tool}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n详细结果已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
