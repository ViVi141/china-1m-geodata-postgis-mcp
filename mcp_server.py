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
from mcp.types import (
    Resource,
    Tool,
    TextContent
)

from core.data_importer import DataImporter
from core.config_manager import ConfigManager
from core.spec_loader import SpecLoader

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
app = Server("china-1m-geodata-postgis-mcp")

# 初始化核心组件
config_manager = ConfigManager()
spec_loader = SpecLoader()
data_importer = DataImporter()


@app.list_resources()
async def list_resources() -> List[Resource]:
    """列出可用的资源"""
    resources = []
    
    # 列出可用的数据规格配置
    specs = spec_loader.list_specs()
    for spec_name in specs:
        resources.append(Resource(
            uri=f"spec://{spec_name}",
            name=f"数据规格: {spec_name}",
            description=f"数据规格配置: {spec_name}",
            mimeType="application/json"
        ))
    
    # 列出可用的数据源
    data_sources = config_manager.list_data_sources()
    for source_name in data_sources:
        resources.append(Resource(
            uri=f"datasource://{source_name}",
            name=f"数据源: {source_name}",
            description=f"已配置的数据源: {source_name}",
            mimeType="application/json"
        ))
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri.startswith("spec://"):
        spec_name = uri.replace("spec://", "")
        spec = spec_loader.load_spec(spec_name)
        return json.dumps(spec, ensure_ascii=False, indent=2)
    
    elif uri.startswith("datasource://"):
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
            name="import_geodata",
            description="导入地理数据到PostgreSQL/PostGIS数据库。数据将被导入到PostgreSQL中以便高性能查询和分析。支持GDB格式。",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_path": {
                        "type": "string",
                        "description": "GDB文件路径（.gdb目录）"
                    },
                    "spec_name": {
                        "type": "string",
                        "description": "数据规格名称（可选，如果不提供则自动检测）"
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选，如果不提供则使用默认配置）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    },
                    "options": {
                        "type": "object",
                        "description": "导入选项",
                        "properties": {
                            "srid": {"type": "integer", "description": "目标坐标系SRID（默认4326）"},
                            "batch_size": {"type": "integer", "description": "批量插入大小（默认1000）"},
                            "skip_invalid": {"type": "boolean", "description": "跳过无效几何（默认true）"},
                            "create_indexes": {"type": "boolean", "description": "创建索引（默认true）"}
                        }
                    }
                },
                "required": ["data_path"]
            }
        ),
        Tool(
            name="verify_import",
            description="验证已导入的数据，检查数据完整性、坐标系、几何有效性等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "要验证的表名（可选，如果不提供则验证所有表）"
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                }
            }
        ),
        Tool(
            name="list_specs",
            description="列出所有可用的数据规格配置。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_spec",
            description="获取指定数据规格的详细信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_name": {
                        "type": "string",
                        "description": "数据规格名称"
                    }
                },
                "required": ["spec_name"]
            }
        ),
        Tool(
            name="query_data",
            description="查询已导入的地理数据。",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "表名"
                    },
                    "spatial_filter": {
                        "type": "object",
                        "description": "空间过滤条件（可选）",
                        "properties": {
                            "bbox": {
                                "type": "array",
                                "description": "边界框 [minx, miny, maxx, maxy]"
                            },
                            "geometry": {
                                "type": "string",
                                "description": "WKT格式的几何对象"
                            }
                        }
                    },
                    "attribute_filter": {
                        "type": "object",
                        "description": "属性过滤条件（可选）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回记录数限制（默认100）"
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="register_spec",
            description="注册新的数据规格配置。",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_name": {
                        "type": "string",
                        "description": "数据规格名称"
                    },
                    "spec_config": {
                        "type": "object",
                        "description": "数据规格配置（JSON对象）"
                    }
                },
                "required": ["spec_name", "spec_config"]
            }
        ),
        Tool(
            name="list_tables",
            description="列出PostgreSQL数据库中所有已导入的地理数据表。",
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
                            "password": {"type": "string"}
                        }
                    }
                }
            }
        ),
        Tool(
            name="execute_sql",
            description="在PostgreSQL数据库中执行SQL查询。用于复杂查询和分析。",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的SQL语句"
                    },
                    "database_config": {
                        "type": "object",
                        "description": "数据库连接配置（可选）",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"},
                            "database": {"type": "string"},
                            "user": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                },
                "required": ["sql"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """执行工具调用"""
    try:
        if name == "import_geodata":
            result = await import_geodata_handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "verify_import":
            result = await verify_import_handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "list_specs":
            specs = spec_loader.list_specs()
            return [TextContent(type="text", text=json.dumps({"specs": specs}, ensure_ascii=False, indent=2))]
        
        elif name == "get_spec":
            spec_name = arguments.get("spec_name")
            spec = spec_loader.load_spec(spec_name)
            return [TextContent(type="text", text=json.dumps(spec, ensure_ascii=False, indent=2))]
        
        elif name == "query_data":
            result = await query_data_handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "register_spec":
            spec_name = arguments.get("spec_name")
            spec_config = arguments.get("spec_config")
            spec_loader.save_spec(spec_name, spec_config)
            return [TextContent(type="text", text=json.dumps({"status": "success", "message": f"数据规格 '{spec_name}' 已注册"}, ensure_ascii=False))]
        
        elif name == "list_tables":
            result = await list_tables_handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "execute_sql":
            result = await execute_sql_handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        else:
            raise ValueError(f"未知的工具: {name}")
    
    except Exception as e:
        logger.error(f"工具执行错误: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


async def import_geodata_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理数据导入请求"""
    data_path = arguments["data_path"]
    spec_name = arguments.get("spec_name")
    database_config = arguments.get("database_config")
    options = arguments.get("options", {})
    
    # 如果没有提供数据库配置，使用默认配置
    if not database_config:
        database_config = config_manager.get_default_database_config()
    
    # 执行导入
    result = await data_importer.import_data(
        data_path=data_path,
        spec_name=spec_name,
        database_config=database_config,
        options=options
    )
    
    return result


async def verify_import_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理数据验证请求"""
    table_name = arguments.get("table_name")
    database_config = arguments.get("database_config")
    
    if not database_config:
        database_config = config_manager.get_default_database_config()
    
    result = await data_importer.verify_data(
        table_name=table_name,
        database_config=database_config
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
        database_config=database_config
    )
    
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
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


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

