"""
统一的分析导入工具集
整合解析图幅结构、创建表结构和导入数据三个步骤
"""

import sys
import argparse
from pathlib import Path
import configparser
import json
import subprocess
import psycopg2

# 导入各个工具模块的功能（使用相对导入）
sys.path.insert(0, str(Path(__file__).parent))

from parse_tile_schema import parse_tile_completely
from create_unified_schema import load_analysis_result, create_unified_table_schema
from import_all_tiles import import_gdb_to_unified_tables


def get_database_connection():
    """获取数据库连接"""
    import os

    # 在Docker环境中，优先使用环境变量（如果设置）
    # 这样可以避免挂载的配置文件覆盖容器环境变量的问题
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
            raise FileNotFoundError(
                f"配置文件不存在，已检查以下路径:\n"
                + "\n".join(f"  - {p}" for p in possible_paths)
                + "\n\n在Docker环境中，请设置环境变量: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
            )

        print(f"使用配置文件: {config_file}")
        config = configparser.ConfigParser()
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config.read_file(f)
        except Exception as e:
            raise FileNotFoundError(f"无法读取配置文件 {config_file}: {e}")

        if "postgresql" not in config:
            raise ValueError(f"配置文件中缺少[postgresql]节: {config_file}")

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

    # 显示配置信息（用于调试，不显示完整密码）
    print(f"数据库连接配置:")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  数据库: {database}")
    print(f"  用户: {user}")
    if password:
        password_preview = f"{password[:3]}***" if len(password) >= 3 else "***"
        print(f"  密码: {password_preview} (长度: {len(password)})")
    else:
        print(f"  密码: (未设置)")

    # 验证必要参数
    if not all([host, database, user]):
        raise ValueError("数据库配置不完整: host, database, user 必须设置")

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
        print(f"✓ 成功连接到数据库: {host}:{port}/{database}")
        return conn
    except psycopg2.OperationalError as e:
        raise ConnectionError(
            f"无法连接到数据库 {host}:{port}/{database}: {e}\n"
            f"请检查:\n"
            f"  1. 数据库服务是否运行\n"
            f"  2. 主机名是否正确（Docker环境中应使用服务名 'postgres'）\n"
            f"  3. 用户名和密码是否正确\n"
            f"  4. 网络连接是否正常"
        )


def step1_parse_tile(
    gdb_path: str, output_dir: str = "analysis", reference_tile: str = None
) -> str:
    """
    步骤1：解析图幅结构

    Args:
        gdb_path: GDB文件路径（参考图幅，通常使用F49）
        output_dir: 输出目录
        reference_tile: 参考图幅代码（如果为None，从gdb_path提取）

    Returns:
        分析结果JSON文件路径
    """
    print("=" * 80)
    print("步骤1：解析图幅结构")
    print("=" * 80)

    if not reference_tile:
        gdb_name = Path(gdb_path).stem.replace(".gdb", "")
        reference_tile = (
            gdb_name[:3]
            if len(gdb_name) >= 3 and gdb_name[0] in ["F", "G"]
            else gdb_name
        )

    print(f"参考图幅: {reference_tile}")
    print(f"GDB路径: {gdb_path}")
    print(f"输出目录: {output_dir}\n")

    result = parse_tile_completely(gdb_path, output_dir)

    if not result:
        raise RuntimeError("解析图幅结构失败")

    analysis_file = Path(output_dir) / f"{reference_tile}_complete_analysis.json"

    if not analysis_file.exists():
        raise FileNotFoundError(f"分析结果文件未生成: {analysis_file}")

    print(f"\n[完成] 分析结果已保存到: {analysis_file}")
    return str(analysis_file)


def step2_create_schema(
    analysis_file: str, srid: int = 4326, force: bool = False
) -> bool:
    """
    步骤2：创建统一表结构

    Args:
        analysis_file: 分析结果JSON文件路径
        srid: 坐标系SRID
        force: 是否强制重新创建表

    Returns:
        是否成功
    """
    print("\n" + "=" * 80)
    print("步骤2：创建统一表结构")
    print("=" * 80)

    analysis_path = Path(analysis_file)
    if not analysis_path.exists():
        raise FileNotFoundError(f"分析结果文件不存在: {analysis_file}")

    print(f"分析结果: {analysis_file}")
    analysis_result = load_analysis_result(analysis_file)
    print(f"图层数: {len(analysis_result.get('layers', []))}")

    conn = get_database_connection()

    try:
        # 如果使用--force，先删除已存在的表
        if force:
            print("\n[警告] 使用--force选项，将删除已存在的表")
            with conn.cursor() as cur:
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
        result = create_unified_table_schema(analysis_result, conn, srid)

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

        if result["errors"]:
            print("\n错误列表:")
            for error in result["errors"]:
                print(f"  - {error}")

        return len(result["tables_created"]) > 0

    finally:
        conn.close()


