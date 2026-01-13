#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docker容器资源监控脚本
实时监控Docker容器的CPU、内存、网络等资源使用情况

使用方法:
    # 监控所有相关容器
    python scripts/monitor_docker.py

    # 监控特定容器
    python scripts/monitor_docker.py --container geodata-postgres

    # 监控并保存到文件
    python scripts/monitor_docker.py --output monitor.log
"""

import argparse
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class DockerMonitor:
    """Docker容器监控类"""

    def __init__(self, container_names: Optional[List[str]] = None):
        """
        初始化监控

        Args:
            container_names: 要监控的容器名称列表，如果为None则监控所有相关容器
        """
        if container_names is None:
            # 默认监控的容器
            self.container_names = [
                "geodata-postgres",
                "geodata-mcp-server",
                "geodata-supergateway",
            ]
        else:
            self.container_names = container_names

    def get_container_list(self) -> List[str]:
        """获取实际运行的容器列表"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                running_containers = result.stdout.strip().split("\n")
                # 过滤出要监控的容器
                return [
                    name for name in self.container_names if name in running_containers
                ]
        except Exception as e:
            print(f"获取容器列表失败: {e}")
        return []

    def get_container_stats(self, container_name: str) -> Dict[str, Any]:
        """获取单个容器的统计信息"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    container_name,
                    "--no-stream",
                    "--format",
                    "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 6:
                    return {
                        "container": container_name,
                        "cpu_percent": parts[0].strip(),
                        "memory_usage": parts[1].strip(),
                        "memory_percent": parts[2].strip(),
                        "network_io": parts[3].strip(),
                        "block_io": parts[4].strip(),
                        "pids": parts[5].strip(),
                        "timestamp": datetime.now().isoformat(),
                    }
        except Exception as e:
            print(f"获取容器 {container_name} 统计信息失败: {e}")
        return {}

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有容器的统计信息"""
        containers = self.get_container_list()
        stats = {}
        for container in containers:
            container_stats = self.get_container_stats(container)
            if container_stats:
                stats[container] = container_stats
        return stats

    def print_stats(self, stats: Dict[str, Any]):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print(f"容器资源监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        if not stats:
            print("没有找到运行的容器")
            return

        for container_name, container_stats in stats.items():
            print(f"\n容器: {container_name}")
            print(f"  CPU使用率: {container_stats.get('cpu_percent', 'N/A')}")
            print(f"  内存使用: {container_stats.get('memory_usage', 'N/A')}")
            print(f"  内存百分比: {container_stats.get('memory_percent', 'N/A')}")
            print(f"  网络IO: {container_stats.get('network_io', 'N/A')}")
            print(f"  块IO: {container_stats.get('block_io', 'N/A')}")
            print(f"  进程数: {container_stats.get('pids', 'N/A')}")

        print("=" * 80)

    def monitor_loop(self, interval: int = 5, output_file: Optional[str] = None):
        """监控循环"""
        print(f"开始监控容器，刷新间隔: {interval}秒")
        print("按 Ctrl+C 停止监控")
        print()

        log_data = []

        try:
            while True:
                stats = self.get_all_stats()
                if stats:
                    self.print_stats(stats)

                    # 记录到日志
                    if output_file:
                        log_data.append(stats)
                        # 每10次记录保存一次
                        if len(log_data) >= 10:
                            self.save_log(log_data, output_file)
                            log_data = []

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            if output_file and log_data:
                self.save_log(log_data, output_file)
                print(f"监控数据已保存到: {output_file}")

    def save_log(self, log_data: List[Dict[str, Any]], output_file: str):
        """保存日志到文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果文件存在，读取现有数据
        existing_data = []
        if output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                pass

        # 合并数据
        all_data = existing_data + log_data

        # 保存
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

    def get_one_time_stats(self) -> Dict[str, Any]:
        """获取一次性的统计信息"""
        return self.get_all_stats()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Docker容器资源监控工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监控所有相关容器（实时刷新）
  python scripts/monitor_docker.py

  # 监控特定容器
  python scripts/monitor_docker.py --container geodata-postgres

  # 监控并保存日志
  python scripts/monitor_docker.py --output monitor.log

  # 只获取一次统计信息
  python scripts/monitor_docker.py --once
        """,
    )

    parser.add_argument(
        "--container",
        type=str,
        action="append",
        help="要监控的容器名称（可多次指定）",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="刷新间隔（秒，默认5）",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出日志文件路径",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只获取一次统计信息，不持续监控",
    )

    args = parser.parse_args()

    # 确定要监控的容器
    container_names = args.container if args.container else None

    # 创建监控实例
    monitor = DockerMonitor(container_names=container_names)

    if args.once:
        # 只获取一次统计
        stats = monitor.get_one_time_stats()
        monitor.print_stats(stats)
    else:
        # 持续监控
        monitor.monitor_loop(interval=args.interval, output_file=args.output)


if __name__ == "__main__":
    main()
