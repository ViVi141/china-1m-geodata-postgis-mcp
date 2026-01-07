"""
基于F49图幅的分析结果，创建适合MCP的统一PostGIS表结构
所有图幅共享同一组表，通过tile_code字段区分
"""

import json
import psycopg2
from pathlib import Path
from typing import Dict, Any
import sys
import configparser


def load_analysis_result(analysis_file: str) -> Dict[str, Any]:
    """加载分析结果"""
    with open(analysis_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_postgresql_type(fiona_type: Any, field_info: Dict[str, Any]) -> str:
    """根据字段信息获取PostgreSQL类型"""
    type_str = str(fiona_type)

    if ":" in type_str:
        base_type = type_str.split(":")[0]
        length = type_str.split(":")[1]
    else:
        base_type = type_str
        length = None

    base_type = base_type.lower()

    # 类型映射
    type_mapping = {
        "int": "INTEGER",
        "int32": "INTEGER",
        "int64": "BIGINT",
        "float": "DOUBLE PRECISION",
        "float32": "REAL",
        "float64": "DOUBLE PRECISION",
        "str": "TEXT",
        "string": "TEXT",
        "date": "DATE",
        "time": "TIME",
        "datetime": "TIMESTAMP",
        "bool": "BOOLEAN",
        "bytes": "BYTEA",
    }

    pg_type = type_mapping.get(base_type, "TEXT")

    # 字符串类型优化
    if pg_type == "TEXT" or base_type in ["str", "string"]:
        if length:
            try:
                max_len = int(length)
                if max_len <= 50:
                    return f"VARCHAR({max_len})"
                elif max_len <= 100:
                    return "VARCHAR(100)"
                elif max_len <= 255:
                    return "VARCHAR(255)"
                elif max_len <= 500:
                    return "VARCHAR(500)"
                else:
                    return "TEXT"
            except:
                pass

        # 根据实际数据优化
        max_length = field_info.get("max_length", 0)
        if max_length > 0:
            if max_length <= 50:
                return "VARCHAR(50)"
            elif max_length <= 100:
                return "VARCHAR(100)"
            elif max_length <= 255:
                return "VARCHAR(255)"
            elif max_length <= 500:
                return "VARCHAR(500)"
            else:
                return "TEXT"

    return pg_type


def create_unified_table_schema(
    analysis_result: Dict[str, Any],
    conn: psycopg2.extensions.connection,
    srid: int = 4326,
) -> Dict[str, Any]:
    """
    创建统一的表结构
    所有图幅共享同一组表
    """
    layers = analysis_result.get("layers", [])
    result = {"tables_created": [], "tables_skipped": [], "errors": []}

    with conn.cursor() as cur:
        # 确保PostGIS扩展已安装
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            conn.commit()
        except Exception as e:
            conn.rollback()
            result["errors"].append(f"无法安装PostGIS扩展: {e}")
            return result

        for layer_info in layers:
            if "error" in layer_info:
                result["tables_skipped"].append(
                    {
                        "layer": layer_info.get("layer_name", "Unknown"),
                        "reason": layer_info["error"],
                    }
                )
                continue

            layer_name = layer_info["layer_name"]
            geometry_type = layer_info.get("geometry_type", "Unknown")

            # 生成表名（使用图层名的小写形式）
            table_name = layer_name.lower()

            # 检查表是否已存在
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """,
                (table_name,),
            )

            if cur.fetchone()[0]:
                print(f"  [SKIP] 表 {table_name} 已存在，跳过创建")
                result["tables_skipped"].append(
                    {"layer": layer_name, "table": table_name, "reason": "表已存在"}
                )
                continue

            # 使用通用的 GEOMETRY 类型，而不是特定的几何类型
            # 因为不同图幅的同一图层可能包含不同的几何类型
            # 例如：某个图层在F49中是 MultiLineString，在G49中可能是 Polygon
            # 使用 GEOMETRY 类型可以支持所有几何类型

            # 构建CREATE TABLE语句
            columns = []

            # 1. 主键
            columns.append("id BIGSERIAL PRIMARY KEY")

            # 2. 几何字段（使用通用 GEOMETRY 类型）
            if geometry_type and geometry_type != "Unknown" and geometry_type != "None":
                # 使用 GEOMETRY(GEOMETRY, srid) 支持所有几何类型，同时指定SRID
                # 这样可以存储 Point、LineString、Polygon 等所有类型的几何对象
                columns.append(f"geom GEOMETRY(GEOMETRY, {srid})")

            # 3. 图幅代码（NOT NULL，用于区分不同图幅）
            columns.append("tile_code VARCHAR(10) NOT NULL")

            # 4. 数据字段
            fields = layer_info.get("fields", {})
            for field_name, field_info in fields.items():
                # 清理字段名
                clean_name = (
                    field_name.lower()
                    .replace("-", "_")
                    .replace(".", "_")
                    .replace(" ", "_")
                )
                if clean_name and clean_name[0].isdigit():
                    clean_name = "_" + clean_name
                if len(clean_name) > 63:
                    clean_name = clean_name[:63]

                # 避免冲突
                if clean_name in ["id", "geom", "tile_code"]:
                    clean_name = f"{clean_name}_field"

                # 获取PostgreSQL类型
                fiona_type = field_info.get("fiona_type", "str")
                pg_type = get_postgresql_type(fiona_type, field_info)

                # 构建列定义
                col_def = f"{clean_name} {pg_type}"

                # 注意：不自动添加 NOT NULL 约束
                # 因为不同图幅的数据可能不同，参考图幅中非空的字段在其他图幅可能为空
                # 如果需要 NOT NULL 约束，应该手动分析所有图幅的数据后再添加

                columns.append(col_def)

            # 5. 时间戳字段（用于数据管理）
            columns.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

            # 创建表
            # 注意：f-string 表达式中不能包含反斜杠，需要先定义换行符
            newline_indent = ",\n                "
            create_sql = f"""
            CREATE TABLE {table_name} (
                {newline_indent.join(columns)}
            );
            """

            try:
                cur.execute(create_sql)
                conn.commit()
                print(f"  [OK] 创建表: {table_name}")

                # 创建索引
                indexes = []

                # 空间索引
                if (
                    geometry_type
                    and geometry_type != "Unknown"
                    and geometry_type != "None"
                ):
                    index_sql = f"""
                    CREATE INDEX {table_name}_geom_idx 
                    ON {table_name} USING GIST (geom);
                    """
                    cur.execute(index_sql)
                    indexes.append(f"{table_name}_geom_idx (GIST)")

                # 图幅代码索引（用于快速过滤图幅）
                index_sql = f"""
                CREATE INDEX {table_name}_tile_code_idx 
                ON {table_name} (tile_code);
                """
                cur.execute(index_sql)
                indexes.append(f"{table_name}_tile_code_idx (BTREE)")

                # 为常用查询字段创建索引
                common_index_fields = ["gb", "name", "class", "type", "rn"]
                for field_name in common_index_fields:
                    clean_name = field_name.lower()
                    # 检查字段是否存在
                    cur.execute(
                        """
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s 
                        AND column_name = %s;
                    """,
                        (table_name, clean_name),
                    )

                    if cur.fetchone():
                        index_sql = f"""
                        CREATE INDEX {table_name}_{clean_name}_idx 
                        ON {table_name} ({clean_name});
                        """
                        try:
                            cur.execute(index_sql)
                            indexes.append(f"{table_name}_{clean_name}_idx (BTREE)")
                        except Exception:
                            pass  # 索引创建失败，继续

                conn.commit()

                # 添加表和列注释
                try:
                    comment_sql = f"""
                    COMMENT ON TABLE {table_name} IS '图层 {layer_name} 的统一表，存储所有图幅的数据';
                    """
                    cur.execute(comment_sql)

                    # 添加关键列注释
                    cur.execute(
                        f"""
                        COMMENT ON COLUMN {table_name}.tile_code IS '图幅代码，1:100万图幅编号（如F49、F50、G49、G50等）';
                    """
                    )

                    if geometry_type and geometry_type != "Unknown":
                        cur.execute(
                            f"""
                            COMMENT ON COLUMN {table_name}.geom IS 'PostGIS几何对象（通用GEOMETRY类型，支持所有几何类型）。参考图幅中的类型: {geometry_type}';
                        """
                        )

                    conn.commit()
                except Exception:
                    pass  # 注释添加失败不影响表创建

                result["tables_created"].append(
                    {
                        "layer": layer_name,
                        "table": table_name,
                        "geometry_type": geometry_type,
                        "columns": len(columns),
                        "indexes": len(indexes),
                    }
                )

            except Exception as exc:
                conn.rollback()
                error_msg = f"创建表 {table_name} 失败: {exc}"
                print(f"  [ERROR] {error_msg}")
                result["errors"].append(error_msg)
                result["tables_skipped"].append(
                    {"layer": layer_name, "table": table_name, "reason": str(exc)}
                )

    return result


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="基于分析结果创建统一的PostGIS表结构（所有图幅共享）"
    )
    parser.add_argument(
        "--analysis",
        "-a",
        default="analysis/F49_complete_analysis.json",
        help="分析结果JSON文件路径（默认: analysis/F49_complete_analysis.json）",
    )
    parser.add_argument(
        "--srid", type=int, default=4326, help="坐标系SRID（默认: 4326）"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="强制重新创建表（会删除已存在的表）"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("创建统一的PostGIS表结构")
    print("=" * 80)

    # 加载分析结果
    analysis_file = Path(args.analysis)
    if not analysis_file.exists():
        print(f"错误: 分析结果文件不存在: {analysis_file}")
        print("请先运行: python scripts/parse_tile_schema.py F49.gdb")
        sys.exit(1)

    print(f"\n加载分析结果: {analysis_file}")
    analysis_result = load_analysis_result(str(analysis_file))
    print(f"图层数: {len(analysis_result.get('layers', []))}")

    # 读取数据库配置
    # 在Docker环境中，优先使用环境变量（如果设置）
    import os

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "").strip()

    # 如果环境变量未设置，从配置文件读取
    if not all([host, database, user, password]):
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
            print(
                "\n在Docker环境中，请设置环境变量: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
            )
            sys.exit(1)

        print(f"使用配置文件: {config_file}")
        config = configparser.ConfigParser()
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config.read_file(f)
        except Exception as e:
            print(f"错误: 无法读取配置文件: {e}")
            sys.exit(1)

        if "postgresql" not in config:
            print(f"错误: 配置文件中缺少[postgresql]节")
            sys.exit(1)

        db_config = config["postgresql"]

        # 使用环境变量（如果设置）或配置文件的值
        host = host or db_config.get("host", "localhost")
        port = int(port) if port else db_config.getint("port", 5432)
        database = database or db_config.get("database")
        user = user or db_config.get("user")
        password = password or db_config.get("password", "").strip()
    else:
        print("使用环境变量配置数据库连接")
        port = int(port) if port else 5432

    # 显示配置信息（用于调试）
    print(f"\n数据库连接配置:")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  数据库: {database}")
    print(f"  用户: {user}")
    if password:
        password_preview = f"{password[:3]}***" if len(password) >= 3 else "***"
        print(f"  密码: {password_preview} (长度: {len(password)})")
    else:
        print(f"  密码: (未设置)")

    # 连接数据库
    print(f"\n连接数据库: {host}:{port}/{database}")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            client_encoding="UTF8",  # 确保使用UTF-8编码
        )
        # 设置连接编码
        with conn.cursor() as cur:
            cur.execute("SET client_encoding TO 'UTF8';")
        conn.commit()
        print(f"✓ 成功连接到数据库")
    except psycopg2.OperationalError as e:
        print(f"错误: 无法连接数据库: {e}")
        print(f"\n请检查:")
        print(f"  1. 数据库服务是否运行")
        print(f"  2. 主机名是否正确（Docker环境中应使用服务名 'postgres'）")
        print(f"  3. 用户名和密码是否正确")
        print(f"  4. 网络连接是否正常")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 连接数据库时发生异常: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # 如果使用--force，先删除已存在的表
    if args.force:
        print("\n[警告] 使用--force选项，将删除已存在的表")
        response = input("确认继续? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("已取消")
            conn.close()
            sys.exit(0)

        with conn.cursor() as cur:
            # 获取所有要创建的表名
            tables_to_drop = []
            for layer_info in analysis_result.get("layers", []):
                if "error" not in layer_info:
                    table_name = layer_info["layer_name"].lower()
                    tables_to_drop.append(table_name)

            for table_name in tables_to_drop:
                try:
                    cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                    print(f"  [DROP] 删除表: {table_name}")
                except Exception as e:
                    print(f"  [ERROR] 删除表 {table_name} 失败: {e}")

            conn.commit()

    # 创建表结构
    print("\n开始创建表结构...")
    result = create_unified_table_schema(analysis_result, conn, args.srid)

    conn.close()

    # 显示结果
    print("\n" + "=" * 80)
    print("创建结果")
    print("=" * 80)
    print(f"成功创建: {len(result['tables_created'])} 个表")
    print(f"跳过: {len(result['tables_skipped'])} 个表")
    if result["errors"]:
        print(f"错误: {len(result['errors'])} 个")

    if result["tables_created"]:
        print("\n已创建的表:")
        for table_info in result["tables_created"]:
            print(f"  - {table_info['table']} ({table_info['layer']})")
            print(
                f"    几何类型: {table_info['geometry_type']}, 列数: {table_info['columns']}, 索引数: {table_info['indexes']}"
            )

    if result["errors"]:
        print("\n错误列表:")
        for error in result["errors"]:
            print(f"  - {error}")

    print("\n" + "=" * 80)
    print("表结构创建完成！")
    print("=" * 80)
    print("\n下一步: 使用 scripts/import_all_tiles.py 导入所有图幅的数据")


if __name__ == "__main__":
    main()
