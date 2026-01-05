"""
数据导入器：核心数据导入逻辑
"""

import psycopg2
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .spec_loader import SpecLoader

logger = logging.getLogger(__name__)


class DataImporter:
    """数据导入器"""
    
    def __init__(self):
        self.spec_loader = SpecLoader()
        self.default_srid = 4326
    
    async def import_data(
        self,
        data_path: str,
        spec_name: Optional[str] = None,
        database_config: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        导入地理数据
        
        Args:
            data_path: 数据文件或目录路径
            spec_name: 数据规格名称（可选）
            database_config: 数据库配置
            options: 导入选项
            
        Returns:
            导入结果字典
        """
        if options is None:
            options = {}
        
        # 自动检测规格
        if not spec_name:
            spec_name = self.spec_loader.detect_spec(data_path)
            if spec_name:
                logger.info(f"自动检测到数据规格: {spec_name}")
            else:
                raise ValueError("无法自动检测数据规格，请指定spec_name参数")
        
        # 加载规格配置
        spec = self.spec_loader.load_spec(spec_name)
        
        # 获取导入选项
        srid = options.get("srid", spec.get("default_srid", self.default_srid))
        batch_size = options.get("batch_size", 1000)
        skip_invalid = options.get("skip_invalid", True)
        create_indexes = options.get("create_indexes", True)
        
        # 连接数据库
        conn = self._get_connection(database_config)
        
        try:
            # 确保PostGIS扩展已安装
            self._ensure_postgis(conn)
            
            # 检测数据格式（目前仅支持GDB）
            data_format = self._detect_format(data_path)
            
            if data_format != "gdb":
                raise ValueError(f"目前仅支持GDB格式，检测到格式: {data_format}")
            
            # 导入GDB数据到PostgreSQL
            result = await self._import_gdb(
                data_path, spec, conn, srid, batch_size, skip_invalid, create_indexes
            )
            
            return result
        
        finally:
            conn.close()
    
    async def verify_data(
        self,
        table_name: Optional[str] = None,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        验证已导入的数据
        
        Args:
            table_name: 表名（可选，如果不提供则验证所有表）
            database_config: 数据库配置
            
        Returns:
            验证结果字典
        """
        conn = self._get_connection(database_config)
        
        try:
            with conn.cursor() as cur:
                if table_name:
                    tables = [table_name]
                else:
                    # 获取所有表
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                          AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """)
                    tables = [row[0] for row in cur.fetchall()]
                
                results = {}
                for table in tables:
                    result = self._verify_table(cur, table)
                    results[table] = result
                
                return {"tables": results}
        
        finally:
            conn.close()
    
    async def query_data(
        self,
        table_name: str,
        spatial_filter: Optional[Dict[str, Any]] = None,
        attribute_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        查询地理数据
        
        Args:
            table_name: 表名
            spatial_filter: 空间过滤条件
            attribute_filter: 属性过滤条件
            limit: 返回记录数限制
            database_config: 数据库配置
            
        Returns:
            查询结果字典
        """
        conn = self._get_connection(database_config)
        
        try:
            with conn.cursor() as cur:
                # 构建查询SQL
                sql = f"SELECT * FROM {table_name} WHERE 1=1"
                params = []
                
                # 添加空间过滤
                if spatial_filter:
                    if "bbox" in spatial_filter:
                        bbox = spatial_filter["bbox"]
                        sql += " AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)"
                        params.extend(bbox)
                    elif "geometry" in spatial_filter:
                        geom_wkt = spatial_filter["geometry"]
                        sql += " AND ST_Intersects(geom, ST_GeomFromText(%s, 4326))"
                        params.append(geom_wkt)
                
                # 添加属性过滤
                if attribute_filter:
                    for key, value in attribute_filter.items():
                        sql += f" AND {key} = %s"
                        params.append(value)
                
                sql += " LIMIT %s"
                params.append(limit)
                
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    # 将几何对象转换为WKT
                    if "geom" in record and record["geom"]:
                        try:
                            # 检查是否为空几何
                            cur.execute("SELECT ST_IsEmpty(%s), ST_AsText(%s)", (record["geom"], record["geom"]))
                            is_empty, geom_wkt = cur.fetchone()
                            if is_empty:
                                record["geom"] = geom_wkt + " (空几何)"
                            else:
                                record["geom"] = geom_wkt
                        except Exception as e:
                            # 如果转换失败，使用原始值
                            record["geom"] = str(record["geom"])
                    results.append(record)
                
                return {
                    "count": len(results),
                    "limit": limit,
                    "data": results
                }
        
        finally:
            conn.close()
    
    def _get_connection(self, database_config: Dict[str, Any]) -> psycopg2.extensions.connection:
        """获取数据库连接"""
        return psycopg2.connect(
            host=database_config.get('host', 'localhost'),
            port=database_config.get('port', 5432),
            database=database_config.get('database'),
            user=database_config.get('user'),
            password=database_config.get('password')
        )
    
    def _ensure_postgis(self, conn):
        """确保PostGIS扩展已安装"""
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise Exception(f"无法安装PostGIS扩展: {e}")
    
    def _detect_format(self, data_path: str) -> str:
        """检测数据格式（目前仅支持GDB）"""
        path = Path(data_path)
        
        if path.is_dir():
            # 检查是否是GDB目录
            if path.suffix == ".gdb" or (path.is_dir() and any(path.glob("*.gdbtable"))):
                return "gdb"
        
        if path.suffix.lower() == ".gdb":
            return "gdb"
        
        raise ValueError(f"无法识别GDB格式: {data_path}。请确保路径指向.gdb目录")
    
    async def _import_gdb(
        self,
        gdb_path: str,
        spec: Dict[str, Any],
        conn: psycopg2.extensions.connection,
        srid: int,
        batch_size: int,
        skip_invalid: bool,
        create_indexes: bool
    ) -> Dict[str, Any]:
        """导入GDB文件"""
        # 这里复用原有的导入逻辑，但使用规格配置
        from .gdb_importer import GDBImporter
        importer = GDBImporter(spec)
        # 在事件循环中运行同步代码
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: importer.import_gdb_sync(
                gdb_path, conn, srid, batch_size, skip_invalid, create_indexes
            )
        )
    
    async def list_tables(
        self,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        列出PostgreSQL中所有已导入的地理数据表
        
        Args:
            database_config: 数据库配置
            
        Returns:
            表列表字典
        """
        conn = self._get_connection(database_config)
        
        try:
            with conn.cursor() as cur:
                # 查找所有包含geom字段的表（PostGIS表）
                cur.execute("""
                    SELECT 
                        t.table_name,
                        (SELECT COUNT(*) FROM information_schema.columns 
                         WHERE table_schema = 'public' 
                         AND table_name = t.table_name 
                         AND column_name = 'geom') as has_geom
                    FROM information_schema.tables t
                    WHERE t.table_schema = 'public' 
                      AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name;
                """)
                
                all_tables = cur.fetchall()
                
                # 过滤出有geom字段的表
                geo_tables = []
                for table_name, has_geom in all_tables:
                    if has_geom > 0:
                        # 获取记录数
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                            count = cur.fetchone()[0]
                            
                            # 获取SRID
                            cur.execute(f"""
                                SELECT DISTINCT ST_SRID(geom) as srid
                                FROM {table_name}
                                WHERE geom IS NOT NULL
                                LIMIT 1;
                            """)
                            srid_result = cur.fetchone()
                            srid = srid_result[0] if srid_result else None
                            
                            geo_tables.append({
                                "table_name": table_name,
                                "record_count": count,
                                "srid": srid
                            })
                        except Exception as e:
                            logger.warning(f"获取表 {table_name} 信息失败: {e}")
                
                return {
                    "tables": geo_tables,
                    "total": len(geo_tables)
                }
        
        finally:
            conn.close()
    
    async def list_tile_codes(
        self,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        列出数据库中所有已导入的图幅代码
        
        Args:
            database_config: 数据库配置
            
        Returns:
            图幅代码列表字典
        """
        conn = self._get_connection(database_config)
        
        try:
            with conn.cursor() as cur:
                # 查找所有包含tile_code字段的表
                cur.execute("""
                    SELECT DISTINCT table_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                      AND column_name = 'tile_code'
                      AND table_name NOT IN ('spatial_ref_sys', 'geometry_columns')
                    ORDER BY table_name;
                """)
                
                tables_with_tile_code = [row[0] for row in cur.fetchall()]
                
                if not tables_with_tile_code:
                    return {
                        "tile_codes": [],
                        "total": 0,
                        "message": "未找到包含tile_code字段的表"
                    }
                
                # 从所有表中收集图幅代码
                all_tile_codes = set()
                tile_code_stats = {}
                
                for table_name in tables_with_tile_code:
                    try:
                        cur.execute(f"""
                            SELECT DISTINCT tile_code, COUNT(*) as count
                            FROM {table_name}
                            WHERE tile_code IS NOT NULL
                            GROUP BY tile_code
                            ORDER BY tile_code;
                        """)
                        
                        for tile_code, count in cur.fetchall():
                            all_tile_codes.add(tile_code)
                            if tile_code not in tile_code_stats:
                                tile_code_stats[tile_code] = {}
                            tile_code_stats[tile_code][table_name] = count
                    except Exception as e:
                        logger.warning(f"查询表 {table_name} 的图幅代码失败: {e}")
                
                # 构建结果
                tile_codes_list = []
                for tile_code in sorted(all_tile_codes):
                    total_records = sum(tile_code_stats[tile_code].values())
                    tile_codes_list.append({
                        "tile_code": tile_code,
                        "total_records": total_records,
                        "tables": tile_code_stats[tile_code]
                    })
                
                return {
                    "tile_codes": tile_codes_list,
                    "total": len(tile_codes_list)
                }
        
        finally:
            conn.close()
    
    async def execute_sql(
        self,
        sql: str,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行SQL查询
        
        Args:
            sql: SQL语句
            database_config: 数据库配置
            
        Returns:
            查询结果字典
        """
        # 安全检查：只允许SELECT语句
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            raise ValueError("只允许执行SELECT查询语句")
        
        conn = self._get_connection(database_config)
        
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                
                # 获取列名
                columns = [desc[0] for desc in cur.description] if cur.description else []
                
                # 获取数据
                rows = cur.fetchall()
                
                # 转换结果
                results = []
                for row in rows:
                    record = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # 处理几何对象
                        if isinstance(value, (bytes, str)) and col == "geom":
                            try:
                                cur.execute("SELECT ST_AsText(%s)", (value,))
                                record[col] = cur.fetchone()[0]
                            except:
                                record[col] = str(value)
                        else:
                            record[col] = value
                    results.append(record)
                
                return {
                    "columns": columns,
                    "count": len(results),
                    "data": results
                }
        
        finally:
            conn.close()
    
    def _verify_table(self, cur, table_name: str) -> Dict[str, Any]:
        """验证单个表"""
        result = {
            "table_name": table_name,
            "record_count": 0,
            "srid": None,
            "bbox": None,
            "invalid_geometries": 0,
            "columns": []
        }
        
        try:
            # 记录数
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            result["record_count"] = cur.fetchone()[0]
            
            # 坐标系
            cur.execute(f"""
                SELECT DISTINCT ST_SRID(geom) as srid
                FROM {table_name}
                WHERE geom IS NOT NULL
                LIMIT 1;
            """)
            srid_result = cur.fetchone()
            if srid_result:
                result["srid"] = srid_result[0]
            
            # 空间范围
            cur.execute(f"""
                SELECT 
                    ST_XMin(ST_Extent(geom)) as xmin,
                    ST_YMin(ST_Extent(geom)) as ymin,
                    ST_XMax(ST_Extent(geom)) as xmax,
                    ST_YMax(ST_Extent(geom)) as ymax
                FROM {table_name}
                WHERE geom IS NOT NULL;
            """)
            bbox = cur.fetchone()
            if bbox:
                result["bbox"] = {
                    "minx": bbox[0],
                    "miny": bbox[1],
                    "maxx": bbox[2],
                    "maxy": bbox[3]
                }
            
            # 无效几何
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name}
                WHERE geom IS NOT NULL 
                  AND NOT ST_IsValid(geom);
            """)
            result["invalid_geometries"] = cur.fetchone()[0]
            
            # 字段信息（包含字段说明）
            cur.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                  AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            # 获取字段说明
            from core.spec_loader import SpecLoader
            spec_loader = SpecLoader()
            field_descriptions = self._get_field_descriptions(table_name, spec_loader)
            
            columns_info = []
            for row in cur.fetchall():
                col_name = row[0]
                col_type = row[1]
                description = field_descriptions.get(col_name, "字段说明请查看docs/FIELD_SPEC.md")
                columns_info.append({
                    "name": col_name,
                    "type": col_type,
                    "description": description
                })
            result["columns"] = columns_info
        
        except Exception as e:
            result["error"] = str(e)
        
        return result

