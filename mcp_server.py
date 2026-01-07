"""
1:100万基础地理信息PostGIS MCP服务器
China 1M GeoData PostGIS MCP Server

基于PostgreSQL/PostGIS的空间数据服务
提供PostGIS空间数据查询、分析和交互能力
"""

import asyncio
import json
from typing import Any, Dict, List
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

from core.data_importer import DataImporter
from core.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
app = Server("china-1m-geodata-postgis-mcp")

# 初始化核心组件
config_manager = ConfigManager()
data_importer = DataImporter()


@app.list_resources()
async def list_resources() -> List[Resource]:
    """列出可用的资源"""
    resources = []

    # 列出可用的数据源
    data_sources = config_manager.list_data_sources()
    for source_name in data_sources:
        resources.append(
            Resource(
                uri=f"datasource://{source_name}",
                name=f"数据源: {source_name}",
                description=f"已配置的数据源: {source_name}",
                mimeType="application/json",
            )
        )

    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri.startswith("datasource://"):
        source_name = uri.replace("datasource://", "")
        source_config = config_manager.get_data_source(source_name)
        return json.dumps(source_config, ensure_ascii=False, indent=2)

    else:
        raise ValueError(f"未知的资源URI: {uri}")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="list_tile_codes",
            description="列出数据库中所有已导入的图幅代码。**这是查询数据的第一步，必须首先执行！**图幅编号是全球通用的1:100万图幅编号（如F49、F50、G49、G50等），每个图幅覆盖约6°×4°的地理范围。在查询数据前，必须先使用此工具查看有哪些图幅可用，然后根据查询目的地的地理位置确定需要查询的图幅。例如：惠州市主要在F49和F50图幅，广州市主要在F49图幅，深圳市主要在F49和F50图幅。返回每个图幅代码及其在各表中的记录数统计。详细说明请查看docs/TILE_CODE_GUIDE.md。",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    }
                },
            },
        ),
        Tool(
            name="list_tables",
            description="列出PostgreSQL/PostGIS数据库中所有已导入的地理数据表。**这是查询数据的第二步，在list_tile_codes之后执行。**返回每个表的名称、用途说明、分类、记录数、坐标系(SRID)等信息。**重要提示：1)必须先使用list_tile_codes查看有哪些图幅。2)不要盲目猜测表名，必须使用此工具查看可用表。3)根据查询需求选择正确的表：查询行政区面积使用boua表（行政境界面，注意：只包含区/县/县级市，不包含地级市；同一行政区域可能被分割成多个记录，查询时必须使用GROUP BY name/pac和ST_Union(geom)合并），查询水系使用hyda/hydl/hydp表，查询道路使用lrdl表，查询居民地使用resa/resp表，查询植被使用vega表（可能包含自然保护区），查询区域界线使用brga表（可能包含自然保护区）。4)表名通常是小写的图层代码，如boua、hyda、lrdl等。5)单位转换：计算面积必须使用ST_Area(geom::geography)/1000000（shape_area是度²，不能直接转换），计算长度必须使用ST_Length(geom::geography)/1000（shape_length是度，不能直接转换）。详细表用途和单位转换说明请查看docs/TABLE_USAGE_GUIDE.md。**",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    }
                },
            },
        ),
        Tool(
            name="verify_import",
            description="验证PostgreSQL/PostGIS中已导入的数据，检查数据完整性、坐标系、几何有效性、空间范围等。**这是查询数据的第三步，在list_tables之后执行。**返回每个表的用途说明、分类、记录数、坐标系(SRID)、边界框(bbox)、无效几何数量、字段信息（包含字段说明）等。**这是了解表结构和字段含义的重要工具，在查询数据前必须先使用此工具查看表的用途和字段说明，不要猜测字段含义。**重要提示：1)返回结果包含表的description（用途说明）和category（分类），帮助选择正确的表。2)name字段在1:100万数据中经常为空，不能仅通过名称查询。3)需要使用空间范围(bbox)和图幅代码(tile_code)进行查询。4)查询行政区面积使用boua表（行政境界面），查询水系使用hyda/hydl/hydp表，查询道路使用lrdl表。详细字段说明请查看docs/FIELD_SPEC.md。",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "要验证的表名（可选，如果不提供则验证所有表）。建议先使用list_tables查看可用表。",
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    },
                },
            },
        ),
        Tool(
            name="query_data",
            description='查询PostgreSQL/PostGIS中的空间数据，支持空间过滤和属性过滤。返回匹配的记录，包括所有字段和几何对象（以WKT格式）。适用于简单的空间查询，如：按边界框查询、按几何相交查询、按属性过滤等。**重要：1)必须按顺序执行：先list_tile_codes→再list_tables→再verify_import→最后query_data。2)查询前必须先使用list_tile_codes查看有哪些图幅，然后根据目的地地理位置确定需要查询的图幅（不要只查F49），使用attribute_filter按tile_code过滤，例如{"tile_code": "F49"}或{"tile_code": ["F49", "F50"]}。3)查询前必须先使用list_tables和verify_import查看表的用途说明，选择正确的表：查询行政区面积使用boua表（注意：boua表只包含区/县/县级市，不包含地级市；同一行政区域可能被分割成多个记录，需要合并计算总面积），查询水系使用hyda/hydl/hydp表，查询道路使用lrdl表，查询居民地使用resa/resp表。4)name字段经常为空，不能仅通过名称查询，必须结合空间范围查询。**对于复杂的空间分析（如计算面积、距离、缓冲区、空间连接、合并同一行政区域的多个记录等），应使用execute_sql工具配合PostGIS函数。',
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "表名（必须先使用list_tables查看可用表）",
                    },
                    "spatial_filter": {
                        "type": "object",
                        "description": "空间过滤条件（可选）。支持边界框(bbox)或几何对象(geometry)过滤。",
                        "properties": {
                            "bbox": {
                                "type": "array",
                                "description": "边界框 [minx, miny, maxx, maxy]，单位为度（经纬度）",
                            },
                            "geometry": {
                                "type": "string",
                                "description": "WKT格式的几何对象，如 'POINT(113.3 23.1)' 或 'POLYGON((...))'",
                            },
                        },
                    },
                    "attribute_filter": {
                        "type": "object",
                        "description": '属性过滤条件（可选），键值对形式，如 {"tile_code": "F49"}',
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回记录数限制（默认100）",
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    },
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="execute_sql",
            description="在PostgreSQL/PostGIS数据库中执行SQL查询。这是进行复杂空间分析和计算的主要工具。支持所有PostGIS空间函数和WITH语句（CTE），如：ST_Area(计算面积)、ST_Distance(计算距离)、ST_Buffer(缓冲区)、ST_Intersects(相交判断)、ST_Within(包含判断)、ST_Union(合并)、ST_Intersection(求交)、ST_Centroid(中心点)、ST_Envelope(边界框)等。使用此工具可以进行：1)空间分析（面积、距离、缓冲区、空间关系判断）；2)空间计算（合并、求交、简化、转换坐标系）；3)复杂查询（多表连接、聚合统计、空间分组、WITH子查询）；4)数据统计（按区域统计、按图幅统计等）。**重要：1)必须按顺序执行：先list_tile_codes→再list_tables→再verify_import→最后execute_sql。2)查询前必须先使用list_tile_codes查看有哪些图幅，然后根据目的地地理位置确定需要查询的图幅（不要只查F49），在SQL中使用WHERE tile_code IN ('F49', 'F50', ...)过滤。3)查询前必须先使用list_tables和verify_import查看表的用途说明，选择正确的表：查询行政区面积使用boua表（注意：boua表只包含区/县/县级市，不包含地级市；同一行政区域可能被分割成多个记录，查询时需要使用GROUP BY name/pac和ST_Union(geom)合并计算总面积），查询水系使用hyda/hydl/hydp表，查询道路使用lrdl表，查询居民地使用resa/resp表，查询植被使用vega表，查询区域界线使用brga表。4)name字段经常为空，不能仅通过名称查询，必须结合空间范围查询。5)单位转换：计算面积必须使用ST_Area(geom::geography)/1000000转换为平方公里（shape_area字段是度²，不能直接转换）；计算长度必须使用ST_Length(geom::geography)/1000转换为公里（shape_length字段是度，不能直接转换）。6)查询boua表时，如果查询某个行政区域的完整面积，必须使用GROUP BY和ST_Union合并所有分割的部分。**注意：支持SELECT查询和WITH语句（CTE），不支持INSERT/UPDATE/DELETE/DROP/CREATE/ALTER等修改操作。详细表用途和单位转换说明请查看docs/TABLE_USAGE_GUIDE.md。",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的SQL SELECT语句或WITH语句（CTE）。可以使用PostGIS空间函数和WITH子查询，例如：计算面积使用 ST_Area(geom::geography)/1000000（转换为平方公里，注意：shape_area字段是度²，不能直接转换），计算距离使用 ST_Distance(geom1::geography, geom2::geography)/1000（转换为公里），计算长度使用 ST_Length(geom::geography)/1000（转换为公里，注意：shape_length字段是度，不能直接转换），空间过滤使用 ST_Intersects(geom1, geom2) 或 geom && ST_MakeEnvelope(...)。常用PostGIS函数：ST_Area(计算面积)、ST_Distance(计算距离)、ST_Length(计算长度)、ST_Buffer(缓冲区)、ST_Intersects(相交)、ST_Within(包含)、ST_Contains(包含)、ST_Overlaps(重叠)、ST_Union(合并)、ST_Intersection(求交)、ST_Centroid(中心点)、ST_Envelope(边界框)、ST_AsText(转为WKT)、ST_GeomFromText(从WKT创建)、ST_MakeEnvelope(创建边界框)、ST_Transform(坐标系转换)。支持WITH语句进行复杂查询，例如：WITH temp AS (SELECT ...) SELECT ... FROM temp。详细表用途和单位转换说明请查看docs/TABLE_USAGE_GUIDE.md。",
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    },
                },
                "required": ["sql"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """执行工具调用"""
    try:
        if name == "verify_import":
            result = await verify_import_handler(arguments)
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "query_data":
            result = await query_data_handler(arguments)
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "list_tables":
            result = await list_tables_handler(arguments)
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "list_tile_codes":
            result = await list_tile_codes_handler(arguments)
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "execute_sql":
            result = await execute_sql_handler(arguments)
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        else:
            raise ValueError(f"未知的工具: {name}")

    except Exception as e:
        logger.error(f"工具执行错误: {e}", exc_info=True)
        return [
            TextContent(
                type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False)
            )
        ]


