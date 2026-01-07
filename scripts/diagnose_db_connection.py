#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接诊断工具
用于排查Docker容器中的数据库连接问题
"""

import os
import sys
from pathlib import Path
import configparser


def diagnose_connection():
    """诊断数据库连接配置"""
    print("=" * 80)
    print("数据库连接诊断工具")
    print("=" * 80)
    print()

    # 1. 检查环境变量
    print("1. 环境变量检查:")
    print("-" * 80)
    env_vars = {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    }

    for key, value in env_vars.items():
        if value:
            if "PASSWORD" in key:
                preview = f"{value[:3]}***" if len(value) >= 3 else "***"
                print(f"  {key}: {preview} (长度: {len(value)})")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: (未设置)")

    print()

    # 2. 检查配置文件
    print("2. 配置文件检查:")
    print("-" * 80)
    possible_paths = [
        Path(__file__).parent.parent / "config" / "database.ini",  # 本地开发
        Path("/app/config/database.ini"),  # Docker容器
    ]

    config_file = None
    for path in possible_paths:
        if path.exists():
            config_file = path
            print(f"  找到配置文件: {path}")
            break

    if config_file:
        try:
            config = configparser.ConfigParser()
            with open(config_file, "r", encoding="utf-8") as f:
                config.read_file(f)

            if "postgresql" in config:
                db_config = config["postgresql"]
                print(f"  主机: {db_config.get('host', '(未设置)')}")
                print(f"  端口: {db_config.get('port', '(未设置)')}")
                print(f"  数据库: {db_config.get('database', '(未设置)')}")
                print(f"  用户: {db_config.get('user', '(未设置)')}")
                password = db_config.get("password", "")
                if password:
                    preview = f"{password[:3]}***" if len(password) >= 3 else "***"
                    print(f"  密码: {preview} (长度: {len(password)})")
                else:
                    print(f"  密码: (未设置)")
            else:
                print(f"  警告: 配置文件中缺少[postgresql]节")
        except Exception as e:
            print(f"  错误: 无法读取配置文件: {e}")
    else:
        print(f"  未找到配置文件，已检查以下路径:")
        for path in possible_paths:
            print(f"    - {path}")

    print()

    # 3. 确定最终使用的配置
    print("3. 最终使用的配置（优先级：环境变量 > 配置文件）:")
    print("-" * 80)

    # 从环境变量或配置文件获取
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "").strip()

    if config_file and not all([host, database, user, password]):
        try:
            config = configparser.ConfigParser()
            with open(config_file, "r", encoding="utf-8") as f:
                config.read_file(f)

            if "postgresql" in config:
                db_config = config["postgresql"]
                host = host or db_config.get("host", "localhost")
                port = int(port) if port else db_config.getint("port", 5432)
                database = database or db_config.get("database")
                user = user or db_config.get("user")
                password = password or db_config.get("password", "").strip()
        except Exception:
            pass

    if not port:
        port = 5432

    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  数据库: {database}")
    print(f"  用户: {user}")
    if password:
        preview = f"{password[:3]}***" if len(password) >= 3 else "***"
        print(f"  密码: {preview} (长度: {len(password)})")
    else:
        print(f"  密码: (未设置)")

    print()

    # 4. 检查配置问题
    print("4. 配置问题检查:")
    print("-" * 80)

    issues = []

    if not host:
        issues.append("❌ 主机名未设置")
    elif host == "localhost" and os.path.exists("/.dockerenv"):
        issues.append("⚠️  在Docker容器中使用localhost，应使用服务名'postgres'")
    elif host != "postgres" and os.path.exists("/.dockerenv"):
        issues.append(f"⚠️  在Docker容器中host为'{host}'，建议使用服务名'postgres'")

    if not database:
        issues.append("❌ 数据库名未设置")

    if not user:
        issues.append("❌ 用户名未设置")

    if not password:
        issues.append("⚠️  密码未设置，将使用空密码")

    if not issues:
        print("  ✓ 配置看起来正常")
    else:
        for issue in issues:
            print(f"  {issue}")

    print()

    # 5. 尝试连接（如果可能）
    print("5. 连接测试:")
    print("-" * 80)

    if not all([host, database, user]):
        print("  ⚠️  配置不完整，跳过连接测试")
        return

    try:
        import psycopg2

        print(f"  尝试连接到: {host}:{port}/{database}")
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"  ✓ 连接成功!")
                print(f"  PostgreSQL版本: {version.split(',')[0]}")

                # 检查PostGIS扩展
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');"
                )
                has_postgis = cur.fetchone()[0]
                if has_postgis:
                    print(f"  ✓ PostGIS扩展已安装")
                else:
                    print(f"  ⚠️  PostGIS扩展未安装")

            conn.close()
        except psycopg2.OperationalError as e:
            print(f"  ❌ 连接失败: {e}")
            print()
            print("  可能的原因:")
            print("    1. 数据库服务未运行")
            print("    2. 主机名或端口不正确")
            print("    3. 用户名或密码错误")
            print("    4. 网络连接问题（Docker环境中检查服务名和网络）")
            if os.path.exists("/.dockerenv"):
                print("    5. 在Docker环境中，确保:")
                print("       - 使用服务名'postgres'而不是'localhost'")
                print("       - 容器在同一网络中")
                print("       - depends_on配置正确")
    except ImportError:
        print("  ⚠️  psycopg2未安装，跳过连接测试")

    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        diagnose_connection()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
