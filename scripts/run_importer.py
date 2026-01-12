#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨平台数据导入脚本
自动检测平台并使用正确的 docker-compose 命令语法
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


def detect_platform():
    """检测当前平台"""
    system = platform.system().lower()
    shell = os.environ.get("SHELL", "").lower()

    if system == "windows":
        # 检查是否在 PowerShell 中
        if "powershell" in os.environ.get("PSModulePath", "").lower():
            return "powershell"
        # 检查是否在 CMD 中
        elif "COMSPEC" in os.environ:
            return "cmd"
        else:
            return "windows"
    elif system == "linux" or system == "darwin":
        if "bash" in shell or "zsh" in shell or "sh" in shell:
            return "bash"
        else:
            return "unix"
    else:
        return "unknown"


def build_docker_command(args):
    """构建 docker-compose 命令"""
    base_cmd = [
        "docker-compose",
        "--profile",
        "importer",
        "run",
        "--rm",
        "data-importer",
    ]

    # 如果提供了额外参数，添加到命令中
    if args:
        base_cmd.extend(args)

    return base_cmd


def run_command(cmd):
    """执行命令"""
    print(f"执行命令: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"错误: 命令执行失败，返回码: {e.returncode}")
        return False
    except FileNotFoundError:
        print("错误: 未找到 docker-compose 命令")
        print("请确保已安装 Docker 和 Docker Compose")
        return False


def main():
    """主函数"""
    # 检测平台
    detected_platform = detect_platform()

    print("=" * 60)
    print("跨平台数据导入工具")
    print("=" * 60)
    print(f"检测到平台: {detected_platform}")
    print(f"操作系统: {platform.system()}")
    print("=" * 60)
    print()

    # 获取命令行参数（排除脚本名）
    args = sys.argv[1:]

    # 如果没有参数，显示帮助
    if not args or "--help" in args or "-h" in args:
        print("使用方法:")
        print(f"  python {Path(__file__).name} [命令参数...]")
        print()
        print("示例:")
        print("  # 查看帮助")
        print(f"  python {Path(__file__).name} python main.py --help")
        print()
        print("  # 重置数据库并导入数据")
        print(
            f"  python {Path(__file__).name} python main.py --reset-and-import --gdb-dir /app/data"
        )
        print()
        print("  # 只导入数据（不重置）")
        print(f"  python {Path(__file__).name} python scripts/import_all_tiles.py")
        print()
        print("  # 验证数据")
        print(f"  python {Path(__file__).name} python scripts/verify_data.py")
        print()
        print("注意:")
        print("  - 容器内的路径使用 /app/data 作为 GDB 文件目录")
        print("  - 如果 GDB 文件在项目根目录，使用 --gdb-dir /app/data")
        print("  - 脚本会自动处理平台差异，无需担心续行符问题")
        sys.exit(0)

    # 构建并执行命令
    cmd = build_docker_command(args)
    success = run_command(cmd)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
