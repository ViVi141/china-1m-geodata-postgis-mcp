"""
重置数据库脚本
删除所有导入的地理数据表，保留PostGIS扩展
"""

import psycopg2
import sys
import os
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
        with open(config_file, "r", encoding="utf-8") as f:
            config.read_file(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件: {e}")
        return False

    if "postgresql" not in config:
        print(f"错误: 配置文件中缺少[postgresql]节")
        return False

    db_config = config["postgresql"]

    # 在Docker环境中，优先使用环境变量（如果设置）
    # 这样可以避免挂载的配置文件覆盖容器环境变量的问题
    host = os.getenv("DB_HOST") or db_config.get("host", "localhost")
    port = int(os.getenv("DB_PORT", 0)) or db_config.getint("port", 5432)
    database = os.getenv("DB_NAME") or db_config.get("database")
    user = os.getenv("DB_USER") or db_config.get("user")
    # 直接从环境变量读取密码，避免配置文件中的特殊字符问题
    password = (
        os.getenv("DB_PASSWORD", "").strip() or db_config.get("password", "").strip()
    )

    # 显示配置信息（显示密码前3个字符用于调试）
    password_preview = (
        f"{password[:3]}***"
        if password and len(password) >= 3
        else ("***已设置***" if password else "未设置")
    )
    config_source = (
        "环境变量" if os.getenv("DB_PASSWORD") or os.getenv("DB_HOST") else "配置文件"
    )

    print(f"数据库连接信息 (来源: {config_source}):")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  数据库: {database}")
    print(f"  用户: {user}")
    print(f"  密码: {password_preview} (长度: {len(password)})")

    # 尝试连接，提供更详细的错误信息
    try:
        print(f"\n正在连接到: {host}:{port}/{database} (用户: {user})")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=5,
        )

        # 验证连接到的PostgreSQL版本和容器信息
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            pg_version = cur.fetchone()[0]
            print(f"✓ 成功连接到PostgreSQL")
            print(f"  PostgreSQL版本: {pg_version[:50]}...")

            # 检查PostGIS是否可用
            try:
                cur.execute("SELECT PostGIS_Version();")
                postgis_version = cur.fetchone()[0]
                print(f"  PostGIS版本: {postgis_version}")
            except:
                print(f"  ⚠️  警告: PostGIS扩展未安装")

        with conn.cursor() as cur:
            # 查找所有有geom字段的表（导入的地理数据表）
            cur.execute(
                """
                SELECT DISTINCT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                  AND column_name = 'geom'
                  AND table_name NOT IN ('spatial_ref_sys', 'geometry_columns');
            """
            )

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
                if response not in ["yes", "y"]:
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
                cur.execute(
                    "DELETE FROM geometry_columns WHERE f_table_schema = 'public';"
                )
                conn.commit()
                print("\n  [OK] 已清理geometry_columns")
            except Exception as e:
                conn.rollback()
                print(f"\n  [WARN] 清理geometry_columns失败: {e}")

            # 显示剩余表
            cur.execute(
                """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE';
            """
            )
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
        print("\n诊断信息:")
        print(f"  尝试连接: {host}:{port}/{database} (用户: {user})")
        print(
            f"  尝试使用的密码前3个字符: {password[:3] if len(password) >= 3 else 'N/A'}"
        )
        print(f"  密码长度: {len(password)}")
        print(f"  配置来源: {config_source}")

        # 在Docker环境中提供额外的诊断信息
        env_password = os.getenv("DB_PASSWORD", "")
        if env_password:
            print(f"  环境变量 DB_PASSWORD 已设置 (长度: {len(env_password)})")
            print(
                f"  环境变量 DB_PASSWORD 前3个字符: {env_password[:3] if len(env_password) >= 3 else 'N/A'}"
            )
            print(
                f"  环境变量 DB_PASSWORD 后3个字符: {env_password[-3:] if len(env_password) >= 3 else 'N/A'}"
            )
            if len(env_password) != len(password):
                print(
                    f"  ⚠️  警告: 环境变量密码长度 ({len(env_password)}) 与实际使用的密码长度 ({len(password)}) 不一致！"
                )
        else:
            print(f"  环境变量 DB_PASSWORD 未设置，使用配置文件中的密码")
            # 读取配置文件中的实际密码长度
            config_password = db_config.get("password", "").strip()
            if config_password:
                print(f"  配置文件中的密码长度: {len(config_password)}")

        # 检查是否连接到了错误的PostgreSQL容器
        print("\n⚠️  可能的问题:")
        print("1. **连接到了错误的PostgreSQL容器**（最可能）")
        print("   - 检查是否有多个PostgreSQL容器在运行:")
        print("     docker ps | grep postgres")
        print("   - 确认 geodata-postgres 容器在正确的网络中:")
        print("     docker inspect geodata-postgres | grep NetworkMode")
        print("   - 确认 data-importer 容器在正确的网络中:")
        print("     docker inspect geodata-importer | grep NetworkMode")
        print("   - 检查 geodata-network 网络:")
        print("     docker network inspect geodata-network")
        print("2. 密码不匹配")
        print("   - 验证PostgreSQL容器的实际密码:")
        print("     docker inspect geodata-postgres | grep -A 5 POSTGRES_PASSWORD")
        print("   - 或者: docker-compose exec postgres env | grep POSTGRES_PASSWORD")
        print("3. 如果PostgreSQL容器使用了旧密码（可能来自旧的volume），需要:")
        print("   - 方法1: 查看容器实际使用的密码，修改 .env 文件使其一致")
        print("   - 方法2: 重新创建容器和数据卷（注意：会删除数据）:")
        print("     docker-compose down")
        print("     docker volume rm geodata-postgres-data")
        print("     修改 .env 文件中的 POSTGRES_PASSWORD")
        print("     docker-compose up -d")
        print("4. 配置文件路径: {}".format(config_file))
        return False
    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="重置数据库，删除所有导入的地理数据表")
    parser.add_argument("--yes", "-y", action="store_true", help="跳过确认，直接删除")
    args = parser.parse_args()

    try:
        success = reset_database(confirm=not args.yes)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
