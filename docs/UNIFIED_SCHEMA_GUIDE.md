# 统一表结构导入指南

本文档说明如何创建统一的PostGIS表结构并导入所有图幅的数据。

## 概述

所有图幅共享同一组表结构，通过 `tile_code` 字段区分不同图幅的数据。这种设计适合MCP服务，便于跨图幅查询和分析。

## 工作流程

### 方式1：使用统一工具集（推荐）⭐⭐⭐

**最简单的方式，一键完成所有步骤：**

```bash
python scripts/setup_unified_database.py
```

工具会自动执行：
1. 解析图幅结构（自动查找F49.gdb作为参考）
2. 创建统一表结构
3. 导入所有图幅数据

**自定义参数：**
```bash
# 指定参考图幅和GDB目录
python scripts/setup_unified_database.py --reference-gdb F49.gdb --gdb-dir .

# 强制重新创建表结构
python scripts/setup_unified_database.py --force

# 只执行导入步骤（如果表结构已创建）
python scripts/setup_unified_database.py --skip-parse --skip-create
```

### 方式2：分步执行

如果需要分步执行或自定义参数：

#### 步骤1：解析图幅结构（如果还没有）

首先需要解析一个图幅的完整结构（通常使用F49作为参考）：

```bash
python scripts/parse_tile_schema.py F49.gdb --output analysis
```

这会生成 `analysis/F49_complete_analysis.json` 文件，包含所有图层的详细字段信息。

#### 步骤2：创建统一表结构

基于分析结果创建统一的PostGIS表结构：

```bash
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json
```

**选项说明：**
- `--analysis, -a`: 分析结果JSON文件路径（默认: `analysis/F49_complete_analysis.json`）
- `--srid`: 坐标系SRID（默认: 4326）
- `--force, -f`: 强制重新创建表（会删除已存在的表）

**示例：**
```bash
# 使用默认分析结果
python scripts/create_unified_schema.py

# 使用自定义分析结果
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json

# 强制重新创建（会删除已存在的表）
python scripts/create_unified_schema.py --force
```

#### 步骤3：导入所有图幅数据

将所有图幅的数据导入到统一表结构中：

```bash
python scripts/import_all_tiles.py
```

**选项说明：**
- `--gdb-dir, -d`: 包含GDB文件的目录（默认: 当前目录）
- `--gdb, -g`: 单个GDB文件路径（如果指定，只导入该文件）
- `--srid`: 坐标系SRID（默认: 4326）
- `--batch-size`: 批量插入大小（默认: 1000）
- `--skip-invalid`: 跳过无效几何（默认: True）

**示例：**
```bash
# 导入当前目录下的所有GDB文件
python scripts/import_all_tiles.py

# 导入指定目录下的所有GDB文件
python scripts/import_all_tiles.py --gdb-dir /path/to/gdb/files

# 只导入单个GDB文件
python scripts/import_all_tiles.py --gdb F49.gdb

# 自定义批量大小
python scripts/import_all_tiles.py --batch-size 2000
```

## 表结构特点

### 统一表结构

所有图幅共享同一组表，表名对应图层名（小写）：
- `aanp` - 地名点（AANP图层）
- `hyda` - 水系面（HYDA图层）
- `lrdl` - 公路（LRDL图层）
- ... 等等

### 标准字段

每个表都包含以下标准字段：

1. **id** (BIGSERIAL PRIMARY KEY) - 主键，自动递增
2. **geom** (GEOMETRY) - PostGIS几何对象，根据图层类型自动选择
3. **tile_code** (VARCHAR(10) NOT NULL) - 图幅代码，用于区分不同图幅
4. **created_at** (TIMESTAMP) - 记录创建时间
5. **updated_at** (TIMESTAMP) - 记录更新时间
6. **数据字段** - 根据图层结构自动添加

### 索引

每个表都自动创建以下索引：

