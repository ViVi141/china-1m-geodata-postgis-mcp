"""
完全解析某一图幅的所有图层的所有字段，从零设计全新的表结构
"""

import fiona
import argparse
import json
from pathlib import Path
from collections import defaultdict
import sys
from typing import Dict, Any, List, Set


def get_postgresql_type(fiona_type: Any, field_name: str, sample_values: List[str]) -> str:
    """
    将Fiona字段类型映射到PostgreSQL类型
    根据实际数据优化类型选择
    """
    type_str = str(fiona_type)
    
    # 处理带长度的类型
    if ':' in type_str:
        base_type = type_str.split(':')[0]
        length = type_str.split(':')[1]
    else:
        base_type = type_str
        length = None
    
    base_type = base_type.lower()
    
    # 根据字段名和示例值推断更合适的类型
    field_name_upper = field_name.upper()
    
    # 特殊字段处理
    if 'ID' in field_name_upper or field_name_upper.endswith('_ID'):
        # ID字段，可能是整数或字符串
        if base_type in ['int', 'int32', 'int64']:
            return 'BIGINT'
        else:
            # 检查示例值，如果是数字字符串，可能需要VARCHAR
            if sample_values:
                try:
                    int(sample_values[0])
                    return 'VARCHAR(50)'  # ID可能是字符串格式的数字
                except:
                    pass
            return 'VARCHAR(100)'
    
    # 标准类型映射
    type_mapping = {
        'int': 'INTEGER',
        'int32': 'INTEGER',
        'int64': 'BIGINT',
        'float': 'DOUBLE PRECISION',
        'float32': 'REAL',
        'float64': 'DOUBLE PRECISION',
        'str': 'TEXT',
        'string': 'TEXT',
        'date': 'DATE',
        'time': 'TIME',
        'datetime': 'TIMESTAMP',
        'bool': 'BOOLEAN',
        'bytes': 'BYTEA'
    }
    
    pg_type = type_mapping.get(base_type, 'TEXT')
    
    # 如果是字符串类型，根据长度和示例值优化
    if pg_type == 'TEXT' or base_type in ['str', 'string']:
        if length:
            try:
                max_len = int(length)
                # 如果长度较小，使用VARCHAR；否则使用TEXT
                if max_len <= 255:
                    return f'VARCHAR({max_len})'
                elif max_len <= 1000:
                    return 'VARCHAR(1000)'
                else:
                    return 'TEXT'
            except:
                pass
        
        # 根据示例值推断长度
        if sample_values:
            max_sample_len = max(len(str(v)) for v in sample_values if v)
            if max_sample_len > 0:
                if max_sample_len <= 50:
                    return 'VARCHAR(50)'
                elif max_sample_len <= 100:
                    return 'VARCHAR(100)'
                elif max_sample_len <= 255:
                    return 'VARCHAR(255)'
                elif max_sample_len <= 500:
                    return 'VARCHAR(500)'
                else:
                    return 'TEXT'
    
    return pg_type


