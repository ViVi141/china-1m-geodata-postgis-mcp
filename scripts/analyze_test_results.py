#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试结果分析工具
用于分析和对比多个压测结果

使用方法:
    # 分析单个结果文件
    python scripts/analyze_test_results.py load_test_query_data_20260113_235503.json

    # 分析多个结果文件并对比
    python scripts/analyze_test_results.py *.json

    # 生成对比报告
    python scripts/analyze_test_results.py *.json --report html --output comparison.html
"""

import argparse
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import sys


class TestResultAnalyzer:
    """测试结果分析器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def load_result(self, file_path: str) -> Dict[str, Any]:
        """加载单个测试结果文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 添加文件名和时间戳
            data["file_name"] = Path(file_path).name
            data["file_path"] = str(Path(file_path).absolute())
            if "timestamp" not in data:
                # 尝试从文件名提取时间戳
                try:
                    parts = Path(file_path).stem.split("_")
                    if len(parts) >= 3:
                        date_str = parts[-2]
                        time_str = parts[-1]
                        data["timestamp"] = f"{date_str}_{time_str}"
                except Exception:
                    data["timestamp"] = "unknown"
            return data

    def load_results(self, file_paths: List[str]):
        """加载多个测试结果文件"""
        for file_path in file_paths:
            try:
                result = self.load_result(file_path)
                self.results.append(result)
            except Exception as e:
                print(f"警告: 无法加载文件 {file_path}: {e}")

    def analyze_single(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个测试结果"""
        analysis = {
            "file_name": result.get("file_name", "unknown"),
            "timestamp": result.get("timestamp", "unknown"),
            "test_type": (
                "持续压测"
                if "total_time" in result and result.get("total_time", 0) > 30
                else "单次压测"
            ),
        }

        # 基本统计
        analysis["total_requests"] = result.get("total_requests", 0)
        analysis["successful_requests"] = result.get("successful_requests", 0)
        analysis["failed_requests"] = result.get("failed_requests", 0)
        analysis["success_rate"] = result.get("success_rate", 0)
        analysis["qps"] = result.get("requests_per_second", 0)
        analysis["total_time"] = result.get("total_time", 0)

        # 响应时间统计
        if "min_duration" in result:
            analysis["response_time"] = {
                "min": result.get("min_duration", 0),
                "max": result.get("max_duration", 0),
                "avg": result.get("avg_duration", 0),
                "median": result.get("median_duration", 0),
                "p95": result.get("p95_duration", 0),
                "p99": result.get("p99_duration", 0),
            }

        # 资源使用
        if "initial_stats" in result and result["initial_stats"]:
            analysis["initial_stats"] = result["initial_stats"]
        if "final_stats" in result and result["final_stats"]:
            analysis["final_stats"] = result["final_stats"]

        # 性能评级
        analysis["performance_rating"] = self._rate_performance(analysis)

        return analysis

    def _rate_performance(self, analysis: Dict[str, Any]) -> str:
        """评估性能等级"""
        qps = analysis.get("qps", 0)
        success_rate = analysis.get("success_rate", 0)
        avg_time = analysis.get("response_time", {}).get("avg", 0)

        if success_rate < 95:
            return "差"
        elif qps < 10 or avg_time > 1.0:
            return "一般"
        elif qps < 30 or avg_time > 0.1:
            return "良好"
        elif qps < 50 or avg_time > 0.05:
            return "优秀"
        else:
            return "卓越"

    def compare_results(self) -> Dict[str, Any]:
        """对比多个测试结果"""
        if len(self.results) < 2:
            return {"error": "需要至少2个结果文件才能进行对比"}

        analyses = [self.analyze_single(result) for result in self.results]

        comparison = {
            "total_tests": len(analyses),
            "tests": analyses,
            "summary": {
                "avg_qps": statistics.mean([a["qps"] for a in analyses]),
                "max_qps": max([a["qps"] for a in analyses]),
                "min_qps": min([a["qps"] for a in analyses]),
                "avg_success_rate": statistics.mean(
                    [a["success_rate"] for a in analyses]
                ),
                "avg_response_time": statistics.mean(
                    [a.get("response_time", {}).get("avg", 0) for a in analyses]
                ),
            },
        }

        return comparison

    def print_analysis(self, analysis: Dict[str, Any]):
        """打印单个分析结果"""
        print("=" * 80)
        print(f"测试结果分析: {analysis['file_name']}")
        print("=" * 80)
        print(f"测试类型: {analysis['test_type']}")
        print(f"时间戳: {analysis['timestamp']}")
        print()
        print("基本统计:")
        print(f"  总请求数: {analysis['total_requests']}")
        print(f"  成功请求: {analysis['successful_requests']}")
        print(f"  失败请求: {analysis['failed_requests']}")
        print(f"  成功率: {analysis['success_rate']:.2f}%")
        print(f"  QPS: {analysis['qps']:.2f}")
        print(f"  总耗时: {analysis['total_time']:.2f}秒")
        print()

        if "response_time" in analysis:
            rt = analysis["response_time"]
            print("响应时间统计:")
            print(f"  最小: {rt['min']:.3f}秒")
            print(f"  最大: {rt['max']:.3f}秒")
            print(f"  平均: {rt['avg']:.3f}秒")
            print(f"  中位数: {rt['median']:.3f}秒")
            print(f"  P95: {rt['p95']:.3f}秒")
            print(f"  P99: {rt['p99']:.3f}秒")
            print()

        print(f"性能评级: {analysis['performance_rating']}")
        print("=" * 80)

    def print_comparison(self, comparison: Dict[str, Any]):
        """打印对比结果"""
        if "error" in comparison:
            print(f"错误: {comparison['error']}")
            return

        print("=" * 80)
        print("测试结果对比")
        print("=" * 80)
        print()

        # 打印每个测试的摘要
        for i, test in enumerate(comparison["tests"], 1):
            print(f"测试 {i}: {test['file_name']}")
            print(f"  类型: {test['test_type']}")
            print(f"  QPS: {test['qps']:.2f}")
            print(f"  成功率: {test['success_rate']:.2f}%")
            if "response_time" in test:
                print(f"  平均响应时间: {test['response_time']['avg']:.3f}秒")
            print(f"  性能评级: {test['performance_rating']}")
            print()

        # 打印汇总统计
        summary = comparison["summary"]
        print("汇总统计:")
        print(f"  平均QPS: {summary['avg_qps']:.2f}")
        print(f"  最高QPS: {summary['max_qps']:.2f}")
        print(f"  最低QPS: {summary['min_qps']:.2f}")
        print(f"  平均成功率: {summary['avg_success_rate']:.2f}%")
        print(f"  平均响应时间: {summary['avg_response_time']:.3f}秒")
        print("=" * 80)

    def generate_html_report(self, comparison: Dict[str, Any], output_file: str):
        """生成HTML报告"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append('<meta charset="UTF-8">')
        html.append("<title>测试结果对比报告</title>")
        html.append(
            """
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                h2 { color: #555; margin-top: 30px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .excellent { color: #4CAF50; font-weight: bold; }
                .good { color: #2196F3; font-weight: bold; }
                .fair { color: #FF9800; font-weight: bold; }
                .poor { color: #f44336; font-weight: bold; }
                .summary { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
            """
        )
        html.append("</head>")
        html.append("<body>")
        html.append('<div class="container">')
        html.append("<h1>测试结果对比报告</h1>")
        html.append(f"<p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        if "error" in comparison:
            html.append(f"<p style='color: red;'>{comparison['error']}</p>")
        else:
            # 汇总统计
            summary = comparison["summary"]
            html.append("<div class='summary'>")
            html.append("<h2>汇总统计</h2>")
            html.append("<table>")
            html.append("<tr><th>指标</th><th>值</th></tr>")
            html.append(
                f"<tr><td>测试数量</td><td>{comparison['total_tests']}</td></tr>"
            )
            html.append(f"<tr><td>平均QPS</td><td>{summary['avg_qps']:.2f}</td></tr>")
            html.append(f"<tr><td>最高QPS</td><td>{summary['max_qps']:.2f}</td></tr>")
            html.append(f"<tr><td>最低QPS</td><td>{summary['min_qps']:.2f}</td></tr>")
            html.append(
                f"<tr><td>平均成功率</td><td>{summary['avg_success_rate']:.2f}%</td></tr>"
            )
            html.append(
                f"<tr><td>平均响应时间</td><td>{summary['avg_response_time']:.3f}秒</td></tr>"
            )
            html.append("</table>")
            html.append("</div>")

            # 详细对比表
            html.append("<h2>详细对比</h2>")
            html.append("<table>")
            html.append(
                "<tr><th>测试文件</th><th>类型</th><th>QPS</th><th>成功率</th><th>平均响应时间</th><th>性能评级</th></tr>"
            )
            for test in comparison["tests"]:
                rating_class = {
                    "卓越": "excellent",
                    "优秀": "good",
                    "良好": "fair",
                    "一般": "fair",
                    "差": "poor",
                }.get(test["performance_rating"], "")
                rt_avg = test.get("response_time", {}).get("avg", 0)
                html.append(
                    f"<tr>"
                    f"<td>{test['file_name']}</td>"
                    f"<td>{test['test_type']}</td>"
                    f"<td>{test['qps']:.2f}</td>"
                    f"<td>{test['success_rate']:.2f}%</td>"
                    f"<td>{rt_avg:.3f}秒</td>"
                    f"<td class='{rating_class}'>{test['performance_rating']}</td>"
                    f"</tr>"
                )
            html.append("</table>")

        html.append("</div>")
        html.append("</body>")
        html.append("</html>")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))
        print(f"HTML报告已保存到: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="测试结果分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析单个结果文件
  python scripts/analyze_test_results.py load_test_query_data_20260113_235503.json

  # 分析多个结果文件并对比
  python scripts/analyze_test_results.py *.json

  # 生成HTML对比报告
  python scripts/analyze_test_results.py *.json --report html --output comparison.html
        """,
    )

    parser.add_argument("files", nargs="+", help="测试结果JSON文件（支持通配符）")
    parser.add_argument(
        "--report",
        type=str,
        choices=["text", "html"],
        default="text",
        help="报告格式（默认text）",
    )
    parser.add_argument("--output", type=str, help="输出文件路径（HTML格式时必需）")

    args = parser.parse_args()

    # 展开通配符
    import glob

    file_paths = []
    for pattern in args.files:
        file_paths.extend(glob.glob(pattern))

    if not file_paths:
        print("错误: 未找到任何结果文件")
        sys.exit(1)

    # 创建分析器
    analyzer = TestResultAnalyzer()
    analyzer.load_results(file_paths)

    if len(analyzer.results) == 1:
        # 单个结果分析
        analysis = analyzer.analyze_single(analyzer.results[0])
        analyzer.print_analysis(analysis)
    else:
        # 多个结果对比
        comparison = analyzer.compare_results()
        if args.report == "html":
            if not args.output:
                print("错误: 生成HTML报告需要指定 --output 参数")
                sys.exit(1)
            analyzer.generate_html_report(comparison, args.output)
        else:
            analyzer.print_comparison(comparison)


if __name__ == "__main__":
    main()
