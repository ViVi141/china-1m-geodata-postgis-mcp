"""
MCP服务使用示例
演示如何直接调用MCP服务的功能
"""

import asyncio
import json
from core.config_manager import ConfigManager
from core.spec_loader import SpecLoader
from core.data_importer import DataImporter


async def example_import():
    """示例：导入数据"""
    print("=" * 60)
    print("示例：导入地理数据")
    print("=" * 60)

    # 初始化组件
    config_manager = ConfigManager()
    data_importer = DataImporter()

    # 获取数据库配置
    try:
        db_config = config_manager.get_default_database_config()
    except FileNotFoundError:
        print("错误: 请先创建 config/database.ini 文件")
        return

    # 导入数据
    result = await data_importer.import_data(
        data_path="F49.gdb",
        spec_name="china_1m_2021",
        database_config=db_config,
        options={
            "srid": 4326,
            "batch_size": 1000,
            "skip_invalid": True,
            "create_indexes": True,
        },
    )

    print("\n导入结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_verify():
    """示例：验证数据"""
    print("\n" + "=" * 60)
    print("示例：验证导入的数据")
    print("=" * 60)

    config_manager = ConfigManager()
    data_importer = DataImporter()

    try:
        db_config = config_manager.get_default_database_config()
    except FileNotFoundError:
        print("错误: 请先创建 config/database.ini 文件")
        return

    result = await data_importer.verify_data(
        table_name="water_system_area", database_config=db_config
    )

    print("\n验证结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_query():
    """示例：查询数据"""
    print("\n" + "=" * 60)
    print("示例：查询地理数据")
    print("=" * 60)

    config_manager = ConfigManager()
    data_importer = DataImporter()

    try:
        db_config = config_manager.get_default_database_config()
    except FileNotFoundError:
        print("错误: 请先创建 config/database.ini 文件")
        return

    result = await data_importer.query_data(
        table_name="water_system_area",
        spatial_filter={"bbox": [110.0, 20.0, 120.0, 30.0]},
        limit=10,
        database_config=db_config,
    )

    print("\n查询结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def example_list_specs():
    """示例：列出规格"""
    print("\n" + "=" * 60)
    print("示例：列出数据规格")
    print("=" * 60)

    spec_loader = SpecLoader()
    specs = spec_loader.list_specs()

    print(f"\n找到 {len(specs)} 个数据规格:")
    for spec_name in specs:
        print(f"  - {spec_name}")

    # 加载一个规格
    if specs:
        spec = spec_loader.load_spec(specs[0])
        print(f"\n规格 '{specs[0]}' 详情:")
        print(f"  名称: {spec.get('name')}")
        print(f"  描述: {spec.get('description')}")
        print(f"  图层数: {len(spec.get('layer_mapping', {}))}")


async def main():
    """主函数"""
    # 列出规格
    example_list_specs()

    # 导入数据（需要实际的数据文件）
    # await example_import()

    # 验证数据（需要先导入数据）
    # await example_verify()

    # 查询数据（需要先导入数据）
    # await example_query()


if __name__ == "__main__":
    asyncio.run(main())