def analyze_field_completely(
    gdb_path: str,
    layer_name: str,
    field_name: str,
    field_type: Any,
    total_records: int
) -> Dict[str, Any]:
    """
    完全分析单个字段的所有信息
    """
    field_info = {
        "field_name": field_name,
        "original_type": str(field_type),
        "fiona_type": field_type,
        "total_records": total_records,
        "null_count": 0,
        "not_null_count": 0,
        "null_percentage": 0.0,
        "unique_values": set(),
        "sample_values": [],
        "min_value": None,
        "max_value": None,
        "avg_value": None,
        "value_lengths": [],
        "is_numeric": False,
        "is_integer": False,
        "is_float": False,
        "is_string": False,
        "is_date": False,
        "is_boolean": False,
        "max_length": 0,
        "min_length": None,
        "recommended_type": None,
        "recommended_constraints": []
    }
    
    try:
        with fiona.open(gdb_path, layer=layer_name) as src:
            numeric_values = []
            string_lengths = []
            
            for feature in src:
                props = feature.get('properties', {})
                value = props.get(field_name)
                
                if value is None:
                    field_info["null_count"] += 1
                else:
                    field_info["not_null_count"] += 1
                    field_info["unique_values"].add(str(value))
                    
                    # 数值分析
                    if isinstance(value, (int, float)):
                        field_info["is_numeric"] = True
                        numeric_values.append(value)
                        if isinstance(value, int):
                            field_info["is_integer"] = True
                        else:
                            field_info["is_float"] = True
                        
                        if field_info["min_value"] is None or value < field_info["min_value"]:
                            field_info["min_value"] = value
                        if field_info["max_value"] is None or value > field_info["max_value"]:
                            field_info["max_value"] = value
                    
                    # 字符串分析
                    elif isinstance(value, str):
                        field_info["is_string"] = True
                        str_len = len(value)
                        string_lengths.append(str_len)
                        if str_len > field_info["max_length"]:
                            field_info["max_length"] = str_len
                        if field_info["min_length"] is None or str_len < field_info["min_length"]:
                            field_info["min_length"] = str_len
                    
                    # 日期分析
                    elif isinstance(value, (type(None))):
                        pass
                    else:
                        # 尝试转换为字符串
                        str_value = str(value)
                        str_len = len(str_value)
                        string_lengths.append(str_len)
                        if str_len > field_info["max_length"]:
                            field_info["max_length"] = str_len
            
            # 计算统计信息
            if total_records > 0:
                field_info["null_percentage"] = (field_info["null_count"] / total_records) * 100
            
            # 数值统计
            if numeric_values:
                field_info["avg_value"] = sum(numeric_values) / len(numeric_values)
                field_info["value_lengths"] = sorted(set(numeric_values))
            
            # 字符串长度统计
            if string_lengths:
                field_info["value_lengths"] = sorted(set(string_lengths))
            
            # 收集示例值（最多20个不同的值）
            field_info["sample_values"] = sorted(list(field_info["unique_values"]))[:20]
            field_info["unique_count"] = len(field_info["unique_values"])
            field_info["unique_percentage"] = (len(field_info["unique_values"]) / total_records * 100) if total_records > 0 else 0
            
            # 推荐PostgreSQL类型
            sample_values_str = [str(v) for v in field_info["sample_values"]]
            field_info["recommended_type"] = get_postgresql_type(
                field_type, field_name, sample_values_str
            )
            
            # 推荐约束
            if field_info["null_percentage"] == 0:
                field_info["recommended_constraints"].append("NOT NULL")
            
            if field_info["unique_percentage"] == 100 and field_info["not_null_count"] > 0:
                field_info["recommended_constraints"].append("UNIQUE")
            
            # 如果是数值且有范围，可以考虑CHECK约束
            if field_info["is_numeric"] and field_info["min_value"] is not None and field_info["max_value"] is not None:
                if field_info["min_value"] >= 0:
                    field_info["recommended_constraints"].append(f"CHECK (>= {field_info['min_value']})")
    
    except Exception as e:
        field_info["error"] = str(e)
        import traceback
        field_info["traceback"] = traceback.format_exc()
    
    return field_info


def analyze_layer_completely(gdb_path: str, layer_name: str) -> Dict[str, Any]:
    """
    完全分析单个图层的所有信息
    """
    print(f"  正在分析图层: {layer_name}...")
    
    layer_info = {
        "layer_name": layer_name,
        "geometry_type": None,
        "crs": None,
        "total_records": 0,
        "fields": {},
        "field_count": 0,
        "has_geometry": 0,
        "null_geometry_count": 0
    }
    
    try:
        with fiona.open(gdb_path, layer=layer_name) as src:
            schema = src.schema
            layer_info["geometry_type"] = schema.get('geometry', 'Unknown')
            layer_info["crs"] = str(src.crs) if src.crs else None
            properties = schema.get('properties', {})
            layer_info["field_count"] = len(properties)
            
            # 先统计总记录数
            print(f"    统计记录数...")
            total_records = 0
            for _ in src:
                total_records += 1
            layer_info["total_records"] = total_records
            print(f"    总记录数: {total_records:,}")
            
            # 分析每个字段
            print(f"    分析 {len(properties)} 个字段...")
            for idx, (field_name, field_type) in enumerate(properties.items(), 1):
                print(f"      [{idx}/{len(properties)}] 分析字段: {field_name}")
                field_info = analyze_field_completely(
                    gdb_path, layer_name, field_name, field_type, total_records
                )
                layer_info["fields"][field_name] = field_info
            
            # 统计几何信息
            print(f"    统计几何信息...")
            with fiona.open(gdb_path, layer=layer_name) as src2:
                for feature in src2:
                    if feature.get('geometry'):
                        layer_info["has_geometry"] += 1
                    else:
                        layer_info["null_geometry_count"] += 1
    
    except Exception as e:
        layer_info["error"] = str(e)
        import traceback
        layer_info["traceback"] = traceback.format_exc()
        print(f"    [ERROR] 分析失败: {e}")
    
    return layer_info


