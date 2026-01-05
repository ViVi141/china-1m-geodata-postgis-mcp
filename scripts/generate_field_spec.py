"""
基于GDB图层分析结果生成字段说明文档
"""

import json
from pathlib import Path
import sys


def load_spec():
    """加载数据规格配置"""
    spec_path = Path("specs/china_1m_2021.json")
    if not spec_path.exists():
        print(f"错误: 找不到规格文件: {spec_path}")
        return None
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_analysis_result(analysis_file):
    """加载分析结果"""
    analysis_path = Path(analysis_file)
    if not analysis_path.exists():
        print(f"错误: 找不到分析结果文件: {analysis_path}")
        return None
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_field_description(layer_name, field_name, field_info, stats):
    """根据字段信息生成描述"""
    field_type = field_info.get('type', '')
    null_pct = stats.get('null_percentage', 0)
    samples = stats.get('sample_values', [])
    
    descriptions = {
        # 通用字段
        'GB': 'GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码',
        'PAC': '属性分类代码（Property Attribute Code），用于标识要素的分类',
        'NAME': '名称字段，存储要素的中文名称（可能为空）',
        'PINYIN': '拼音字段，存储名称的拼音（通常为空）',
        'SHAPE_Length': '几何形状的边界长度（度），使用PostGIS的ST_Length计算',
        'SHAPE_Area': '几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里',
        
        # 水系相关
        'HYDC': '水系代码（Hydrography Code），用于标识水系要素的唯一代码',
        'PERIOD': '时期/时段信息，如河流的丰水期、枯水期等',
        'VOL': '容量/规模，如水库的容量等级（大、中、小）',
        
        # 交通相关
        'RN': '路线编号（Route Number），如国道、省道编号',
        'RTEG': '道路等级（Road Grade），如一级、二级、三级、四级、等外',
        'TYPE': '类型字段，存储要素的类型分类',
        'BRGLEV': '桥梁等级（Bridge Level），1表示一级，2表示二级等',
        'ANGLE': '角度，用于标注要素的旋转角度（度）',
        
        # 地名相关
        'CLASS': '分类代码，用于标识地名或要素的分类',
        'GNID': '地名ID（Geographic Name ID），12位数字代码',
        'XZNAME': '行政名称，所属行政区划名称',
        
        # 境界相关
        'BNO': '边界编号（Boundary Number），用于标识边界点',
        
        # 地貌相关
        'ELEV': '高程值（Elevation），单位：米',
    }
    
    # 如果有预定义描述，使用它
    if field_name in descriptions:
        desc = descriptions[field_name]
    else:
        # 根据字段类型和示例值推断
        if field_type.startswith('str'):
            desc = f'字符串字段，最大长度{field_type.split(":")[1] if ":" in field_type else "未知"}'
        elif field_type == 'int32':
            desc = '整数字段（32位）'
        elif field_type == 'float':
            desc = '浮点数字段'
        else:
            desc = f'字段类型: {field_type}'
    
    # 添加空值率信息
    if null_pct > 50:
        desc += f'（注意：空值率{null_pct:.1f}%，该字段可能经常为空）'
    elif null_pct > 0:
        desc += f'（空值率{null_pct:.1f}%）'
    
    # 添加示例值
    if samples and len(samples) > 0 and len(samples) <= 5:
        sample_str = '、'.join(samples[:5])
        desc += f'，示例值：{sample_str}'
    
    return desc


