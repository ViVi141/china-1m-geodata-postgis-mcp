"""
导入GDB数据到PostgreSQL/PostGIS数据库
支持指定单个GDB文件或目录（批量导入）
"""

import asyncio
import sys
import argparse
from pathlib import Path
from core.data_importer import DataImporter
from core.config_manager import ConfigManager
from core.spec_loader import SpecLoader

async def import_data(gdb_path=None, spec_name=None, srid=4326, batch_size=1000):
    """导入GDB数据"""
    print("=" * 60)
    print("导入GDB数据到PostgreSQL/PostGIS")
    print("=" * 60)
    
    # 检查配置
    config_manager = ConfigManager()
    try:
        db_config = config_manager.get_default_database_config()
        print(f"\n[OK] 数据库配置: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    except Exception as e:
        print(f"\n错误: 无法读取数据库配置: {e}")
        return False
    
    # 检查规格
    spec_loader = SpecLoader()
    specs = spec_loader.list_specs()
    if not specs:
        print("\n错误: 未找到数据规格配置")
        return False
    
    if not spec_name:
        spec_name = "china_1m_2021" if "china_1m_2021" in specs else specs[0]
    elif spec_name not in specs:
        print(f"\n错误: 未找到数据规格: {spec_name}")
        print(f"可用规格: {', '.join(specs)}")
        return False
    
    print(f"\n[OK] 使用数据规格: {spec_name}")
    
    # 查找GDB文件
    gdb_files = []
    
    if gdb_path:
        gdb_path = Path(gdb_path)
        if gdb_path.is_file() or (gdb_path.is_dir() and gdb_path.suffix == '.gdb'):
            # 单个GDB文件
            if gdb_path.exists():
                gdb_files.append(str(gdb_path))
            else:
                print(f"\n错误: GDB文件不存在: {gdb_path}")
                return False
        elif gdb_path.is_dir():
            # 目录，查找所有.gdb文件
            gdb_files = [str(p) for p in gdb_path.glob("*.gdb") if p.is_dir()]
            if not gdb_files:
                print(f"\n错误: 目录中未找到GDB文件: {gdb_path}")
                return False
        else:
            print(f"\n错误: 无效的路径: {gdb_path}")
            return False
    else:
        # 默认检查当前目录
        default_gdbs = ['F49.gdb', 'G49.gdb', 'G50.gdb', 'F50.gdb']
        for gdb_file in default_gdbs:
            gdb_path = Path(gdb_file)
            if gdb_path.exists():
                gdb_files.append(gdb_file)
                print(f"[OK] 找到GDB文件: {gdb_file}")
            else:
                print(f"[SKIP] 未找到: {gdb_file}")
        
        if not gdb_files:
            print("\n错误: 未找到任何GDB文件")
            print("用法: python scripts/import_data.py <gdb_path>")
            print("  或: python scripts/import_data.py --dir <directory>")
            return False
    
    print(f"\n找到 {len(gdb_files)} 个GDB文件:")
    for gdb_file in gdb_files:
        print(f"  - {gdb_file}")
    
    # 导入数据
    data_importer = DataImporter()
    
    print("\n" + "=" * 60)
    print("开始导入数据")
    print("=" * 60)
    
    total_success = 0
    total_failed = 0
    
    for gdb_file in gdb_files:
        print(f"\n导入: {gdb_file}")
        print("-" * 60)
        
        try:
            result = await data_importer.import_data(
                data_path=gdb_file,
                spec_name=spec_name,
                database_config=db_config,
                options={
                    "srid": srid,
                    "batch_size": batch_size,
                    "skip_invalid": True,
                    "create_indexes": True
                }
            )
            
            if result.get("status") == "success":
                total_success += 1
                print(f"\n[OK] 导入成功")
                print(f"  图幅代码: {result.get('tile_code')}")
                total_layers = result.get('total_layers', 0)
                success_layers = result.get('success_layers', 0)
                error_layers = result.get('error_layers', 0)
                skipped_layers = result.get('skipped_layers', 0)
                total_time = result.get('total_time_seconds', 0)
                print(f"  总图层数: {total_layers}")
                print(f"  成功导入: {success_layers}")
                if error_layers > 0:
                    print(f"  导入失败: {error_layers}")
                if skipped_layers > 0:
                    print(f"  跳过(空): {skipped_layers}")
                if total_time > 0:
                    print(f"  耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
                print(f"  表统计:")
                for table, count in sorted(result.get('table_stats', {}).items()):
                    print(f"    {table}: {count:,} 条记录")
            else:
                total_failed += 1
                print(f"[ERROR] 导入失败: {result}")
        
        except Exception as e:
            total_failed += 1
            print(f"[ERROR] 导入失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 60)
    print("导入完成")
    print("=" * 60)
    print(f"成功: {total_success} 个文件")
    print(f"失败: {total_failed} 个文件")
    
    if total_success > 0:
        print("\n[下一步] 验证导入的数据:")
        print("  python scripts/verify_data.py")
        print("\n[下一步] 查询数据:")
        print("  python scripts/query_data.py")
    
    return total_success > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入GDB数据到PostgreSQL/PostGIS数据库")
    parser.add_argument('gdb_path', nargs='?', help='GDB文件路径或包含GDB文件的目录')
    parser.add_argument('--dir', '-d', dest='gdb_dir', help='包含GDB文件的目录（批量导入）')
    parser.add_argument('--spec', '-s', dest='spec_name', help='数据规格名称（默认: china_1m_2021）')
    parser.add_argument('--srid', type=int, default=4326, help='目标坐标系SRID（默认: 4326）')
    parser.add_argument('--batch-size', type=int, default=1000, dest='batch_size', help='批量插入大小（默认: 1000）')
    
    args = parser.parse_args()
    
    # 确定GDB路径
    gdb_path = args.gdb_dir if args.gdb_dir else args.gdb_path
    
    try:
        success = asyncio.run(import_data(
            gdb_path=gdb_path,
            spec_name=args.spec_name,
            srid=args.srid,
            batch_size=args.batch_size
        ))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