def design_table_structure(layer_info: Dict[str, Any], table_name: str = None) -> Dict[str, Any]:
    """
    从零设计全新的表结构
    """
    if table_name is None:
        # 从图层名生成表名
        layer_name = layer_info["layer_name"]
        # 移除可能的图幅前缀
        if '_' in layer_name:
            layer_name = layer_name.split('_')[-1]
        table_name = layer_name.lower().replace('-', '_').replace('.', '_')
        # 确保符合PostgreSQL命名规范
        if table_name and table_name[0].isdigit():
            table_name = '_' + table_name
        if len(table_name) > 63:
            table_name = table_name[:63]
    
    table_design = {
        "table_name": table_name,
        "layer_name": layer_info["layer_name"],
        "geometry_type": layer_info.get("geometry_type"),
        "description": f"表 {table_name} 存储图层 {layer_info['layer_name']} 的数据",
        "columns": [],
        "indexes": [],
        "constraints": [],
        "create_sql": ""
    }
    
    # 1. 主键列
    table_design["columns"].append({
        "name": "id",
        "type": "BIGSERIAL",
        "constraints": ["PRIMARY KEY"],
        "description": "主键，自动递增的唯一标识符"
    })
    
    # 2. 几何列
    geom_type = layer_info.get("geometry_type", "Unknown")
    if geom_type and geom_type != "Unknown" and geom_type != "None":
        # 映射几何类型
        pg_geom_type = {
            "Point": "POINT",
            "LineString": "LINESTRING",
            "Polygon": "POLYGON",
            "MultiPoint": "MULTIPOINT",
            "MultiLineString": "MULTILINESTRING",
            "MultiPolygon": "MULTIPOLYGON",
            "GeometryCollection": "GEOMETRYCOLLECTION"
        }.get(geom_type, "GEOMETRY")
        
        table_design["columns"].append({
            "name": "geom",
            "type": f"GEOMETRY({pg_geom_type}, 4326)",
            "constraints": [],
            "description": f"PostGIS几何对象，类型: {geom_type}",
            "index": "GIST"
        })
    
    # 3. 图幅代码列
    table_design["columns"].append({
        "name": "tile_code",
        "type": "VARCHAR(10)",
        "constraints": ["NOT NULL"],
        "description": "图幅代码，1:100万图幅编号（如F49、F50等）",
        "index": "BTREE"
    })
    
    # 4. 数据字段
    fields = layer_info.get("fields", {})
    for field_name, field_info in fields.items():
        # 清理字段名，符合PostgreSQL规范
        clean_name = field_name.lower().replace('-', '_').replace('.', '_').replace(' ', '_')
        if clean_name and clean_name[0].isdigit():
            clean_name = '_' + clean_name
        if len(clean_name) > 63:
            clean_name = clean_name[:63]
        
        # 避免与系统列名冲突
        if clean_name in ['id', 'geom', 'tile_code']:
            clean_name = f"{clean_name}_field"
        
        column = {
            "name": clean_name,
            "original_name": field_name,
            "type": field_info.get("recommended_type", "TEXT"),
            "constraints": field_info.get("recommended_constraints", []),
            "description": f"原始字段: {field_name}",
            "null_percentage": field_info.get("null_percentage", 0),
            "unique_percentage": field_info.get("unique_percentage", 0),
            "sample_values": field_info.get("sample_values", [])[:5]
        }
        
        # 添加详细统计信息
        if field_info.get("is_numeric"):
            column["statistics"] = {
                "min": field_info.get("min_value"),
                "max": field_info.get("max_value"),
                "avg": field_info.get("avg_value")
            }
        
        if field_info.get("is_string") and field_info.get("max_length"):
            column["max_length"] = field_info.get("max_length")
        
        table_design["columns"].append(column)
    
    # 5. 时间戳列（可选，用于数据管理）
    table_design["columns"].append({
        "name": "created_at",
        "type": "TIMESTAMP",
        "constraints": ["DEFAULT CURRENT_TIMESTAMP"],
        "description": "记录创建时间"
    })
    
    table_design["columns"].append({
        "name": "updated_at",
        "type": "TIMESTAMP",
        "constraints": ["DEFAULT CURRENT_TIMESTAMP"],
        "description": "记录更新时间"
    })
    
    # 6. 生成CREATE TABLE SQL
    sql_parts = [f"CREATE TABLE {table_name} ("]
    
    column_defs = []
    for col in table_design["columns"]:
        col_def = f"    {col['name']} {col['type']}"
        
        # 添加约束
        if col.get("constraints"):
            col_def += " " + " ".join(col["constraints"])
        
        # 添加注释
        if col.get("description"):
            col_def += f"  -- {col['description']}"
        
        column_defs.append(col_def)
    
    sql_parts.append(",\n".join(column_defs))
    sql_parts.append(");")
    
    # 7. 添加索引
    index_sql = []
    for col in table_design["columns"]:
        if col.get("index"):
            index_type = col["index"]
            index_name = f"{table_name}_{col['name']}_idx"
            if index_type == "GIST":
                index_sql.append(
                    f"CREATE INDEX {index_name} ON {table_name} USING GIST ({col['name']});"
                )
            else:
                index_sql.append(
                    f"CREATE INDEX {index_name} ON {table_name} ({col['name']});"
                )
    
    # 8. 添加表注释
    comment_sql = f"COMMENT ON TABLE {table_name} IS '{table_design['description']}';"
    
    # 9. 添加列注释
    column_comments = []
    for col in table_design["columns"]:
        if col.get("description"):
            comment = col["description"].replace("'", "''")
            column_comments.append(
                f"COMMENT ON COLUMN {table_name}.{col['name']} IS '{comment}';"
            )
    
    # 组合完整的SQL
    full_sql = "\n".join(sql_parts)
    if index_sql:
        full_sql += "\n\n-- 索引\n" + "\n".join(index_sql)
    if comment_sql:
        full_sql += "\n\n-- 表注释\n" + comment_sql
    if column_comments:
        full_sql += "\n\n-- 列注释\n" + "\n".join(column_comments)
    
    table_design["create_sql"] = full_sql
    table_design["indexes"] = index_sql
    table_design["constraints"] = [c for col in table_design["columns"] for c in col.get("constraints", [])]
    
    return table_design