def generate_field_spec(analysis_file, output_file):
    """生成字段说明文档"""
    spec = load_spec()
    if not spec:
        return False
    
    analysis = load_analysis_result(analysis_file)
    if not analysis:
        return False
    
    layer_mapping = spec.get('layer_mapping', {})
    
    # 按类别组织图层
    categories = {}
    for layer_code, layer_info in layer_mapping.items():
        category = layer_info.get('category', '其他')
        if category not in categories:
            categories[category] = []
        categories[category].append({
            'layer_code': layer_code,
            'table_name': layer_info.get('table_name'),
            'description': layer_info.get('description')
        })
    
    # 查找分析结果中的图层数据
    layer_data = {}
    for layer_result in analysis.get('layers', []):
        layer_name = layer_result.get('layer_name')
        if layer_name:
            layer_data[layer_name] = layer_result
    
    # 生成文档
    lines = []
    lines.append("# 数据字段说明")
    lines.append("")
    lines.append("本文档基于实际GDB图层分析结果生成，详细说明1:100万基础地理信息数据中所有表的字段含义，帮助LLM正确理解和使用字段。")
    lines.append("")
    lines.append("## 通用字段")
    lines.append("")
    lines.append("所有表都包含以下通用字段：")
    lines.append("")
    lines.append("| 字段名 | 类型 | 说明 |")
    lines.append("|--------|------|------|")
    lines.append("| `id` | INTEGER | 主键，自动递增的唯一标识符 |")
    lines.append("| `geom` | GEOMETRY | PostGIS几何对象，存储空间数据（点、线、面） |")
    lines.append("| `tile_code` | VARCHAR(10) | 图幅代码，1:100万图幅编号（如F49、F50、G49、G50等） |")
    lines.append("")
    lines.append("## 各表字段说明")
    lines.append("")
    
    # 按类别输出
    for category in sorted(categories.keys()):
        lines.append(f"### {category}")
        lines.append("")
        
        for layer_info in sorted(categories[category], key=lambda x: x['table_name']):
            layer_code = layer_info['layer_code']
            table_name = layer_info['table_name']
            description = layer_info['description']
            
            lines.append(f"#### {table_name} ({description})")
            lines.append("")
            
            # 查找对应的图层数据
            layer_result = layer_data.get(layer_code)
            if not layer_result:
                lines.append(f"*注：图层 {layer_code} 的分析数据未找到*")
                lines.append("")
                continue
            
            fields = layer_result.get('fields', {})
            field_stats = layer_result.get('field_statistics', {})
            geometry_type = layer_result.get('geometry_type', 'Unknown')
            
            lines.append(f"**几何类型**: {geometry_type}")
            lines.append("")
            lines.append("| 字段名 | 类型 | 说明 |")
            lines.append("|--------|------|------|")
            
            # 输出字段
            for field_name, field_info in sorted(fields.items()):
                stats = field_stats.get(field_name, {})
                field_desc = get_field_description(layer_code, field_name, field_info, stats)
                field_type = field_info.get('type', '')
                
                # 转换类型显示
                if field_type.startswith('str'):
                    max_len = field_type.split(':')[1] if ':' in field_type else ''
                    pg_type = f"VARCHAR({max_len})" if max_len else "TEXT"
                elif field_type == 'int32':
                    pg_type = "INTEGER"
                elif field_type == 'float':
                    pg_type = "DOUBLE PRECISION"
                else:
                    pg_type = field_type
                
                lines.append(f"| `{field_name.lower()}` | {pg_type} | {field_desc} |")
            
            lines.append("")
            
            # 添加使用提示
            has_name = 'NAME' in fields or 'name' in [f.lower() for f in fields.keys()]
            if has_name:
                name_stats = field_stats.get('NAME', {}) or field_stats.get('name', {})
                if name_stats and name_stats.get('null_percentage', 0) > 50:
                    lines.append("**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。")
                    lines.append("")
    
    # 写入文件
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"字段说明文档已生成: {output_path}")
    return True


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python scripts/generate_field_spec.py <analysis_json> [output_file]")
        print("  示例: python scripts/generate_field_spec.py analysis/F49_schema.json docs/FIELD_SPEC.md")
        sys.exit(1)
    
    analysis_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "docs/FIELD_SPEC.md"
    
    if generate_field_spec(analysis_file, output_file):
        print("生成成功！")
        sys.exit(0)
    else:
        print("生成失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()

