"""
测试数据查询功能
"""

import asyncio
import sys
from core.data_importer import DataImporter
from core.config_manager import ConfigManager

async def query_data():
    """测试查询数据"""
    print("=" * 60)
    print("测试数据查询")
    print("=" * 60)
    
    config_manager = ConfigManager()
    try:
        db_config = config_manager.get_default_database_config()
    except Exception as e:
        print(f"错误: 无法读取数据库配置: {e}")
        return False
    
    data_importer = DataImporter()
    
    # 1. 列出所有表
    print("\n[1/3] 列出所有表...")
    tables_result = await data_importer.list_tables(database_config=db_config)
    tables = tables_result.get("tables", [])
    
    if not tables:
        print("[WARN] 未找到任何表，请先导入数据")
        return False
    
    print(f"找到 {len(tables)} 个表:")
    for table in tables[:5]:  # 只显示前5个
        print(f"  - {table['table_name']} ({table.get('record_count', 0):,} 条记录)")
    
    # 2. 查询一个表的数据
    if tables:
        table_name = tables[0]['table_name']
        print(f"\n[2/3] 查询表: {table_name}")
        print("-" * 60)
        
        result = await data_importer.query_data(
            table_name=table_name,
            limit=5,
            database_config=db_config
        )
        
        print(f"返回 {result.get('count', 0)} 条记录 (限制5条)")
        if result.get('data'):
            print("\n示例数据:")
            for i, record in enumerate(result['data'][:3], 1):
                print(f"\n  记录 {i}:")
                for key, value in list(record.items())[:5]:  # 只显示前5个字段
                    if key == 'geom' and value:
                        # 检查是否为空几何
                        if 'EMPTY' in str(value).upper():
                            print(f"    {key}: {value} (空几何)")
                        else:
                            # 几何对象太长，只显示前100个字符
                            geom_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                            print(f"    {key}: {geom_str}")
                    else:
                        print(f"    {key}: {value}")
    
    # 3. 空间查询示例
    if tables:
        table_name = tables[0]['table_name']
        print(f"\n[3/3] 空间查询示例: {table_name}")
        print("-" * 60)
        
        # 广东省大致范围
        bbox = [109.0, 20.0, 117.0, 25.0]
        print(f"查询边界框: {bbox}")
        
        result = await data_importer.query_data(
            table_name=table_name,
            spatial_filter={"bbox": bbox},
            limit=10,
            database_config=db_config
        )
        
        print(f"找到 {result.get('count', 0)} 条记录")
    
    print("\n" + "=" * 60)
    print("[OK] 查询测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(query_data())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