def parse_tile_completely(gdb_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    完全解析图幅的所有图层和字段
    """
    print("=" * 80)
    print(f"完全解析图幅: {gdb_path}")
    print("=" * 80)
    
    gdb_file = Path(gdb_path)
    if not gdb_file.exists():
        print(f"错误: 文件不存在: {gdb_path}")
        return None
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path("analysis")
        output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        layers = fiona.listlayers(gdb_path)
        if not layers:
            print("错误: 未找到任何图层")
            return None
        
        print(f"\n找到 {len(layers)} 个图层\n")
        
        tile_code = gdb_file.stem.replace('.gdb', '')
        
        result = {
            "tile_code": tile_code,
            "gdb_path": str(gdb_path),
            "total_layers": len(layers),
            "layers": [],
            "table_designs": []
        }
        
        # 分析每个图层
        for idx, layer_name in enumerate(layers, 1):
            print(f"\n[{idx}/{len(layers)}] 分析图层: {layer_name}")
            print("-" * 80)
            
            layer_info = analyze_layer_completely(gdb_path, layer_name)
            result["layers"].append(layer_info)
            
            if "error" not in layer_info:
                print(f"  [完成] 几何类型: {layer_info['geometry_type']}")
                print(f"  [完成] 字段数: {layer_info['field_count']}")
                print(f"  [完成] 记录数: {layer_info['total_records']:,}")
                
                # 设计表结构
                print(f"  [设计] 生成表结构...")
                table_design = design_table_structure(layer_info)
                result["table_designs"].append(table_design)
                print(f"  [完成] 表名: {table_design['table_name']}")
                print(f"  [完成] 列数: {len(table_design['columns'])}")
        
        # 保存完整分析结果
        json_file = output_path / f"{tile_code}_complete_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n完整分析结果已保存到: {json_file}")
        
        # 保存表结构设计
        sql_file = output_path / f"{tile_code}_table_designs.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(f"-- {tile_code} 图幅表结构设计\n")
            f.write(f"-- 生成时间: {Path(__file__).stat().st_mtime}\n")
            f.write(f"-- 图层数: {len(result['table_designs'])}\n\n")
            
            for table_design in result["table_designs"]:
                f.write(f"\n-- ========================================\n")
                f.write(f"-- 表: {table_design['table_name']}\n")
                f.write(f"-- 图层: {table_design['layer_name']}\n")
                f.write(f"-- 描述: {table_design['description']}\n")
                f.write(f"-- ========================================\n\n")
                f.write(table_design["create_sql"])
                f.write("\n\n")
        
        print(f"表结构设计SQL已保存到: {sql_file}")
        
        # 生成表结构摘要
        summary_file = output_path / f"{tile_code}_table_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# {tile_code} 图幅表结构设计摘要\n\n")
            f.write(f"**图幅代码**: {tile_code}\n\n")
            f.write(f"**图层数**: {len(result['table_designs'])}\n\n")
            f.write(f"**总表数**: {len(result['table_designs'])}\n\n")
            f.write("## 表列表\n\n")
            
            for table_design in result["table_designs"]:
                f.write(f"### {table_design['table_name']}\n\n")
                f.write(f"- **图层名**: {table_design['layer_name']}\n")
                f.write(f"- **几何类型**: {table_design.get('geometry_type', 'N/A')}\n")
                f.write(f"- **列数**: {len(table_design['columns'])}\n")
                f.write(f"- **索引数**: {len(table_design['indexes'])}\n\n")
                
                f.write("#### 列信息\n\n")
                f.write("| 列名 | 类型 | 约束 | 空值率 | 说明 |\n")
                f.write("|------|------|------|--------|------|\n")
                
                for col in table_design["columns"]:
                    constraints = ", ".join(col.get("constraints", []))
                    null_pct = col.get("null_percentage", 0)
                    desc = col.get("description", "")
                    f.write(f"| {col['name']} | {col['type']} | {constraints} | {null_pct:.1f}% | {desc} |\n")
                
                f.write("\n")
        
        print(f"表结构摘要已保存到: {summary_file}")
        
        return result
    
    except Exception as e:
        print(f"错误: 无法解析GDB文件: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="完全解析某一图幅的所有图层的所有字段，从零设计全新的表结构"
    )
    parser.add_argument('gdb_path', nargs='?', help='GDB文件路径')
    parser.add_argument('--output', '-o', dest='output_dir', help='输出目录（默认: analysis/）')
    
    args = parser.parse_args()
    
    if not args.gdb_path:
        # 默认检查当前目录下的GDB文件
        gdb_files = ['F49.gdb', 'G49.gdb', 'G50.gdb', 'F50.gdb']
        available = [f for f in gdb_files if Path(f).exists()]
        
        if not available:
            print("错误: 未找到GDB文件")
            print("用法: python scripts/parse_tile_schema.py <gdb_path> [--output output_dir]")
            sys.exit(1)
        
        args.gdb_path = available[0]
        print(f"使用默认文件: {args.gdb_path}\n")
    
    result = parse_tile_completely(args.gdb_path, args.output_dir)
    
    if result:
        print("\n" + "=" * 80)
        print("解析完成！")
        print("=" * 80)
        print(f"图层数: {result['total_layers']}")
        print(f"表设计数: {len(result['table_designs'])}")
        sys.exit(0)
    else:
        print("\n解析失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()

