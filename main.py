#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主脚本：一键重置数据库、分析导入数据、启动MCP服务
"""

import sys
import argparse
from pathlib import Path

# 使用正确的模块导入路径
# main.py 在项目根目录，scripts/ 是子目录
# 因此应该使用 scripts.reset_database 而不是直接导入 reset_database

from scripts.reset_database import reset_database
from scripts.setup_unified_database import (
    step1_parse_tile,
    step2_create_schema,
    step3_import_data
)


def reset_and_import(gdb_dir: str = ".", reference_tile: str = "F49", force: bool = False):
    """
    重置数据库并导入数据
    
    Args:
        gdb_dir: GDB文件目录
        reference_tile: 参考图幅代码（用于分析表结构）
        force: 是否强制重新创建表
    """
    print("=" * 80)
    print("一键重置数据库并导入数据")
    print("=" * 80)
    print()
    
    # 步骤1：重置数据库
    print("[步骤1/4] 重置数据库...")
    if not reset_database(confirm=False):
        print("错误: 重置数据库失败")
        return False
    print("✓ 数据库已重置\n")
    
    # 查找参考图幅的GDB文件
    gdb_path = Path(gdb_dir) / f"{reference_tile}.gdb"
    if not gdb_path.exists():
        print(f"错误: 找不到参考图幅GDB文件: {gdb_path}")
        return False
    
    # 步骤2：解析图幅结构
    print("[步骤2/4] 解析图幅结构...")
    try:
        analysis_file = step1_parse_tile(str(gdb_path), output_dir="analysis", reference_tile=reference_tile)
        print("✓ 图幅结构解析完成\n")
    except Exception as e:
        print(f"错误: 解析图幅结构失败: {e}")
        return False
    
    # 步骤3：创建表结构
    print("[步骤3/4] 创建数据库表结构...")
    try:
        if not step2_create_schema(analysis_file, srid=4326, force=force):
            print("错误: 创建表结构失败")
            return False
        print("✓ 数据库表结构创建完成\n")
    except Exception as e:
        print(f"错误: 创建表结构失败: {e}")
        return False
    
    # 步骤4：导入数据
    print("[步骤4/4] 导入所有图幅数据...")
    try:
        result = step3_import_data(gdb_dir=gdb_dir, srid=4326, batch_size=1000, skip_invalid=True)
        if result.get('failed', 0) > 0:
            print(f"警告: {result['failed']} 个GDB文件导入失败")
        if result.get('success', 0) == 0:
            print("错误: 没有成功导入任何数据")
            return False
        print(f"✓ 数据导入完成 (成功: {result.get('success', 0)} 个文件, 总记录数: {result.get('total_records', 0):,} 条)\n")
    except Exception as e:
        print(f"错误: 导入数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 80)
    print("所有步骤完成！")
    print("=" * 80)
    return True


def start_server():
    """启动MCP服务器"""
    print("=" * 80)
    print("启动MCP服务器")
    print("=" * 80)
    print()
    print("注意: MCP服务器通过stdio通信，可能没有输出")
    print("按 Ctrl+C 停止服务器")
    print()
    
    # 导入并运行MCP服务器
    import asyncio
    from mcp_server import main as mcp_main
    
    try:
        asyncio.run(mcp_main())
    except KeyboardInterrupt:
        print("\nMCP服务器已停止")
    except Exception as e:
        print(f"错误: 启动MCP服务器失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="1:100万基础地理信息PostGIS MCP服务 - 主脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 重置数据库并导入数据
  python main.py --reset-and-import
  
  # 只启动MCP服务器
  python main.py --start-server
  
  # 重置并导入，然后启动服务器
  python main.py --reset-and-import --start-server
  
  # 指定GDB目录和参考图幅
  python main.py --reset-and-import --gdb-dir . --reference-tile F49
        """
    )
    
    parser.add_argument(
        '--reset-and-import',
        action='store_true',
        help='重置数据库并导入数据'
    )
    
    parser.add_argument(
        '--start-server',
        action='store_true',
        help='启动MCP服务器'
    )
    
    parser.add_argument(
        '--gdb-dir',
        type=str,
        default='.',
        help='GDB文件目录（默认: 当前目录）'
    )
    
    parser.add_argument(
        '--reference-tile',
        type=str,
        default='F49',
        help='参考图幅代码，用于分析表结构（默认: F49）'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新创建表（即使表已存在）'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何操作，显示帮助
    if not args.reset_and_import and not args.start_server:
        parser.print_help()
        return
    
    # 执行重置和导入
    if args.reset_and_import:
        success = reset_and_import(
            gdb_dir=args.gdb_dir,
            reference_tile=args.reference_tile,
            force=args.force
        )
        if not success:
            sys.exit(1)
    
    # 启动服务器
    if args.start_server:
        start_server()


if __name__ == "__main__":
    main()

