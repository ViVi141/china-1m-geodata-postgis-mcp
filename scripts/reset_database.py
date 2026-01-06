"""
重置数据库脚本
删除所有导入的地理数据表，保留PostGIS扩展
"""

import psycopg2
import sys
from pathlib import Path
import configparser

def reset_database(confirm=True):
    """重置数据库，删除所有导入的表"""
    print("=" * 60)
    print("重置数据库")
    print("=" * 60)
    
    # 读取配置
    # 支持多种路径：本地开发、Docker容器等
    possible_paths = [
        Path(__file__).parent.parent / "config" / "database.ini",  # 本地开发
        Path("/app/config/database.ini"),  # Docker容器
    ]
    
    config_file = None
    for path in possible_paths:
        if path.exists():
            config_file = path
            break
    
    if config_file is None:
        print(f"错误: 配置文件不存在，已检查以下路径:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    print(f"使用配置文件: {config_file}")
    
    config = configparser.ConfigParser()
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config.read_file(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件: {e}")
        return False
    
    if 'postgresql' not in config:
        print(f"错误: 配置文件中缺少[postgresql]节")
        return False
    
    db_config = config['postgresql']
    
    # 显示配置信息（不显示密码）
    print(f"数据库连接信息:")
    print(f"  主机: {db_config.get('host', 'localhost')}")
    print(f"  端口: {db_config.get('port', '5432')}")
    print(f"  数据库: {db_config.get('database', '')}")
    print(f"  用户: {db_config.get('user', '')}")
    print(f"  密码: {'***已设置***' if db_config.get('password') else '未设置'}")
    
    try:
        conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.getint('port', 5432),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password')
        )
        
        with conn.cursor() as cur:
            # 查找所有有geom字段的表（导入的地理数据表）
            cur.execute("""
                SELECT DISTINCT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                  AND column_name = 'geom'
                  AND table_name NOT IN ('spatial_ref_sys', 'geometry_columns');
            """)
            
            tables = [row[0] for row in cur.fetchall()]
            
            if not tables:
                print("\n未找到需要删除的表")
                print("数据库已经是空的状态")
                conn.close()
                return True
            
            print(f"\n找到 {len(tables)} 个表:")
            for table in tables:
                # 获取记录数
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cur.fetchone()[0]
                    print(f"  - {table}: {count:,} 条记录")
                except:
                    print(f"  - {table}: (无法获取记录数)")
            
            if confirm:
                print("\n" + "=" * 60)
                print("警告: 这将删除所有导入的地理数据表！")
                print("=" * 60)
                response = input("\n确认删除? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    print("已取消")
                    conn.close()
                    return False
            
            print("\n开始删除表...")
            deleted_count = 0
            
            for table in tables:
                try:
                    cur.execute(f"DROP TABLE IF EXISTS public.{table} CASCADE;")
                    conn.commit()
                    print(f"  [OK] 已删除: {table}")
                    deleted_count += 1
                except Exception as e:
                    conn.rollback()
                    print(f"  [ERROR] 删除 {table} 失败: {e}")
            
            # 清理geometry_columns（PostGIS系统表）
            try:
                cur.execute("DELETE FROM geometry_columns WHERE f_table_schema = 'public';")
                conn.commit()
                print("\n  [OK] 已清理geometry_columns")
            except Exception as e:
                conn.rollback()
                print(f"\n  [WARN] 清理geometry_columns失败: {e}")
            
            # 显示剩余表
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE';
            """)
            remaining = cur.fetchone()[0]
            
        conn.close()
        
        print("\n" + "=" * 60)
        print(f"重置完成: 删除了 {deleted_count} 个表")
        print(f"剩余表数: {remaining}")
        print("=" * 60)
        print("\n现在可以重新导入数据:")
        print("  python test_import.py")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"错误: 无法连接数据库: {e}")
        print("\n请检查:")
        print("1. PostgreSQL容器是否运行: docker ps")
        print("2. 数据库密码是否正确:")
        print("   - 检查 .env 文件中的 POSTGRES_PASSWORD")
        print("   - 确保与PostgreSQL容器启动时使用的密码一致")
        print("   - 或者检查环境变量 DB_PASSWORD 或 POSTGRES_PASSWORD")
        print("3. 配置文件路径: {}".format(config_file))
        print("4. 在Docker环境中，确保环境变量已正确传递到容器")
        return False
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='重置数据库，删除所有导入的地理数据表')
    parser.add_argument('--yes', '-y', action='store_true', 
                       help='跳过确认，直接删除')
    args = parser.parse_args()
    
    try:
        success = reset_database(confirm=not args.yes)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)

