"""
导入所有图幅的数据到统一的PostGIS表结构
所有图幅共享同一组表，通过tile_code字段区分
"""

import fiona
import psycopg2
from shapely.geometry import shape
from pathlib import Path
from typing import Dict, Any, List
import sys
import configparser
import time
import logging
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def clean_identifier(name: str, max_length: int = 63) -> str:
    """清理标识符名称，符合PostgreSQL命名规范"""
    name = name.lower().replace("-", "_").replace(".", "_").replace(" ", "_")
    if name and name[0].isdigit():
        name = "_" + name
    if len(name) > max_length:
        name = name[:max_length]
    return name


def get_table_name(layer_name: str) -> str:
    """根据图层名获取表名"""
    return layer_name.lower()


def extract_tile_code(gdb_name: str) -> str:
    """提取图幅代码"""
    gdb_name = gdb_name.replace(".gdb", "")
    if len(gdb_name) >= 3 and gdb_name[0] in ["F", "G"] and gdb_name[1:3].isdigit():
        return gdb_name[:3]
    return gdb_name


def import_layer_data(
    gdb_path: str,
    layer_name: str,
    table_name: str,
    tile_code: str,
    conn: psycopg2.extensions.connection,
    srid: int,
    batch_size: int = 1000,
    skip_invalid: bool = True,
) -> int:
    """
    导入单个图层的数据到统一表
    """
    try:
        with fiona.open(gdb_path, layer=layer_name) as src:
            layer_schema = src.schema
            properties = layer_schema["properties"]

            with conn.cursor() as cur:
                # 获取表的现有字段
                cur.execute(
                    """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = %s
                    ORDER BY ordinal_position;
                """,
                    (table_name,),
                )

                existing_columns = [row[0] for row in cur.fetchall()]
                data_columns = [
                    col
                    for col in existing_columns
                    if col
                    not in ["id", "geom", "tile_code", "created_at", "updated_at"]
                ]

                # 构建字段映射
                field_mapping = {}
                for field_name in properties.keys():
                    clean_name = clean_identifier(field_name)
                    if clean_name in data_columns:
                        field_mapping[field_name] = clean_name

                # 确保字段顺序与数据库表字段顺序一致
                # 按照数据库字段顺序构建field_names
                mapped_db_columns = []
                for db_col in data_columns:
                    # 找到对应的GDB字段名
                    gdb_field = None
                    for gdb_name, db_name in field_mapping.items():
                        if db_name == db_col:
                            gdb_field = gdb_name
                            break
                    if gdb_field:
                        mapped_db_columns.append(db_col)

                # 准备插入SQL（按照数据库字段顺序）
                field_names = ["geom", "tile_code"] + mapped_db_columns
                placeholders = [f"ST_GeomFromText(%s, {srid})", "%s"] + ["%s"] * len(
                    mapped_db_columns
                )

                insert_sql = f"""
                INSERT INTO {table_name} ({', '.join(field_names)})
                VALUES ({', '.join(placeholders)})
                """

                count = 0
                error_count = 0
                batch = []

                processed = 0
                layer_start_time = time.time()
                last_log_time = layer_start_time

                logger.info(f"    开始导入数据...")

                for feature in src:
                    processed += 1

                    if feature["geometry"] is None:
                        continue

                    try:
                        geom = shape(feature["geometry"])

                        # 验证并修复几何
                        if not geom.is_valid:
                            if skip_invalid:
                                geom = geom.buffer(0)
                                if not geom.is_valid:
                                    error_count += 1
                                    continue
                            else:
                                error_count += 1
                                continue

                        wkt_geom = geom.wkt

                        # 构建属性值（按照field_names的顺序，确保与数据库字段顺序一致）
                        values = [wkt_geom, tile_code]
                        # 按照mapped_db_columns的顺序构建值
                        for db_col in mapped_db_columns:
                            # 找到对应的GDB字段名
                            gdb_field = None
                            for gdb_name, db_name in field_mapping.items():
                                if db_name == db_col:
                                    gdb_field = gdb_name
                                    break

                            # 必须为每个字段添加值，即使gdb_field为None
                            if gdb_field:
                                value = feature["properties"].get(gdb_field)
                            else:
                                value = None
                                logger.warning(
                                    f"    警告: 字段 {db_col} 找不到对应的GDB字段"
                                )

                            # 确保字符串值被正确处理
                            if value is not None:
                                # Python 3中str已经是unicode，但确保编码正确
                                if isinstance(value, bytes):
                                    value = value.decode("utf-8", errors="ignore")
                                elif not isinstance(value, str):
                                    value = str(value)

                            values.append(value)

                        batch.append(tuple(values))

                        if len(batch) >= batch_size:
                            try:
                                # 调试：检查第一批数据
                                if count == len(batch) and len(batch) > 0:
                                    first_record = batch[0]
                                    logger.debug(
                                        f"    第一批数据示例: geom长度={len(str(first_record[0]))}, tile_code={first_record[1]}, 其他字段数={len(first_record)-2}"
                                    )
                                    if len(first_record) > 3:
                                        logger.debug(
                                            f"    pac={first_record[2]}, name={first_record[3] if len(first_record) > 3 else 'N/A'}"
                                        )
                                cur.executemany(insert_sql, batch)
                                conn.commit()
                                count += len(batch)
                                batch = []

                                # 每批显示进度
                                current_time = time.time()
                                elapsed = current_time - layer_start_time
                                if (
                                    current_time - last_log_time >= 5
                                    or processed % 1000 == 0
                                ):
                                    speed = count / elapsed if elapsed > 0 else 0
                                    logger.info(
                                        f"    已处理: {processed:,} 条 - 已导入 {count:,} 条 - 速度: {speed:.0f} 条/秒"
                                    )
                                    last_log_time = current_time
                            except Exception as e:
                                conn.rollback()
                                error_count += len(batch)
                                logger.warning(f"    批量插入失败: {e}")
                                batch = []

                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:
                            logger.warning(f"跳过记录: {e}")
                        continue

                # 插入剩余数据
                if batch:
                    try:
                        cur.executemany(insert_sql, batch)
                        conn.commit()
                        count += len(batch)
                        logger.info(f"    插入最后一批: {len(batch)} 条")
                    except Exception as e:
                        conn.rollback()
                        error_count += len(batch)
                        logger.warning(f"    插入剩余数据失败: {e}")

                # 显示最终统计
                layer_elapsed = time.time() - layer_start_time
                logger.info(f"    处理完成: {processed:,} 条记录")
                logger.info(f"    成功导入: {count:,} 条")
                if error_count > 0:
                    logger.warning(f"    失败记录: {error_count:,} 条")
                if layer_elapsed > 0:
                    avg_speed = count / layer_elapsed
                    logger.info(f"    平均速度: {avg_speed:.0f} 条/秒")

                # 更新统计信息
                logger.info(f"    更新表统计信息...")
                try:
                    cur.execute(f"ANALYZE {table_name};")
                    conn.commit()
                    logger.info(f"    统计信息已更新")
                except Exception:
                    conn.rollback()
                    logger.warning(f"    更新统计信息失败")

                return count

    except Exception as e:
        logger.error(f"导入图层 {layer_name} 时出错: {e}")
        return 0


