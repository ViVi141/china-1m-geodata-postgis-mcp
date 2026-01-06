"""
统一检查工具
整合了数据库连接检查、GDB图层检查和几何数据质量检查
"""

import psycopg2
import fiona
import argparse
import sys
import os
from pathlib import Path
import configparser

# 设置Windows控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')


def get_db_config():
    """读取数据库配置"""
    config_file = Path(__file__).parent.parent / "config" / "database.ini"
    if not config_file.exists():
        print(f"错误: 配置文件不存在: {config_file}")
        return None
    
    config = configparser.ConfigParser()
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config.read_file(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件: {e}")
        return None
    
    if 'postgresql' not in config:
        print("错误: 配置文件中缺少[postgresql]节")
        return None
    
    return config['postgresql']


def check_connection():
    """检查数据库连接和PostGIS"""
    print("=" * 60)
    print("检查数据库连接")
    print("=" * 60)
    
    db_config = get_db_config()
    if not db_config:
        return False
    
    try:
        print("\n[1/3] 连接数据库...")
        conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.getint('port', 5432),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password')
        )
        print("[OK] 数据库连接成功")
        
        print("\n[2/3] 检查PostGIS扩展...")
        with conn.cursor() as cur:
            cur.execute("SELECT PostGIS_Version();")
            version = cur.fetchone()[0]
            print(f"[OK] PostGIS版本: {version}")
            
            cur.execute("SELECT COUNT(*) FROM pg_extension WHERE extname = 'postgis';")
            count = cur.fetchone()[0]
            if count > 0:
                print("[OK] PostGIS扩展已启用")
            else:
                print("⚠ 警告: PostGIS扩展未启用，正在创建...")
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                conn.commit()
                print("[OK] PostGIS扩展已创建")
        
        print("\n[3/3] 检查数据库表...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE';
            """)
            table_count = cur.fetchone()[0]
            print(f"[OK] 当前数据库中有 {table_count} 个表")
            
            if table_count > 0:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    LIMIT 5;
                """)
                tables = [row[0] for row in cur.fetchall()]
                print(f"  示例表: {', '.join(tables)}")
        
        conn.close()
        print("\n" + "=" * 60)
        print("[OK] 数据库连接检查通过")
        print("=" * 60)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] 连接失败: {e}")
        print("\n请检查:")
        print("1. Docker容器是否正在运行: docker ps")
        print("2. 端口5432是否被占用")
        print("3. 数据库配置是否正确")
        return False
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False


