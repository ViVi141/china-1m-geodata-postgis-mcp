"""
GDB文件导入器：实现GDB格式的导入逻辑
"""

import fiona
import psycopg2
from shapely.geometry import shape
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
import time

from .logging_config import get_logger

logger = get_logger(__name__)


class GDBImporter:
    """GDB文件导入器"""

    def __init__(self, spec: Dict[str, Any]):
        """
        初始化GDB导入器

        Args:
            spec: 数据规格配置
        """
        self.spec = spec
        self.layer_mapping = spec.get("layer_mapping", {})
        self.default_srid = spec.get("default_srid", 4326)

    def import_gdb_sync(
        self,
        gdb_path: str,
        conn: psycopg2.extensions.connection,
        srid: int,
        batch_size: int,
        skip_invalid: bool,
        create_indexes: bool,
    ) -> Dict[str, Any]:
        """
        导入GDB文件

        Args:
            gdb_path: GDB文件路径
            conn: 数据库连接
            srid: 目标坐标系SRID
            batch_size: 批量插入大小
            skip_invalid: 是否跳过无效几何
            create_indexes: 是否创建索引

        Returns:
            导入结果字典
        """
        gdb_name = Path(gdb_path).stem.replace(".gdb", "")
        tile_code = self._extract_tile_code(gdb_name)

        start_time = time.time()
        logger.info(f"开始导入GDB: {gdb_name}, 图幅代码: {tile_code}")
        logger.info(
            f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}"
        )

        # 获取所有图层
        layers = self._get_layers(gdb_path)
        if not layers:
            raise ValueError(f"无法读取GDB文件或文件为空: {gdb_path}")

        logger.info(f"找到 {len(layers)} 个图层，开始处理...")
        logger.info("=" * 60)

        # 统计信息
        table_stats = defaultdict(int)
        success_count = 0
        error_count = 0
        skipped_count = 0  # 空图层计数

        for idx, layer_name in enumerate(layers, 1):
            layer_start_time = time.time()
            logger.info(f"[{idx}/{len(layers)}] 处理图层: {layer_name}")
            try:
                table_name = self._get_table_name(layer_name)
                logger.info(f"处理图层: {layer_name} -> 表: {table_name}")

                try:
                    # 先检查图层是否有数据
                    layer_empty = False
                    try:
                        with fiona.open(gdb_path, layer=layer_name) as src:
                            # 尝试读取第一个要素
                            first = next(iter(src), None)
                            if first is None:
                                layer_empty = True
                    except StopIteration:
                        layer_empty = True
                    except Exception:
                        pass  # 如果检查失败，继续尝试导入

                    if layer_empty:
                        elapsed = time.time() - layer_start_time
                        logger.info(
                            f"  [SKIP] 图层 {layer_name} 为空（0条记录） - 耗时 {elapsed:.2f}秒"
                        )
                        skipped_count += 1
                        continue

                    logger.info(f"  → 导入到表: {table_name}")
                    count = self._import_layer(
                        gdb_path,
                        layer_name,
                        table_name,
                        tile_code,
                        conn,
                        srid,
                        batch_size,
                        skip_invalid,
                        create_indexes,
                    )

                    elapsed = time.time() - layer_start_time
                    if count > 0:
                        table_stats[table_name] += count
                        success_count += 1
                        logger.info(
                            f"  ✓ 成功导入 {count:,} 条记录 - 耗时 {elapsed:.2f}秒"
                        )
                    else:
                        error_count += 1
                        logger.warning(
                            f"  ✗ 图层 {layer_name} 导入失败（源数据有记录，但导入0条） - 耗时 {elapsed:.2f}秒"
                        )
                except Exception as e:
                    elapsed = time.time() - layer_start_time
                    error_count += 1
                    logger.error(
                        f"  ✗ 图层 {layer_name} 导入时出错: {e} - 耗时 {elapsed:.2f}秒"
                    )
                    import traceback

                    logger.debug(traceback.format_exc())

            except Exception as e:
                elapsed = time.time() - layer_start_time
                error_count += 1
                logger.error(
                    f"  ✗ 导入图层 {layer_name} 时出错: {e} - 耗时 {elapsed:.2f}秒"
                )

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

    def _extract_tile_code(self, gdb_name: str) -> str:
        """提取图幅代码"""
        # 从规格配置中获取图幅代码提取规则
        tile_code_pattern = self.spec.get("tile_code_pattern", "auto")

        if tile_code_pattern == "auto":
            # 自动提取：F49, G49等
            if (
                len(gdb_name) >= 3
                and gdb_name[0] in ["F", "G"]
                and gdb_name[1:3].isdigit()
            ):
                return gdb_name[:3]
            return gdb_name
        else:
            # 使用自定义规则
            # TODO: 实现自定义规则解析
            return gdb_name

    def _get_layers(self, gdb_path: str) -> List[str]:
        """获取GDB文件中的所有图层"""
        try:
            layers = fiona.listlayers(gdb_path)
            return layers
        except Exception as e:
            logger.error(f"无法读取GDB图层: {e}")
            return []

    def _get_table_name(self, layer_name: str) -> str:
        """根据图层名获取表名"""
        # 移除可能的图幅前缀
        layer_code = layer_name.upper()
        if "_" in layer_code:
            layer_code = layer_code.split("_")[-1]

        # 查找映射
        if layer_code in self.layer_mapping:
            return self.layer_mapping[layer_code]["table_name"]

        # 如果没有映射，使用清理后的图层名
        return self._clean_identifier(layer_name.lower())

    def _clean_identifier(self, name: str, max_length: int = 63) -> str:
        """清理标识符名称，符合PostgreSQL命名规范"""
        name = name.replace("-", "_").replace(".", "_").replace(" ", "_")
        if name and name[0].isdigit():
            name = "_" + name
        if len(name) > max_length:
            name = name[:max_length]
        return name

    def _import_layer(
        self,
        gdb_path: str,
        layer_name: str,
        table_name: str,
        tile_code: str,
        conn: psycopg2.extensions.connection,
        srid: int,
        batch_size: int,
        skip_invalid: bool,
        create_indexes: bool,
    ) -> int:
        """导入单个图层"""
        try:
            with fiona.open(gdb_path, layer=layer_name) as src:
                layer_schema = src.schema
                properties = layer_schema["properties"]

                # 确保表存在
                if not self._create_table_if_not_exists(
                    conn, table_name, layer_schema, srid, create_indexes
                ):
                    logger.warning(f"无法创建表 {table_name}")
                    return 0

                with conn.cursor() as cur:
                    # 获取字段映射
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
                        if col not in ["id", "geom", "tile_code"]
                    ]

                    # 构建字段映射
                    field_mapping = {}
                    for field_name in properties.keys():
                        clean_name = self._clean_identifier(field_name)
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
                    placeholders = [f"ST_GeomFromText(%s, {srid})", "%s"] + [
                        "%s"
                    ] * len(mapped_db_columns)

                    insert_sql = f"""
                    INSERT INTO public.{table_name} ({', '.join(field_names)})
                    VALUES ({', '.join(placeholders)})
                    """

                    count = 0
                    error_count = 0
                    batch = []

                    # 初始化进度跟踪
                    processed = 0
                    layer_start_time = time.time()
                    last_log_time = layer_start_time
                    total_features = None  # 大图层不统计总数

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
                                if gdb_field:
                                    value = feature["properties"].get(gdb_field)
                                    # 确保字符串值被正确处理
                                    if value is not None:
                                        # Python 3中str已经是unicode，但确保编码正确
                                        if isinstance(value, bytes):
                                            value = value.decode(
                                                "utf-8", errors="ignore"
                                            )
                                        elif not isinstance(value, str):
                                            value = str(value)
                                    values.append(value)

                            batch.append(tuple(values))

                            if len(batch) >= batch_size:
                                try:
                                    cur.executemany(insert_sql, batch)
                                    conn.commit()
                                    count += len(batch)
                                    batch = []

                                    # 每批显示进度（每5秒或每1000条）
                                    current_time = time.time()
                                    elapsed = current_time - layer_start_time
                                    if (
                                        current_time - last_log_time >= 5
                                        or processed % 1000 == 0
                                    ):
                                        if total_features:
                                            progress_pct = (
                                                processed / total_features
                                            ) * 100
                                            speed = (
                                                count / elapsed if elapsed > 0 else 0
                                            )
                                            logger.info(
                                                f"    进度: {processed:,}/{total_features:,} ({progress_pct:.1f}%) - 已导入 {count:,} 条 - 速度: {speed:.0f} 条/秒"
                                            )
                                        else:
                                            speed = (
                                                count / elapsed if elapsed > 0 else 0
                                            )
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
                    if total_features:
                        logger.info(
                            f"    处理完成: {processed:,}/{total_features:,} 条记录"
                        )
                    else:
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
                        cur.execute(f"ANALYZE public.{table_name};")
                        conn.commit()
                        logger.info(f"    统计信息已更新")
                    except Exception:
                        conn.rollback()
                        logger.warning(f"    更新统计信息失败")

                    return count

        except Exception as e:
            logger.error(f"导入图层 {layer_name} 时出错: {e}")
            return 0

    def _create_table_if_not_exists(
        self,
        conn: psycopg2.extensions.connection,
        table_name: str,
        layer_schema: Dict[str, Any],
        srid: int,
        create_indexes: bool,
    ) -> bool:
        """创建表（如果不存在）"""
        try:
            with conn.cursor() as cur:
                geom_type = layer_schema["geometry"]
                if geom_type is None:
                    return False

                # 使用GEOMETRY类型以支持多种几何类型（避免类型不匹配错误）
                # 默认使用通用GEOMETRY类型，可以存储任何几何类型
                postgis_geom_type = "GEOMETRY"  # 使用通用类型，避免类型不匹配

                # 检查表是否存在
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

                table_exists = cur.fetchone()[0]

                if not table_exists:
                    # 创建新表
                    properties = layer_schema["properties"]

                    create_table_sql = f"""
                    CREATE TABLE public.{table_name} (
                        id SERIAL PRIMARY KEY,
                        geom GEOMETRY({postgis_geom_type}, {srid}),
                        tile_code VARCHAR(10)
                    """

                    # 添加属性字段
                    for field_name, field_type in properties.items():
                        clean_field_name = self._clean_identifier(field_name)
                        pg_type = self._get_pg_field_type(field_type)
                        create_table_sql += f",\n    {clean_field_name} {pg_type}"

                    create_table_sql += "\n);"

                    try:
                        cur.execute(create_table_sql)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        logger.error(f"创建表失败: {e}")
                        return False

                    # 创建索引
                    if create_indexes:
                        try:
                            cur.execute(
                                f"""
                                CREATE INDEX IF NOT EXISTS {table_name}_geom_idx 
                                ON public.{table_name} USING GIST (geom);
                            """
                            )
                            cur.execute(
                                f"""
                                CREATE INDEX IF NOT EXISTS {table_name}_tile_code_idx 
                                ON public.{table_name} (tile_code);
                            """
                            )
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            logger.warning(f"创建索引失败: {e}")

                else:
                    # 表已存在，检查是否有tile_code字段
                    try:
                        cur.execute(
                            """
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = %s 
                            AND column_name = 'tile_code';
                        """,
                            (table_name,),
                        )

                        if not cur.fetchone():
                            cur.execute(
                                f"ALTER TABLE public.{table_name} ADD COLUMN tile_code VARCHAR(10);"
                            )
                            conn.commit()

                            if create_indexes:
                                try:
                                    cur.execute(
                                        f"CREATE INDEX IF NOT EXISTS {table_name}_tile_code_idx ON public.{table_name} (tile_code);"
                                    )
                                    conn.commit()
                                except Exception:
                                    conn.rollback()
                    except Exception as e:
                        conn.rollback()
                        logger.warning(f"检查/添加tile_code字段失败: {e}")

                return True

        except Exception as e:
            conn.rollback()
            logger.error(f"创建表时出错: {e}")
            return False

    def _get_pg_field_type(self, fiona_type: str) -> str:
        """将Fiona字段类型映射到PostgreSQL类型"""
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
        if ":" in str(fiona_type):
            base_type = str(fiona_type).split(":")[0]
        else:
            base_type = str(fiona_type)

        return type_mapping.get(base_type.lower(), "TEXT")
