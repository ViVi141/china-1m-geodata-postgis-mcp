"""
检查几何数据质量
"""

import psycopg2
import sys
from pathlib import Path
import configparser

def check_geometry_quality():
    """检查几何数据质量"""
    print("=" * 60)
    print("检查几何数据质量")
    print("=" * 60)
    
    # 读取配置
    config_file = Path(__file__).parent.parent / "config" / "database.ini"
    if not config_file.exists():
        print(f"错误: 配置文件不存在: {config_file}")
        return False
    
    config = configparser.ConfigParser()
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config.read_file(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件: {e}")
        return False
    
    db_config = config['postgresql']
    
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
            print(f"  空几何: {total_empty:,} ({total_empty/total_records*100:.1f}%)" if total_records > 0 else "  空几何: 0")
            print(f"  无效几何: {total_invalid:,} ({total_invalid/total_records*100:.1f}%)" if total_records > 0 else "  无效几何: 0")
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

if __name__ == "__main__":
    success = check_geometry_quality()
    sys.exit(0 if success else 1)