def import_gdb_to_unified_tables(
    gdb_path: str,
    conn: psycopg2.extensions.connection,
    srid: int = 4326,
    batch_size: int = 1000,
    skip_invalid: bool = True,
) -> Dict[str, Any]:
    """
    导入GDB文件的所有图层到统一表结构
    """
    gdb_name = Path(gdb_path).stem.replace(".gdb", "")
    tile_code = extract_tile_code(gdb_name)

    start_time = time.time()
    logger.info(f"开始导入GDB: {gdb_name}, 图幅代码: {tile_code}")
    logger.info(
        f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}"
    )

    # 获取所有图层
    try:
        layers = fiona.listlayers(gdb_path)
    except Exception as e:
        raise ValueError(f"无法读取GDB文件: {e}")

    if not layers:
        raise ValueError(f"GDB文件为空: {gdb_path}")

    logger.info(f"找到 {len(layers)} 个图层，开始处理...")
    logger.info("=" * 60)

    # 统计信息
    table_stats = defaultdict(int)
    success_count = 0
    error_count = 0
    skipped_count = 0

    for idx, layer_name in enumerate(layers, 1):
        layer_start_time = time.time()
        logger.info(f"[{idx}/{len(layers)}] 处理图层: {layer_name}")

        try:
            table_name = get_table_name(layer_name)
            logger.info(f"处理图层: {layer_name} -> 表: {table_name}")

            # 检查表是否存在
            with conn.cursor() as cur:
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

                if not cur.fetchone()[0]:
                    logger.warning(f"  [SKIP] 表 {table_name} 不存在，跳过导入")
                    logger.warning(
                        f"  请先运行: python scripts/create_unified_schema.py"
                    )
                    skipped_count += 1
                    continue

            # 检查图层是否有数据
            layer_empty = False
            try:
                with fiona.open(gdb_path, layer=layer_name) as src:
                    first = next(iter(src), None)
                    if first is None:
                        layer_empty = True
            except StopIteration:
                layer_empty = True
            except Exception:
                pass

            if layer_empty:
                elapsed = time.time() - layer_start_time
                logger.info(
                    f"  [SKIP] 图层 {layer_name} 为空（0条记录） - 耗时 {elapsed:.2f}秒"
                )
                skipped_count += 1
                continue

            logger.info(f"  → 导入到表: {table_name}")
            count = import_layer_data(
                gdb_path,
                layer_name,
                table_name,
                tile_code,
                conn,
                srid,
                batch_size,
                skip_invalid,
            )

            elapsed = time.time() - layer_start_time
            if count > 0:
                table_stats[table_name] += count
                success_count += 1
                logger.info(f"  ✓ 成功导入 {count:,} 条记录 - 耗时 {elapsed:.2f}秒")
            else:
                error_count += 1
                logger.warning(
                    f"  ✗ 图层 {layer_name} 导入失败（源数据有记录，但导入0条） - 耗时 {elapsed:.2f}秒"
                )

        except Exception as e:
            elapsed = time.time() - layer_start_time
            error_count += 1
            logger.error(
                f"  ✗ 导入图层 {layer_name} 时出错: {e} - 耗时 {elapsed:.2f}秒"
            )
            import traceback

            logger.debug(traceback.format_exc())

        # 显示进度
        progress = (idx / len(layers)) * 100
        logger.info(f"  进度: {idx}/{len(layers)} ({progress:.1f}%)")
        logger.info("-" * 60)

    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"导入完成!")
    logger.info(f"  总耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
    logger.info(f"  总图层数: {len(layers)}")
    logger.info(f"  成功导入: {success_count} 个图层")
    logger.info(f"  跳过(空): {skipped_count} 个图层")
    if error_count > 0:
        logger.warning(f"  导入失败: {error_count} 个图层")
    logger.info(f"  总记录数: {sum(table_stats.values()):,} 条")
    logger.info("=" * 60)

    return {
        "status": "success",
        "gdb_name": gdb_name,
        "tile_code": tile_code,
        "total_layers": len(layers),
        "success_layers": success_count,
        "error_layers": error_count,
        "skipped_layers": skipped_count,
        "total_time_seconds": total_time,
        "table_stats": dict(table_stats),
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="导入所有图幅的数据到统一的PostGIS表结构"
    )
    parser.add_argument(
        "--gdb-dir", "-d", default=".", help="包含GDB文件的目录（默认: 当前目录）"
    )
    parser.add_argument("--gdb", "-g", help="单个GDB文件路径（如果指定，只导入该文件）")
    parser.add_argument(
        "--srid", type=int, default=4326, help="坐标系SRID（默认: 4326）"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="批量插入大小（默认: 1000）"
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        default=True,
        help="跳过无效几何（默认: True）",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("导入所有图幅数据到统一表结构")
    print("=" * 80)

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

    # 查找GDB文件
    gdb_files = []

    if args.gdb:
        # 单个GDB文件
        gdb_path = Path(args.gdb)
        if gdb_path.exists():
            gdb_files.append(str(gdb_path))
        else:
            print(f"错误: GDB文件不存在: {args.gdb}")
            conn.close()
            sys.exit(1)
    else:
        # 目录中查找所有GDB文件
        gdb_dir = Path(args.gdb_dir)
        gdb_files = [str(p) for p in gdb_dir.glob("*.gdb") if p.is_dir()]

        if not gdb_files:
            print(f"错误: 目录中未找到GDB文件: {gdb_dir}")
            conn.close()
            sys.exit(1)

    print(f"\n找到 {len(gdb_files)} 个GDB文件:")
    for gdb_file in gdb_files:
        print(f"  - {gdb_file}")

    # 导入数据
    print("\n" + "=" * 80)
    print("开始导入数据")
    print("=" * 80)

    total_success = 0
    total_failed = 0

    for gdb_file in gdb_files:
        print(f"\n导入: {gdb_file}")
        print("-" * 80)

        try:
            result = import_gdb_to_unified_tables(
                gdb_file, conn, args.srid, args.batch_size, args.skip_invalid
            )
            total_success += 1
            print(
                f"\n[完成] {result['gdb_name']} - 成功导入 {result['success_layers']} 个图层"
            )
        except Exception as e:
            total_failed += 1
            print(f"\n[失败] {gdb_file}: {e}")
            import traceback

            traceback.print_exc()

    conn.close()

    # 显示总结
    print("\n" + "=" * 80)
    print("导入总结")
    print("=" * 80)
    print(f"成功: {total_success} 个图幅")
    print(f"失败: {total_failed} 个图幅")
    print("=" * 80)

    if total_success > 0:
        print("\n数据导入完成！现在可以使用MCP服务查询数据了。")
        print("使用 list_tile_codes 查看已导入的图幅")
        print("使用 list_tables 查看已创建的表")
    else:
        print("\n没有成功导入任何数据，请检查错误信息。")
        sys.exit(1)


if __name__ == "__main__":
    main()
