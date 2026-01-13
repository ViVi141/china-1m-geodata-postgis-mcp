#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速性能测试脚本
一键运行所有基本性能测试，适合快速验证服务性能

使用方法:
    python scripts/quick_performance_test.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.performance_test import PerformanceTest


async def main():
    """主函数"""
    print("=" * 80)
    print("快速性能测试")
    print("=" * 80)
    print()
    print("本脚本将运行所有基本性能测试，验证MCP服务性能")
    print()

    # 创建测试实例
    tester = PerformanceTest()

    # 运行基本测试
    try:
        basic_results = await tester.run_basic_tests()

        # 打印总结
        print("=" * 80)
        print("测试总结")
        print("=" * 80)
        print()

        success_count = 0
        total_count = len(basic_results)

        for test_name, result in basic_results.items():
            if result.get("success"):
                success_count += 1
                status = "✓"
                duration = result.get("duration", 0)
                print(f"{status} {test_name:30s} - {duration:.3f}秒")
            else:
                status = "✗"
                error = result.get("error", "未知错误")
                print(f"{status} {test_name:30s} - 失败: {error}")

        print()
        print(f"总计: {success_count}/{total_count} 测试通过")

        if success_count == total_count:
            print("✓ 所有测试通过！")
        else:
            print(f"✗ {total_count - success_count} 个测试失败")

        print("=" * 80)

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
