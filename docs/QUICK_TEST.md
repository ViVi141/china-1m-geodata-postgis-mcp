# 快速测试指南

**作者**: ViVi141 (747384120@qq.com)

## 测试步骤

### 1. 确保环境就绪

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1  # Windows PowerShell
# 或
.venv\Scripts\activate.bat  # Windows CMD

# 安装依赖（如果还没安装）
pip install -r requirements.txt
```

### 2. 确保PostgreSQL容器运行

```bash
# 检查容器状态
docker ps --filter name=geodata-postgres

# 如果未运行，启动容器
docker start geodata-postgres
# 或
start_docker.bat
```

### 3. 测试数据库连接

```bash
python scripts/check_connection.py
```

应该看到：
```
[OK] 数据库连接成功
[OK] PostGIS版本: 3.5 ...
[OK] PostGIS扩展已启用
```

### 4. 导入GDB数据

```bash
# 导入单个GDB文件
python scripts/import_data.py <gdb_path>

# 批量导入目录中的所有GDB文件
python scripts/import_data.py --dir <directory>

# 如果不指定路径，会自动查找当前目录下的GDB文件（F49.gdb, G49.gdb等）
python scripts/import_data.py
```

这会：
- 导入GDB数据到PostgreSQL
- 显示导入进度和结果
- 支持批量导入目录中的所有GDB文件

**参数说明：**
- `gdb_path`: GDB文件路径（可选）
- `--dir, -d`: 包含GDB文件的目录（批量导入）
- `--spec, -s`: 数据规格名称（默认: china_1m_2021）
- `--srid`: 目标坐标系SRID（默认: 4326）
- `--batch-size`: 批量插入大小（默认: 1000）

### 5. 验证导入的数据

```bash
python scripts/verify_data.py
```

这会显示：
- 所有导入的表
- 每个表的记录数
- 坐标系信息
- 空间范围
- 几何有效性

### 6. 测试查询功能

```bash
python scripts/query_data.py
```

这会测试：
- 列出所有表
- 查询表数据
- 空间查询

## 使用MCP工具（在MCP客户端中）

### 导入数据

```json
{
  "name": "import_geodata",
  "arguments": {
    "data_path": "F49.gdb",
    "spec_name": "china_1m_2021"
  }
}
```

### 验证数据

```json
{
  "name": "verify_import",
  "arguments": {
    "table_name": "water_system_area"
  }
}
```

### 查询数据

```json
{
  "name": "query_data",
  "arguments": {
    "table_name": "water_system_area",
    "spatial_filter": {
      "bbox": [110.0, 20.0, 120.0, 30.0]
    },
    "limit": 10
  }
}
```

### 列出所有表

```json
{
  "name": "list_tables",
  "arguments": {}
}
```

### 执行SQL查询

```json
{
  "name": "execute_sql",
  "arguments": {
    "sql": "SELECT COUNT(*) as count, tile_code FROM water_system_area GROUP BY tile_code"
  }
}
```

## 常见问题

### Q: 找不到GDB文件？
A: 使用 `python scripts/import_data.py <gdb_path>` 指定GDB文件路径，或使用 `--dir` 参数指定包含GDB文件的目录

### Q: 导入失败？
A: 检查：
1. PostgreSQL容器是否运行
2. 数据库连接配置是否正确
3. GDB文件是否完整

### Q: 如何查看导入的表？
A: 运行 `python scripts/verify_data.py` 或使用 `list_tables` 工具

### Q: 如何检查GDB文件中的图层信息？
A: 运行 `python scripts/check_layers.py <gdb_path>` 或 `python scripts/check_layers.py --dir <directory>` 批量检查