def step3_import_data(
    gdb_dir: str = ".",
    srid: int = 4326,
    batch_size: int = 1000,
    skip_invalid: bool = True,
) -> dict:
    """
    步骤3：导入所有图幅数据

    Args:
        gdb_dir: 包含GDB文件的目录
        srid: 坐标系SRID
        batch_size: 批量插入大小
        skip_invalid: 是否跳过无效几何

    Returns:
        导入结果统计
    """
    print("\n" + "=" * 80)
    print("步骤3：导入所有图幅数据")
    print("=" * 80)

    # 查找GDB文件
    gdb_dir_path = Path(gdb_dir)
    gdb_files = [str(p) for p in gdb_dir_path.glob("*.gdb") if p.is_dir()]

    if not gdb_files:
        raise FileNotFoundError(f"目录中未找到GDB文件: {gdb_dir}")

    print(f"\n找到 {len(gdb_files)} 个GDB文件:")
    for gdb_file in gdb_files:
        print(f"  - {gdb_file}")

    conn = get_database_connection()

    try:
        total_success = 0
        total_failed = 0
        total_records = 0

        for gdb_file in gdb_files:
            print(f"\n导入: {gdb_file}")
            print("-" * 80)

            try:
                result = import_gdb_to_unified_tables(
                    gdb_file, conn, srid, batch_size, skip_invalid
                )
                total_success += 1
                total_records += sum(result.get("table_stats", {}).values())
                print(
                    f"\n[完成] {result['gdb_name']} - 成功导入 {result['success_layers']} 个图层"
                )
            except Exception as e:
                total_failed += 1
                print(f"\n[失败] {gdb_file}: {e}")
                import traceback

                traceback.print_exc()

        return {
            "total_files": len(gdb_files),
            "success": total_success,
            "failed": total_failed,
            "total_records": total_records,
        }

    finally:
        conn.close()