1. **空间索引** (GIST) - 在 `geom` 字段上，用于快速空间查询
2. **图幅代码索引** (BTREE) - 在 `tile_code` 字段上，用于快速过滤图幅
3. **常用字段索引** (BTREE) - 在常用查询字段上（如 `gb`, `name`, `class`, `type`, `rn`）

## 查询示例

### 查询特定图幅的数据

```sql
-- 查询F49图幅的所有水系面
SELECT * FROM hyda WHERE tile_code = 'F49' LIMIT 100;
```

### 跨图幅查询

```sql
-- 查询F49和F50图幅的所有公路
SELECT * FROM lrdl WHERE tile_code IN ('F49', 'F50') LIMIT 100;
```

### 空间查询

```sql
-- 查询某个区域内的所有水系面（跨图幅）
SELECT * FROM hyda 
WHERE geom && ST_MakeEnvelope(113.0, 23.0, 113.5, 23.5, 4326)
  AND tile_code IN ('F49', 'F50')
LIMIT 100;
```

### 统计查询

```sql
-- 统计每个图幅的记录数
SELECT tile_code, COUNT(*) as count 
FROM hyda 
GROUP BY tile_code 
ORDER BY tile_code;
```

## 注意事项

1. **表结构一致性**：所有图幅必须使用相同的表结构。如果不同图幅的图层结构不同，可能会导致导入失败。

2. **图幅代码**：确保每个图幅的代码正确提取。代码格式为：F49、F50、G49、G50等。

3. **数据验证**：导入过程中会自动验证和修复无效几何。如果修复失败，会跳过该记录。

4. **性能优化**：
   - 使用批量插入（默认1000条/批）
   - 自动创建空间索引和常用字段索引
   - 导入后自动更新统计信息（ANALYZE）

5. **MCP服务兼容**：
   - 表结构完全兼容现有的MCP工具
   - 可以使用 `list_tile_codes` 查看已导入的图幅
   - 可以使用 `list_tables` 查看已创建的表
   - 可以使用 `query_data` 和 `execute_sql` 查询数据

## 故障排除

### 问题1：表不存在

**错误信息**：`表 xxx 不存在，跳过导入`

**解决方案**：
1. 先运行 `python scripts/create_unified_schema.py` 创建表结构
2. 确保使用了正确的分析结果文件

### 问题2：字段不匹配

**错误信息**：`字段 xxx 不存在`

**解决方案**：
1. 检查不同图幅的图层结构是否一致
2. 如果结构不同，需要重新解析并创建表结构

### 问题3：导入速度慢

**解决方案**：
1. 增加批量大小：`--batch-size 2000`
2. 检查数据库性能配置
3. 确保已创建索引

### 问题4：几何验证失败

**解决方案**：
1. 确保使用 `--skip-invalid` 选项（默认启用）
2. 检查源数据质量
3. 查看日志了解具体错误

## 完整示例

### 使用统一工具集（推荐）

```bash
# 一键完成所有步骤
python scripts/setup_unified_database.py

# 验证数据（使用MCP工具或SQL）
# 在MCP客户端中：
# - 使用 list_tile_codes 查看已导入的图幅
# - 使用 list_tables 查看已创建的表
# - 使用 query_data 查询数据
```

### 分步执行

```bash
# 1. 解析F49图幅结构
python scripts/parse_tile_schema.py F49.gdb --output analysis

# 2. 创建统一表结构
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json

# 3. 导入所有图幅数据
python scripts/import_all_tiles.py

# 4. 验证数据（使用MCP工具或SQL）
# 在MCP客户端中：
# - 使用 list_tile_codes 查看已导入的图幅
# - 使用 list_tables 查看已创建的表
# - 使用 query_data 查询数据
```

## 相关文档

- [MCP服务完整指南](MCP_GUIDE.md) - MCP配置、工具使用和查询工作流程
- [字段说明文档](FIELD_SPEC.md)

