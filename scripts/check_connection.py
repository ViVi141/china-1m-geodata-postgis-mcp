"""
测试PostgreSQL/PostGIS连接
"""

import psycopg2
import sys
import os
from pathlib import Path
import configparser

# 设置Windows控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试PostgreSQL/PostGIS连接")
    print("=" * 60)
    
    # 读取配置
    config_file = Path(__file__).parent.parent / "config" / "database.ini"
    if not config_file.exists():
        print(f"错误: 配置文件不存在: {config_file}")
        print("请确保 config/database.ini 文件存在")
        return False
    
    config = configparser.ConfigParser()
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config.read_file(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件: {e}")
        return False
    
    if 'postgresql' not in config:
        print("错误: 配置文件中缺少[postgresql]节")
        return False
    
    db_config = config['postgresql']
    
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
                print(f"  表名: {', '.join(tables)}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("[OK] 所有测试通过！可以开始使用MCP服务了")
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

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