def full_setup(
    reference_gdb: str = None,
    gdb_dir: str = ".",
    output_dir: str = "analysis",
    srid: int = 4326,
    batch_size: int = 1000,
    skip_invalid: bool = True,
    force: bool = False,
    skip_parse: bool = False,
    skip_create: bool = False,
    skip_import: bool = False,
):
    """
    完整设置流程：解析 -> 创建表结构 -> 导入数据

    Args:
        reference_gdb: 参考图幅GDB路径（用于解析结构，默认自动查找F49.gdb）
        gdb_dir: 包含所有GDB文件的目录
        output_dir: 分析结果输出目录
        srid: 坐标系SRID
        batch_size: 批量插入大小
        skip_invalid: 是否跳过无效几何
        force: 是否强制重新创建表
        skip_parse: 跳过解析步骤（使用已有分析结果）
        skip_create: 跳过创建表结构步骤
        skip_import: 跳过导入数据步骤
    """
    print("=" * 80)
    print("统一数据库设置工具")
    print("=" * 80)
    print("\n本工具将执行以下步骤：")
    print("  1. 解析图幅结构（分析GDB文件的所有图层和字段）")
    print("  2. 创建统一表结构（在PostgreSQL中创建表）")
    print("  3. 导入所有图幅数据（将所有GDB数据导入到统一表）")
    print("=" * 80)

    analysis_file = None

    # 步骤1：解析图幅结构
    if not skip_parse:
        if not reference_gdb:
            # 自动查找参考图幅（优先使用F49）
            default_gdbs = ["F49.gdb", "G49.gdb", "G50.gdb", "F50.gdb"]
            for gdb_file in default_gdbs:
                gdb_path = Path(gdb_file)
                if gdb_path.exists():
                    reference_gdb = str(gdb_path)
                    print(f"\n自动选择参考图幅: {reference_gdb}")
                    break

            if not reference_gdb:
                raise FileNotFoundError(
                    "未找到参考图幅GDB文件。请指定 --reference-gdb 参数，"
                    "或确保当前目录下有 F49.gdb、G49.gdb、G50.gdb 或 F50.gdb"
                )

        analysis_file = step1_parse_tile(reference_gdb, output_dir)
    else:
        # 使用已有分析结果
        if not reference_gdb:
            reference_gdb = "F49"  # 默认使用F49

        analysis_file = Path(output_dir) / f"{reference_gdb}_complete_analysis.json"
        if not analysis_file.exists():
            # 尝试查找任何分析结果文件
            analysis_dir = Path(output_dir)
            analysis_files = list(analysis_dir.glob("*_complete_analysis.json"))
            if analysis_files:
                analysis_file = analysis_files[0]
                print(f"\n使用已有分析结果: {analysis_file}")
            else:
                raise FileNotFoundError(
                    f"未找到分析结果文件。请先运行解析步骤，或指定 --reference-gdb 参数"
                )
        else:
            print(f"\n使用已有分析结果: {analysis_file}")

    # 步骤2：创建统一表结构
    if not skip_create:
        success = step2_create_schema(str(analysis_file), srid, force)
        if not success:
            print("\n[警告] 表结构创建失败或没有创建任何表")
            response = input("是否继续导入数据? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                print("已取消")
                return
    else:
        print("\n[跳过] 创建表结构步骤")

    # 步骤3：导入所有图幅数据
    if not skip_import:
        result = step3_import_data(gdb_dir, srid, batch_size, skip_invalid)

        # 显示最终总结
        print("\n" + "=" * 80)
        print("最终总结")
        print("=" * 80)
        print(f"总GDB文件数: {result['total_files']}")
        print(f"成功导入: {result['success']} 个图幅")
        print(f"导入失败: {result['failed']} 个图幅")
        print(f"总记录数: {result['total_records']:,} 条")
        print("=" * 80)

        if result["success"] > 0:
            print("\n✅ 数据库设置完成！现在可以使用MCP服务查询数据了。")
            print("\n下一步：")
            print("  - 使用 list_tile_codes 查看已导入的图幅")
            print("  - 使用 list_tables 查看已创建的表")
            print("  - 使用 query_data 或 execute_sql 查询数据")
        else:
            print("\n❌ 没有成功导入任何数据，请检查错误信息。")
    else:
        print("\n[跳过] 导入数据步骤")

    print("\n" + "=" * 80)
    print("设置完成")
    print("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="统一的分析导入工具集 - 整合解析、创建表结构和导入数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：

  # 完整流程（自动执行所有步骤）
  python scripts/setup_unified_database.py

  # 指定参考图幅和GDB目录
  python scripts/setup_unified_database.py --reference-gdb F49.gdb --gdb-dir .

  # 只执行导入步骤（表结构已创建）
  python scripts/setup_unified_database.py --skip-parse --skip-create

  # 强制重新创建表结构
  python scripts/setup_unified_database.py --force

  # 自定义参数
  python scripts/setup_unified_database.py --srid 4326 --batch-size 2000
        """,
    )

    parser.add_argument(
        "--reference-gdb",
        "-r",
        help="参考图幅GDB路径（用于解析结构，默认自动查找F49.gdb）",
    )
    parser.add_argument(
        "--gdb-dir", "-d", default=".", help="包含所有GDB文件的目录（默认: 当前目录）"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="analysis",
        dest="output_dir",
        help="分析结果输出目录（默认: analysis/）",
    )
    parser.add_argument(
        "--srid", type=int, default=4326, help="坐标系SRID（默认: 4326）"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="批量插入大小（默认: 1000）"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="强制重新创建表（会删除已存在的表）"
    )
    parser.add_argument(
        "--skip-parse", action="store_true", help="跳过解析步骤（使用已有分析结果）"
    )
    parser.add_argument("--skip-create", action="store_true", help="跳过创建表结构步骤")
    parser.add_argument("--skip-import", action="store_true", help="跳过导入数据步骤")

    args = parser.parse_args()

    try:
        full_setup(
            reference_gdb=args.reference_gdb,
            gdb_dir=args.gdb_dir,
            output_dir=args.output_dir,
            srid=args.srid,
            batch_size=args.batch_size,
            skip_invalid=True,
            force=args.force,
            skip_parse=args.skip_parse,
            skip_create=args.skip_create,
            skip_import=args.skip_import,
        )
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
