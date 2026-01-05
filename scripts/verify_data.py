"""
验证导入的数据
"""

import asyncio
import sys
from core.data_importer import DataImporter
from core.config_manager import ConfigManager

async def verify_data():
    """验证导入的数据"""
    print("=" * 60)
    print("验证导入的数据")
    print("=" * 60)
    
    config_manager = ConfigManager()
    try:
        db_config = config_manager.get_default_database_config()
    except Exception as e:
        print(f"错误: 无法读取数据库配置: {e}")
        return False
    
    data_importer = DataImporter()
    
    print("\n验证所有表...")
    result = await data_importer.verify_data(
        table_name=None,  # None表示验证所有表
        database_config=db_config
    )
    
    tables = result.get("tables", {})
    
    if not tables:
        print("\n[WARN] 未找到任何表，可能还没有导入数据")
        print("请先运行: python scripts/import_data.py")
        return False
    
    print(f"\n找到 {len(tables)} 个表\n")
    print("=" * 60)
    
    for table_name, info in tables.items():
        print(f"\n表: {table_name}")
        print("-" * 60)
        print(f"  记录数: {info.get('record_count', 0):,}")
        print(f"  坐标系: SRID {info.get('srid', 'N/A')}")
        
        if info.get('bbox'):
            bbox = info['bbox']
            print(f"  空间范围:")
            print(f"    经度: {bbox.get('minx', 0):.6f} ~ {bbox.get('maxx', 0):.6f}")
            print(f"    纬度: {bbox.get('miny', 0):.6f} ~ {bbox.get('maxy', 0):.6f}")
        
        invalid = info.get('invalid_geometries', 0)
        if invalid > 0:
            print(f"  [WARN] 无效几何: {invalid} 个")
        else:
            print(f"  [OK] 所有几何有效")
        
        print(f"  字段数: {len(info.get('columns', []))}")
    
    print("\n" + "=" * 60)
    print("[OK] 验证完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(verify_data())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