async def verify_import_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理数据验证请求"""
    table_name = arguments.get("table_name")
    database_config = arguments.get("database_config")

    if not database_config:
        database_config = config_manager.get_default_database_config()

    result = await data_importer.verify_data(
        table_name=table_name, database_config=database_config
    )

    return result


async def query_data_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理数据查询请求"""
    table_name = arguments["table_name"]
    spatial_filter = arguments.get("spatial_filter")
    attribute_filter = arguments.get("attribute_filter")
    limit = arguments.get("limit", 100)
    database_config = arguments.get("database_config")

    if not database_config:
        database_config = config_manager.get_default_database_config()

    result = await data_importer.query_data(
        table_name=table_name,
        spatial_filter=spatial_filter,
        attribute_filter=attribute_filter,
        limit=limit,
        database_config=database_config,
    )

    return result


async def list_tile_codes_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理列出图幅代码请求"""
    database_config = arguments.get("database_config")

    if not database_config:
        database_config = config_manager.get_default_database_config()

    result = await data_importer.list_tile_codes(database_config=database_config)
    return result


async def list_tables_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理列出表请求"""
    database_config = arguments.get("database_config")

    if not database_config:
        database_config = config_manager.get_default_database_config()

    result = await data_importer.list_tables(database_config=database_config)
    return result


async def execute_sql_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理SQL执行请求"""
    sql = arguments["sql"]
    database_config = arguments.get("database_config")

    if not database_config:
        database_config = config_manager.get_default_database_config()

    result = await data_importer.execute_sql(sql=sql, database_config=database_config)
    return result


async def main():
    """主函数"""
    # 输出启动信息到stderr（MCP服务器使用stdio通信，stdout用于协议）
    import sys

    print("MCP服务器正在启动...", file=sys.stderr)
    print("等待MCP客户端连接...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        print("MCP服务器已就绪，开始处理请求...", file=sys.stderr)
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        import sys

        print("\nMCP服务器已停止", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        import sys

        print(f"错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
