#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能测试和压测脚本
用于测试Docker部署的MCP服务性能

使用方法:
    # 基本性能测试
    python scripts/performance_test.py

    # 并发压测（10个并发，100个请求）
    python scripts/performance_test.py --concurrent 10 --requests 100

    # 测试特定工具
    python scripts/performance_test.py --tool query_data

    # 生成HTML报告
    python scripts/performance_test.py --report html
"""

import asyncio
import argparse
import json
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_importer import DataImporter
from core.config_manager import ConfigManager


class PerformanceTest:
    """性能测试类"""

    def __init__(self, database_config: Optional[Dict[str, Any]] = None):
        """
        初始化性能测试

        Args:
            database_config: 数据库配置，如果为None则使用默认配置
        """
        self.config_manager = ConfigManager()
        if database_config:
            self.database_config = database_config
        else:
            self.database_config = self.config_manager.get_default_database_config()
            # 如果在本地运行，自动将 "postgres" 替换为 "localhost"
            if self.database_config.get("host") == "postgres":
                if not self._is_in_docker():
                    print(
                        "检测到在本地运行，将数据库主机从 'postgres' 改为 'localhost'"
                    )
                    self.database_config["host"] = "localhost"

        self.data_importer = DataImporter()
        self.results: Dict[str, List[float]] = {}
        self.errors: Dict[str, int] = {}

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

    async def test_list_tile_codes(self) -> Dict[str, Any]:
        """测试 list_tile_codes 工具"""
        start_time = time.time()
        try:
            result = await self.data_importer.list_tile_codes(
                database_config=self.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration, "result": result}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "duration": duration, "error": str(e)}

    async def test_list_tables(self) -> Dict[str, Any]:
        """测试 list_tables 工具"""
        start_time = time.time()
        try:
            result = await self.data_importer.list_tables(
                database_config=self.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration, "result": result}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "duration": duration, "error": str(e)}

    async def test_verify_import(
        self, table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """测试 verify_import 工具"""
        start_time = time.time()
        try:
            result = await self.data_importer.verify_data(
                table_name=table_name, database_config=self.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration, "result": result}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "duration": duration, "error": str(e)}

    async def test_query_data(
        self, table_name: str = "boua", bbox: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """测试 query_data 工具"""
        start_time = time.time()
        try:
            spatial_filter = None
            if bbox:
                spatial_filter = {"bbox": bbox}

            result = await self.data_importer.query_data(
                table_name=table_name,
                spatial_filter=spatial_filter,
                limit=100,
                database_config=self.database_config,
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration, "result": result}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "duration": duration, "error": str(e)}

    async def test_execute_sql(self, sql: str) -> Dict[str, Any]:
        """测试 execute_sql 工具"""
        start_time = time.time()
        try:
            result = await self.data_importer.execute_sql(
                sql=sql, database_config=self.database_config
            )
            duration = time.time() - start_time
            return {"success": True, "duration": duration, "result": result}
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "duration": duration, "error": str(e)}

    async def run_single_test(
        self, test_name: str, test_func, *args, **kwargs
    ) -> Dict[str, Any]:
        """运行单个测试"""
        result = await test_func(*args, **kwargs)
        if test_name not in self.results:
            self.results[test_name] = []
        if result["success"]:
            self.results[test_name].append(result["duration"])
        else:
            if test_name not in self.errors:
                self.errors[test_name] = 0
            self.errors[test_name] += 1
        return result

    async def run_basic_tests(self) -> Dict[str, Any]:
        """运行基本性能测试"""
        print("=" * 80)
        print("开始基本性能测试")
        print("=" * 80)
        print()

        test_results = {}

        # 测试1: list_tile_codes
        print("[测试1] list_tile_codes - 列出图幅代码")
        result = await self.run_single_test(
            "list_tile_codes", self.test_list_tile_codes
        )
        test_results["list_tile_codes"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
            if "result" in result and "tile_codes" in result["result"]:
                tile_count = len(result["result"]["tile_codes"])
                print(f"  ✓ 图幅数量: {tile_count}")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        # 测试2: list_tables
        print("[测试2] list_tables - 列出数据表")
        result = await self.run_single_test("list_tables", self.test_list_tables)
        test_results["list_tables"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
            if "result" in result and "tables" in result["result"]:
                table_count = len(result["result"]["tables"])
                print(f"  ✓ 表数量: {table_count}")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        # 测试3: verify_import (所有表)
        print("[测试3] verify_import - 验证数据（所有表）")
        result = await self.run_single_test("verify_import", self.test_verify_import)
        test_results["verify_import"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        # 测试4: query_data (简单查询)
        print("[测试4] query_data - 空间数据查询（boua表，前100条）")
        result = await self.run_single_test("query_data", self.test_query_data, "boua")
        test_results["query_data"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
            if "result" in result and "count" in result["result"]:
                record_count = result["result"]["count"]
                print(f"  ✓ 返回记录数: {record_count}")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        # 测试5: query_data (空间过滤)
        print("[测试5] query_data - 空间过滤查询（bbox: [110, 20, 120, 30]）")
        bbox = [110, 20, 120, 30]
        result = await self.run_single_test(
            "query_data_bbox", self.test_query_data, "boua", bbox
        )
        test_results["query_data_bbox"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
            if "result" in result and "count" in result["result"]:
                record_count = result["result"]["count"]
                print(f"  ✓ 返回记录数: {record_count}")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        # 测试6: execute_sql (简单SQL)
        print("[测试6] execute_sql - 简单SQL查询（统计记录数）")
        sql = "SELECT COUNT(*) as count FROM boua LIMIT 1"
        result = await self.run_single_test("execute_sql", self.test_execute_sql, sql)
        test_results["execute_sql"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        # 测试7: execute_sql (复杂空间分析)
        print("[测试7] execute_sql - 复杂空间分析（计算面积）")
        sql = """
        SELECT 
            tile_code,
            COUNT(*) as record_count,
            SUM(ST_Area(geom::geography)/1000000) as total_area_km2
        FROM boua
        WHERE tile_code IN ('F49', 'F50')
        GROUP BY tile_code
        LIMIT 10
        """
        result = await self.run_single_test(
            "execute_sql_complex", self.test_execute_sql, sql
        )
        test_results["execute_sql_complex"] = result
        if result["success"]:
            print(f"  ✓ 成功 - 耗时: {result['duration']:.3f}秒")
        else:
            print(f"  ✗ 失败 - {result.get('error', '未知错误')}")
        print()

        return test_results

    async def run_concurrent_test(
        self, test_name: str, test_func, concurrent: int, requests: int, *args, **kwargs
    ) -> Dict[str, Any]:
        """运行并发压测"""
        print(f"开始并发压测: {test_name}")
        print(f"  并发数: {concurrent}, 总请求数: {requests}")
        print()

        durations = []
        errors = 0
        start_time = time.time()

        async def run_single_request():
            """运行单个请求"""
            try:
                result = await test_func(*args, **kwargs)
                return result
            except Exception as e:
                return {"success": False, "error": str(e)}

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
                errors += 1

        total_time = time.time() - start_time

        # 计算统计信息
        if durations:
            stats = {
                "total_requests": requests,
                "successful_requests": len(durations),
                "failed_requests": errors,
                "success_rate": len(durations) / requests * 100,
                "total_time": total_time,
                "requests_per_second": requests / total_time if total_time > 0 else 0,
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "p95_duration": self._percentile(durations, 95),
                "p99_duration": self._percentile(durations, 99),
            }
        else:
            stats = {
                "total_requests": requests,
                "successful_requests": 0,
                "failed_requests": errors,
                "success_rate": 0,
                "total_time": total_time,
                "requests_per_second": 0,
            }

        return stats

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def generate_report(
        self, test_results: Dict[str, Any], output_format: str = "text"
    ) -> str:
        """生成测试报告"""
        if output_format == "json":
            return json.dumps(test_results, ensure_ascii=False, indent=2)
        elif output_format == "html":
            return self._generate_html_report(test_results)
        else:
            return self._generate_text_report(test_results)

    def _generate_text_report(self, test_results: Dict[str, Any]) -> str:
        """生成文本报告"""
        report = []
        report.append("=" * 80)
        report.append("性能测试报告")
        report.append("=" * 80)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 基本测试结果
        if "basic_tests" in test_results:
            report.append("基本性能测试结果:")
            report.append("-" * 80)
            for test_name, result in test_results["basic_tests"].items():
                if result.get("success"):
                    report.append(
                        f"  {test_name:30s} - 耗时: {result['duration']:.3f}秒"
                    )
                else:
                    report.append(
                        f"  {test_name:30s} - 失败: {result.get('error', '未知错误')}"
                    )
            report.append("")

        # 并发测试结果
        if "concurrent_tests" in test_results:
            report.append("并发压测结果:")
            report.append("-" * 80)
            for test_name, stats in test_results["concurrent_tests"].items():
                report.append(f"\n{test_name}:")
                report.append(f"  总请求数: {stats['total_requests']}")
                report.append(f"  成功请求: {stats['successful_requests']}")
                report.append(f"  失败请求: {stats['failed_requests']}")
                report.append(f"  成功率: {stats['success_rate']:.2f}%")
                report.append(f"  总耗时: {stats['total_time']:.2f}秒")
                report.append(f"  QPS: {stats['requests_per_second']:.2f}")
                if "min_duration" in stats:
                    report.append(f"  最小响应时间: {stats['min_duration']:.3f}秒")
                    report.append(f"  最大响应时间: {stats['max_duration']:.3f}秒")
                    report.append(f"  平均响应时间: {stats['avg_duration']:.3f}秒")
                    report.append(f"  中位数响应时间: {stats['median_duration']:.3f}秒")
                    report.append(f"  P95响应时间: {stats['p95_duration']:.3f}秒")
                    report.append(f"  P99响应时间: {stats['p99_duration']:.3f}秒")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def _generate_html_report(self, test_results: Dict[str, Any]) -> str:
        """生成HTML报告"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append('<meta charset="UTF-8">')
        html.append("<title>性能测试报告</title>")
        html.append(
            """
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .success { color: green; }
                .error { color: red; }
            </style>
            """
        )
        html.append("</head>")
        html.append("<body>")
        html.append("<h1>性能测试报告</h1>")
        html.append(f"<p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        # 基本测试结果
        if "basic_tests" in test_results:
            html.append("<h2>基本性能测试结果</h2>")
            html.append("<table>")
            html.append("<tr><th>测试项</th><th>状态</th><th>耗时(秒)</th></tr>")
            for test_name, result in test_results["basic_tests"].items():
                status = "成功" if result.get("success") else "失败"
                status_class = "success" if result.get("success") else "error"
                duration = result.get("duration", 0)
                html.append(
                    f'<tr><td>{test_name}</td><td class="{status_class}">{status}</td><td>{duration:.3f}</td></tr>'
                )
            html.append("</table>")

        # 并发测试结果
        if "concurrent_tests" in test_results:
            html.append("<h2>并发压测结果</h2>")
            for test_name, stats in test_results["concurrent_tests"].items():
                html.append(f"<h3>{test_name}</h3>")
                html.append("<table>")
                html.append("<tr><th>指标</th><th>值</th></tr>")
                for key, value in stats.items():
                    if isinstance(value, float):
                        html.append(f"<tr><td>{key}</td><td>{value:.3f}</td></tr>")
                    else:
                        html.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
                html.append("</table>")

        html.append("</body>")
        html.append("</html>")
        return "\n".join(html)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="MCP服务性能测试和压测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本性能测试
  python scripts/performance_test.py

  # 并发压测（10个并发，100个请求）
  python scripts/performance_test.py --concurrent 10 --requests 100

  # 测试特定工具
  python scripts/performance_test.py --tool query_data --concurrent 5 --requests 50

  # 生成HTML报告
  python scripts/performance_test.py --report html --output report.html
        """,
    )

    parser.add_argument(
        "--concurrent",
        type=int,
        default=0,
        help="并发数（0表示只运行基本测试，不进行并发压测）",
    )
    parser.add_argument("--requests", type=int, default=100, help="总请求数（默认100）")
    parser.add_argument(
        "--tool",
        type=str,
        choices=["list_tile_codes", "list_tables", "query_data", "execute_sql"],
        help="测试特定工具（如果不指定则测试所有工具）",
    )
    parser.add_argument(
        "--report",
        type=str,
        choices=["text", "json", "html"],
        default="text",
        help="报告格式（默认text）",
    )
    parser.add_argument(
        "--output", type=str, help="输出文件路径（如果不指定则输出到控制台）"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="数据库主机（覆盖配置文件）",
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
        from core.config_manager import ConfigManager

        config_manager = ConfigManager()
        database_config = config_manager.get_default_database_config()
        if args.host:
            database_config["host"] = args.host
        if args.port:
            database_config["port"] = args.port

    # 创建测试实例
    tester = PerformanceTest(database_config=database_config)

    # 运行基本测试
    print("开始性能测试...")
    print()
    basic_results = await tester.run_basic_tests()

    test_results = {"basic_tests": basic_results}

    # 运行并发压测
    if args.concurrent > 0:
        print("=" * 80)
        print("开始并发压测")
        print("=" * 80)
        print()

        concurrent_results = {}

        # 确定要测试的工具
        tools_to_test = []
        if args.tool:
            tools_to_test = [args.tool]
        else:
            tools_to_test = [
                "list_tile_codes",
                "list_tables",
                "query_data",
                "execute_sql",
            ]

        # 测试每个工具
        for tool_name in tools_to_test:
            if tool_name == "list_tile_codes":
                stats = await tester.run_concurrent_test(
                    "list_tile_codes",
                    tester.test_list_tile_codes,
                    args.concurrent,
                    args.requests,
                )
                concurrent_results["list_tile_codes"] = stats
            elif tool_name == "list_tables":
                stats = await tester.run_concurrent_test(
                    "list_tables",
                    tester.test_list_tables,
                    args.concurrent,
                    args.requests,
                )
                concurrent_results["list_tables"] = stats
            elif tool_name == "query_data":
                stats = await tester.run_concurrent_test(
                    "query_data",
                    tester.test_query_data,
                    args.concurrent,
                    args.requests,
                    "boua",
                )
                concurrent_results["query_data"] = stats
            elif tool_name == "execute_sql":
                sql = "SELECT COUNT(*) as count FROM boua LIMIT 1"
                stats = await tester.run_concurrent_test(
                    "execute_sql",
                    tester.test_execute_sql,
                    args.concurrent,
                    args.requests,
                    sql,
                )
                concurrent_results["execute_sql"] = stats

            # 打印结果
            print(f"\n{tool_name} 压测结果:")
            print(f"  成功率: {stats['success_rate']:.2f}%")
            print(f"  QPS: {stats['requests_per_second']:.2f}")
            if "avg_duration" in stats:
                print(f"  平均响应时间: {stats['avg_duration']:.3f}秒")
                print(f"  P95响应时间: {stats['p95_duration']:.3f}秒")
            print()

        test_results["concurrent_tests"] = concurrent_results

    # 生成报告
    report = tester.generate_report(test_results, args.report)

    # 输出报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {output_path}")
    else:
        print()
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
