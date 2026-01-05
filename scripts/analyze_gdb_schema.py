"""
分析GDB图层的详细结构
包括字段名称、类型、示例值等，用于生成准确的字段说明文档
"""

import fiona
import argparse
import json
from pathlib import Path
from collections import defaultdict
import sys


def analyze_layer_schema(gdb_path, layer_name, sample_size=100):
    """分析单个图层的详细结构"""
    result = {
        "layer_name": layer_name,
        "geometry_type": None,
        "fields": {},
        "sample_values": {},
        "field_statistics": {}
    }
    
    try:
        with fiona.open(gdb_path, layer=layer_name) as src:
            schema = src.schema
            result["geometry_type"] = schema.get('geometry', 'Unknown')
            properties = schema.get('properties', {})
            
            # 分析字段
            for field_name, field_type in properties.items():
                result["fields"][field_name] = {
                    "type": str(field_type),
                    "fiona_type": field_type
                }
            
            # 采样数据，分析字段的实际值
            sample_values = defaultdict(set)
            field_counts = defaultdict(int)
            null_counts = defaultdict(int)
            
            count = 0
            for feature in src:
                count += 1
                props = feature.get('properties', {})
                
                for field_name in properties.keys():
                    value = props.get(field_name)
                    
                    if value is None:
                        null_counts[field_name] += 1
                    else:
                        field_counts[field_name] += 1
                        # 收集示例值（最多10个不同的值）
                        if len(sample_values[field_name]) < 10:
                            sample_values[field_name].add(str(value))
                
                if count >= sample_size:
                    break
            
            # 构建字段统计信息
            for field_name in properties.keys():
                result["field_statistics"][field_name] = {
                    "has_value_count": field_counts[field_name],
                    "null_count": null_counts[field_name],
                    "null_percentage": (null_counts[field_name] / count * 100) if count > 0 else 0,
                    "sample_values": sorted(list(sample_values[field_name]))[:10]
                }
            
            result["total_samples"] = count
            
    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
    
    return result


def analyze_gdb(gdb_path, output_file=None):
    """分析GDB文件的所有图层"""
    print("=" * 80)
    print(f"分析GDB文件: {gdb_path}")
    print("=" * 80)
    
    gdb_file = Path(gdb_path)
    if not gdb_file.exists():
        print(f"错误: 文件不存在: {gdb_path}")
        return None
    
    try:
        layers = fiona.listlayers(gdb_path)
        if not layers:
            print("错误: 未找到任何图层")
            return None
        
        print(f"\n找到 {len(layers)} 个图层\n")
        
        all_results = {
            "gdb_path": str(gdb_path),
            "layers": []
        }
        
        for layer_name in layers:
            print(f"分析图层: {layer_name}...")
            layer_result = analyze_layer_schema(gdb_path, layer_name, sample_size=1000)
            all_results["layers"].append(layer_result)
            
            # 显示摘要
            if "error" not in layer_result:
                print(f"  [OK] 几何类型: {layer_result['geometry_type']}")
                print(f"  [OK] 字段数: {len(layer_result['fields'])}")
                print(f"  [OK] 采样记录数: {layer_result.get('total_samples', 0)}")
                print()
            else:
                print(f"  [ERROR] 错误: {layer_result['error']}\n")
        
        # 保存结果
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"分析结果已保存到: {output_file}")
        
        # 生成字段说明摘要
        print("\n" + "=" * 80)
        print("字段说明摘要")
        print("=" * 80)
        
        for layer_result in all_results["layers"]:
            if "error" in layer_result:
                continue
            
            layer_name = layer_result["layer_name"]
            print(f"\n图层: {layer_name}")
            print("-" * 80)
            
            for field_name, field_info in layer_result["fields"].items():
                stats = layer_result["field_statistics"].get(field_name, {})
                null_pct = stats.get("null_percentage", 0)
                samples = stats.get("sample_values", [])
                
                print(f"  {field_name}:")
                print(f"    类型: {field_info['type']}")
                print(f"    空值率: {null_pct:.1f}%")
                if samples:
                    print(f"    示例值: {', '.join(samples[:5])}")
                print()
        
        return all_results
    
    except Exception as e:
        print(f"错误: 无法读取GDB文件: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分析GDB图层的详细结构")
    parser.add_argument('gdb_path', nargs='?', help='GDB文件路径')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    parser.add_argument('--dir', '-d', dest='gdb_dir', help='包含GDB文件的目录（批量分析）')
    
    args = parser.parse_args()
    
    # 确定GDB路径
    gdb_path = args.gdb_dir if args.gdb_dir else args.gdb_path
    
    if not gdb_path:
        # 默认检查当前目录下的GDB文件
        gdb_files = ['F49.gdb', 'G49.gdb', 'G50.gdb', 'F50.gdb']
        available = [f for f in gdb_files if Path(f).exists()]
        
        if not available:
            print("错误: 未找到GDB文件")
            print("用法: python scripts/analyze_gdb_schema.py <gdb_path> [--output output.json]")
            print("  或: python scripts/analyze_gdb_schema.py --dir <directory>")
            sys.exit(1)
        
        gdb_path = available[0]
        print(f"使用默认文件: {gdb_path}\n")
    
    # 处理单个文件或目录
    gdb_path_obj = Path(gdb_path)
    
    if gdb_path_obj.is_file() or (gdb_path_obj.is_dir() and gdb_path_obj.suffix == '.gdb'):
        # 单个GDB文件
        output_file = args.output or f"{gdb_path_obj.stem}_schema.json"
        result = analyze_gdb(gdb_path, output_file)
        sys.exit(0 if result else 1)
    elif gdb_path_obj.is_dir():
        # 目录，批量分析
        gdb_files = [p for p in gdb_path_obj.glob("*.gdb") if p.is_dir()]
        if not gdb_files:
            print(f"错误: 目录中未找到GDB文件: {gdb_path}")
            sys.exit(1)
        
        print(f"找到 {len(gdb_files)} 个GDB文件，开始批量分析...\n")
        all_success = True
        
        for gdb_file in sorted(gdb_files):
            output_file = args.output or f"{gdb_file.stem}_schema.json"
            if not analyze_gdb(str(gdb_file), output_file):
                all_success = False
            print("\n" + "=" * 80 + "\n")
        
        sys.exit(0 if all_success else 1)
    else:
        print(f"错误: 无效的路径: {gdb_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()

