"""
检查GDB文件中的图层信息
支持指定单个GDB文件或目录（批量检查）
"""

import fiona
import argparse
from pathlib import Path
import sys

def check_layers(gdb_path):
    """检查GDB文件中的图层"""
    print("=" * 60)
    print(f"检查GDB文件: {gdb_path}")
    print("=" * 60)
    
    gdb_file = Path(gdb_path)
    if not gdb_file.exists():
        print(f"错误: 文件不存在: {gdb_path}")
        return False
    
    try:
        layers = fiona.listlayers(gdb_path)
        if not layers:
            print("错误: 未找到任何图层")
            return False
        
        print(f"\n找到 {len(layers)} 个图层:\n")
        
        for layer_name in layers:
            try:
                with fiona.open(gdb_path, layer=layer_name) as src:
                    schema = src.schema
                    geom_type = schema.get('geometry', 'Unknown')
                    properties = schema.get('properties', {})
                    
                    # 统计记录数
                    count = 0
                    has_geometry = 0
                    has_null_geometry = 0
                    
                    try:
                        for feature in src:
                            count += 1
                            if feature.get('geometry'):
                                has_geometry += 1
                            else:
                                has_null_geometry += 1
                            
                            # 只统计前1000条，避免太慢
                            if count >= 1000:
                                break
                    except Exception as e:
                        print(f"  [WARN] 读取记录时出错: {e}")
                    
                    print(f"图层: {layer_name}")
                    print(f"  几何类型: {geom_type}")
                    print(f"  字段数: {len(properties)}")
                    if count < 1000:
                        print(f"  记录数: {count}")
                        print(f"  有几何: {has_geometry}, 无几何: {has_null_geometry}")
                    else:
                        print(f"  记录数: >= {count} (仅检查前1000条)")
                    print()
            
            except Exception as e:
                print(f"图层: {layer_name}")
                print(f"  [ERROR] 无法读取: {e}")
                print()
        
        return True
    
    except Exception as e:
        print(f"错误: 无法读取GDB文件: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查GDB文件中的图层信息")
    parser.add_argument('gdb_path', nargs='?', help='GDB文件路径或包含GDB文件的目录')
    parser.add_argument('--dir', '-d', dest='gdb_dir', help='包含GDB文件的目录（批量检查）')
    
    args = parser.parse_args()
    
    # 确定GDB路径
    gdb_path = args.gdb_dir if args.gdb_dir else args.gdb_path
    
    if not gdb_path:
        # 默认检查当前目录下的GDB文件
        gdb_files = ['F49.gdb', 'G49.gdb', 'G50.gdb', 'F50.gdb']
        available = [f for f in gdb_files if Path(f).exists()]
        
        if not available:
            print("错误: 未找到GDB文件")
            print("用法: python scripts/check_layers.py <gdb_path>")
            print("  或: python scripts/check_layers.py --dir <directory>")
            sys.exit(1)
        
        gdb_path = available[0]
        print(f"使用默认文件: {gdb_path}\n")
    
    # 处理单个文件或目录
    gdb_path_obj = Path(gdb_path)
    
    if gdb_path_obj.is_file() or (gdb_path_obj.is_dir() and gdb_path_obj.suffix == '.gdb'):
        # 单个GDB文件
        success = check_layers(gdb_path)
        sys.exit(0 if success else 1)
    elif gdb_path_obj.is_dir():
        # 目录，批量检查
        gdb_files = [p for p in gdb_path_obj.glob("*.gdb") if p.is_dir()]
        if not gdb_files:
            print(f"错误: 目录中未找到GDB文件: {gdb_path}")
            sys.exit(1)
        
        print(f"找到 {len(gdb_files)} 个GDB文件，开始批量检查...\n")
        all_success = True
        
        for gdb_file in sorted(gdb_files):
            if not check_layers(str(gdb_file)):
                all_success = False
            print("\n" + "=" * 60 + "\n")
        
        sys.exit(0 if all_success else 1)
    else:
        print(f"错误: 无效的路径: {gdb_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()