def check_layers(gdb_path):
    """检查GDB文件中的图层"""
    print("=" * 60)
    print(f"检查GDB文件: {gdb_path}")
    print("=" * 60)
    
    gdb_file = Path(gdb_path)
    if not gdb_file.exists():
        print(f"错误: 文件不存在: {gdb_path}")
        return False
    
    try:
        layers = fiona.listlayers(gdb_path)
        if not layers:
            print("错误: 未找到任何图层")
            return False
        
        print(f"\n找到 {len(layers)} 个图层:\n")
        
        for layer_name in layers:
            try:
                with fiona.open(gdb_path, layer=layer_name) as src:
                    schema = src.schema
                    geom_type = schema.get('geometry', 'Unknown')
                    properties = schema.get('properties', {})
                    
                    # 统计记录数
                    count = 0
                    has_geometry = 0
                    has_null_geometry = 0
                    
                    try:
                        for feature in src:
                            count += 1
                            if feature.get('geometry'):
                                has_geometry += 1
                            else:
                                has_null_geometry += 1
                            
                            # 只统计前1000条，避免太慢
                            if count >= 1000:
                                break
                    except Exception as e:
                        print(f"  [WARN] 读取记录时出错: {e}")
                    
                    print(f"图层: {layer_name}")
                    print(f"  几何类型: {geom_type}")
                    print(f"  字段数: {len(properties)}")
                    if count < 1000:
                        print(f"  记录数: {count}")
                        print(f"  有几何: {has_geometry}, 无几何: {has_null_geometry}")
                    else:
                        print(f"  记录数: >= {count} (仅检查前1000条)")
                    print()
            
            except Exception as e:
                print(f"图层: {layer_name}")
                print(f"  [ERROR] 无法读取: {e}")
                print()
        
        return True
    
    except Exception as e:
        print(f"错误: 无法读取GDB文件: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_geometry_quality():
    """检查几何数据质量"""
    print("=" * 60)
    print("检查几何数据质量")
    print("=" * 60)
    
    db_config = get_db_config()
    if not db_config:
        return False
    
    try:
        conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.getint('port', 5432),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password')
        )
        
        with conn.cursor() as cur:
            # 查找所有有geom字段的表
            cur.execute("""
                SELECT DISTINCT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                  AND column_name = 'geom'
                  AND table_name NOT IN ('spatial_ref_sys', 'geometry_columns');
            """)
            
            tables = [row[0] for row in cur.fetchall()]
            
            if not tables:
                print("\n未找到任何表")
                return False
            
            print(f"\n检查 {len(tables)} 个表:\n")
            print("=" * 60)
            
            total_empty = 0
            total_invalid = 0
            total_records = 0
            
            for table_name in sorted(tables):
                try:
                    # 统计信息
                    cur.execute(f"""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN ST_IsEmpty(geom) THEN 1 END) as empty_count,
                            COUNT(CASE WHEN NOT ST_IsEmpty(geom) THEN 1 END) as non_empty_count,
                            COUNT(CASE WHEN NOT ST_IsValid(geom) THEN 1 END) as invalid_count
                        FROM {table_name}
                        WHERE geom IS NOT NULL;
                    """)
                    
                    total, empty_count, non_empty_count, invalid_count = cur.fetchone()
                    
                    total_records += total
                    total_empty += empty_count
                    total_invalid += invalid_count
                    
                    print(f"\n表: {table_name}")
                    print(f"  总记录数: {total:,}")
                    print(f"  非空几何: {non_empty_count:,}")
                    if empty_count > 0:
                        print(f"  [WARN] 空几何: {empty_count:,} ({empty_count/total*100:.1f}%)")
                    if invalid_count > 0:
                        print(f"  [ERROR] 无效几何: {invalid_count:,} ({invalid_count/total*100:.1f}%)")
                    
                except Exception as e:
                    print(f"\n表: {table_name}")
                    print(f"  [ERROR] 检查失败: {e}")
            
            print("\n" + "=" * 60)
            print("总体统计:")
            print(f"  总记录数: {total_records:,}")
            if total_records > 0:
                print(f"  空几何: {total_empty:,} ({total_empty/total_records*100:.1f}%)")
                print(f"  无效几何: {total_invalid:,} ({total_invalid/total_records*100:.1f}%)")
            print("=" * 60)
            
            if total_empty > 0:
                print("\n注意: 发现空几何对象，这可能是正常的（某些数据源可能包含空几何）")
            if total_invalid > 0:
                print("\n警告: 发现无效几何对象，建议检查数据源")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="统一检查工具 - 检查数据库连接、GDB图层和几何数据质量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查数据库连接
  python scripts/check.py --connection

  # 检查GDB文件
  python scripts/check.py --layers F49.gdb

  # 检查几何数据质量
  python scripts/check.py --geometry

  # 执行所有检查
  python scripts/check.py --all
        """
    )
    
    parser.add_argument('--connection', '-c', action='store_true',
                       help='检查数据库连接和PostGIS')
    parser.add_argument('--layers', '-l', metavar='GDB_PATH',
                       help='检查GDB文件中的图层信息')
    parser.add_argument('--geometry', '-g', action='store_true',
                       help='检查几何数据质量')
    parser.add_argument('--all', '-a', action='store_true',
                       help='执行所有检查')
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，显示帮助
    if not any([args.connection, args.layers, args.geometry, args.all]):
        parser.print_help()
        sys.exit(1)
    
    success = True
    
    if args.all or args.connection:
        if not check_connection():
            success = False
        print("\n")
    
    if args.all or args.layers:
        gdb_path = args.layers
        if not gdb_path:
            # 默认检查当前目录下的GDB文件
            gdb_files = ['F49.gdb', 'G49.gdb', 'G50.gdb', 'F50.gdb']
            available = [f for f in gdb_files if Path(f).exists()]
            
            if not available:
                print("错误: 未找到GDB文件")
                print("请指定GDB文件路径: python scripts/check.py --layers <gdb_path>")
                success = False
            else:
                gdb_path = available[0]
                print(f"使用默认文件: {gdb_path}\n")
        
        if gdb_path:
            if not check_layers(gdb_path):
                success = False
            print("\n")
    
    if args.all or args.geometry:
        if not check_geometry_quality():
            success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

