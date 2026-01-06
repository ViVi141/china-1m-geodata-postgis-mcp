# MCP服务完整指南

本文档包含MCP服务的配置、工具使用和查询工作流程的完整说明。

## 目录

1. [MCP配置](#mcp配置)
2. [工具使用流程](#工具使用流程)
3. [标准查询工作流程](#标准查询工作流程)
4. [工具选择指南](#工具选择指南)
5. [PostGIS函数参考](#postgis函数参考)
6. [常见问题](#常见问题)

---

## MCP配置

### 配置文件位置

MCP配置文件的位置取决于你使用的MCP客户端：

#### Claude Desktop (Anthropic)
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Cursor IDE
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\mcp.json`
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/mcp.json`

### 配置示例

#### 方式1：使用虚拟环境（推荐）

**Windows:**
```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "C:/Users/YourUsername/Desktop/gdb_mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/Users/YourUsername/Desktop/gdb_mcp/mcp_server.py"
      ],
      "cwd": "C:/Users/YourUsername/Desktop/gdb_mcp"
    }
  }
}
```

**Linux/macOS:**
```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "/home/username/gdb_mcp/.venv/bin/python",
      "args": [
        "/home/username/gdb_mcp/mcp_server.py"
      ],
      "cwd": "/home/username/gdb_mcp"
    }
  }
}
```

#### 方式2：使用系统Python

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "python",
      "args": [
        "/absolute/path/to/gdb_mcp/mcp_server.py"
      ],
      "cwd": "/absolute/path/to/gdb_mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/gdb_mcp"
      }
    }
  }
}
```

### 配置说明

**必需字段：**
- `command`: Python解释器路径
- `args`: MCP服务器脚本的绝对路径数组

**可选字段：**
- `cwd`: 工作目录（推荐设置，确保相对路径正确解析）
- `env`: 环境变量（如`PYTHONPATH`）

### 验证配置

配置完成后，重启MCP客户端，然后：
1. 检查MCP服务器是否启动
2. 查看可用工具列表
3. 测试连接：使用 `list_tables` 工具查看数据库中的表

---

## 工具使用流程

### 标准查询流程（必须按顺序执行）

**注意：数据导入应通过脚本完成（`scripts/setup_unified_database.py` 或 `scripts/import_all_tiles.py`），MCP服务不提供导入功能。**

#### 步骤1：查看图幅代码（必须首先执行）

- **工具**：`list_tile_codes`
- **用途**：查看数据库中有哪些图幅可用
- **返回**：图幅代码列表，包含每个图幅在各表中的记录数统计
- **重要**：根据查询目的地的地理位置确定需要查询的图幅，不要只查询F49图幅

#### 步骤2：查看可用的表

- **工具**：`list_tables`
- **用途**：查看数据库中所有已导入的地理数据表
- **返回**：表列表，包括表名、记录数、坐标系(SRID)
- **重要**：了解各表的用途，不要盲目猜测表名

#### 步骤3：查看字段说明（必须执行）

- **工具**：`verify_import`
- **用途**：验证数据完整性、坐标系、几何有效性等，**最重要的是查看字段说明**
- **返回**：每个表的记录数、坐标系、边界框、无效几何数量、字段信息（包含字段说明）
- **重要提示**：
  - name字段在1:100万数据中经常为空，不能仅通过名称查询
  - 需要使用空间范围(bbox)和图幅代码(tile_code)进行查询
  - 详细字段说明请查看 [字段说明文档](FIELD_SPEC.md)

#### 步骤4：查询数据

- **工具**：`query_data` 或 `execute_sql`
- **用途**：根据前面的信息进行数据查询和分析

---

## 标准查询工作流程

### 完整流程（必须按顺序执行）

```
1. list_tile_codes  →  查看有哪些图幅可用
2. list_tables      →  查看有哪些表可用
3. verify_import    →  查看字段说明（必须执行）
4. query_data/execute_sql  →  执行查询
```

### 详细步骤说明

#### 步骤1：查看图幅代码（必须首先执行）

**工具**：`list_tile_codes`

**目的**：
- 了解数据库中有哪些图幅的数据
- 根据查询目的地的地理位置确定需要查询的图幅

**返回信息**：
- 所有可用的图幅代码（如F49、F50、G49、G50等）
- 每个图幅在各表中的记录数统计

**重要提示**：
- 不要只查询F49图幅
- 根据目的地地理位置确定图幅：
  - 深圳市、惠州市：主要在F49和F50图幅
  - 广州市：主要在F49图幅
  - 详细说明请查看 [图幅编号指南](TILE_CODE_GUIDE.md)

#### 步骤2：查看可用的表

**工具**：`list_tables`

**目的**：
- 了解数据库中有哪些表可用
- 了解各表的用途

**重要提示**：
- 不要猜测表名
- 了解各表的用途：
  - `administrative_boundary_area`：行政境界面，**不是自然保护区**
  - `regional_boundary_area`：区域界线面，**可能包含自然保护区**
  - `vegetation_area`：植被面，**可能包含自然保护区**
  - `place_name_natural`：自然地名，包含地名但可能不完整

#### 步骤3：查看字段说明（必须执行）

**工具**：`verify_import`

**目的**：
- 了解表的结构
- **最重要的是查看字段说明，了解每个字段的含义**

**返回信息**：
- 记录数、坐标系、边界框
- **字段信息（包含字段说明）** ← 这是最重要的

**重要提示**：
1. **name字段经常为空**：1:100万数据中很多表的name字段为空，不能仅通过名称查询
2. **需要使用空间范围**：必须结合空间范围(bbox)和图幅代码(tile_code)进行查询
3. **自然保护区的位置**：
   - 可能在`vegetation_area`表中（植被面）
   - 可能在`regional_boundary_area`表中（区域界线面）
   - **不在**`administrative_boundary_area`表中（这是行政境界，不是保护区）
4. 详细字段说明请查看 [字段说明文档](FIELD_SPEC.md)

#### 步骤4：执行查询

**工具**：`query_data` 或 `execute_sql`

**目的**：根据前面的信息进行数据查询和分析

**重要提示**：
1. **必须使用图幅过滤**：使用`attribute_filter: {"tile_code": "F49"}`或SQL中的`WHERE tile_code IN ('F49', 'F50')`
2. **必须使用空间范围**：使用`spatial_filter.bbox`或SQL中的`geom && ST_MakeEnvelope(...)`
3. **不能仅通过名称查询**：name字段经常为空
4. **计算面积**：使用`ST_Area(geom::geography)/1000000`转换为平方公里

### 查询示例：查找莲花山自然保护区面积

**步骤1：查看图幅代码**
```
list_tile_codes({})
```
→ 确定莲花山所在的图幅（深圳市主要在F49和F50图幅）

**步骤2：查看可用的表**
```
list_tables({})
```
→ 了解有哪些表可用

**步骤3：查看字段说明**
```
verify_import({"table_name": "vegetation_area"})
verify_import({"table_name": "regional_boundary_area"})
```
→ 了解字段含义，确认哪些表可能包含自然保护区

**步骤4：执行查询**
```
execute_sql({
  "sql": "SELECT tile_code, ST_Area(geom::geography)/1000000 as area_km2, ST_AsText(ST_Centroid(geom)) as centroid FROM vegetation_area WHERE tile_code IN ('F49', 'F50') AND geom && ST_MakeEnvelope(113.5, 22.4, 114.5, 22.6, 4326) AND ST_IsValid(geom) ORDER BY area_km2 DESC LIMIT 10"
})
```

### 常见错误

❌ **错误1**：不查看图幅代码，直接查询  
✅ **正确**：先使用`list_tile_codes`查看有哪些图幅

❌ **错误2**：猜测表名，认为自然保护区在`administrative_boundary_area`表中  
✅ **正确**：使用`list_tables`查看可用表，使用`verify_import`查看字段说明

❌ **错误3**：不查看字段说明，猜测字段含义  
✅ **正确**：使用`verify_import`查看字段说明，了解name字段经常为空

❌ **错误4**：只查询F49图幅  
✅ **正确**：根据目的地地理位置确定需要查询的图幅，如果跨图幅则查询多个图幅

❌ **错误5**：仅通过name字段查询"莲花山"  
✅ **正确**：name字段可能为空，必须结合空间范围和图幅代码查询

---

## 工具选择指南

### 工具选择决策树

```
需要查询或分析数据？
│
├─ 第一步：查看图幅代码（必须首先执行）
│  └─ 使用 list_tile_codes
│     └─ 根据目的地地理位置确定需要查询的图幅
│
├─ 第二步：查看可用的表
│  └─ 使用 list_tables
│     └─ 了解各表的用途（不要猜测表名）
│
├─ 第三步：查看字段说明（必须执行）
│  └─ 使用 verify_import
│     └─ 了解字段含义（不要猜测字段含义）
│
└─ 第四步：查询数据
   ├─ 简单查询（按位置或属性过滤）？
   │  └─ 使用 query_data
   │     ├─ 按边界框查询：spatial_filter.bbox
   │     ├─ 按几何查询：spatial_filter.geometry
   │     ├─ 按图幅过滤：attribute_filter.tile_code
   │     └─ 注意：name字段经常为空，不能仅通过名称查询
   │
   └─ 复杂分析（计算、统计、空间关系）？
      └─ 使用 execute_sql
         ├─ 计算面积：ST_Area(geom::geography)/1000000
         ├─ 计算距离：ST_Distance(geom1::geography, geom2::geography)/1000
         ├─ 空间过滤：ST_Intersects(geom1, geom2)
         ├─ 图幅过滤：WHERE tile_code IN ('F49', 'F50', ...)
         ├─ 缓冲区：ST_Buffer(geom, distance)
         └─ 聚合统计：GROUP BY + 空间函数
```

### 简单查询 vs 复杂分析

**简单查询：使用 `query_data`**
- 用途：简单的空间查询和属性过滤
- 适用场景：
  - 按边界框查询（bbox）
  - 按几何对象查询（geometry）
  - 按属性过滤
  - 获取原始记录数据
- 限制：返回原始记录，不进行复杂计算

**复杂分析：使用 `execute_sql`**
- 用途：复杂的空间分析和计算
- 适用场景：
  - 计算面积、距离、长度等
  - 空间关系判断（相交、包含、重叠等）
  - 缓冲区分析
  - 空间聚合统计
  - 多表空间连接
  - 坐标系转换
- 优势：可以使用所有PostGIS空间函数

---

## PostGIS函数参考

### 空间测量函数

- `ST_Area(geom::geography)` - 计算面积（平方米），转换为平方公里需除以1000000
- `ST_Distance(geom1::geography, geom2::geography)` - 计算距离（米），转换为公里需除以1000
- `ST_Length(geom::geography)` - 计算长度（米），转换为公里需除以1000
- `ST_Perimeter(geom::geography)` - 计算周长（米）

### 空间关系函数

- `ST_Intersects(geom1, geom2)` - 判断是否相交
- `ST_Within(geom1, geom2)` - 判断geom1是否在geom2内
- `ST_Contains(geom1, geom2)` - 判断geom1是否包含geom2
- `ST_Overlaps(geom1, geom2)` - 判断是否重叠
- `ST_Touches(geom1, geom2)` - 判断是否接触
- `ST_Crosses(geom1, geom2)` - 判断是否交叉

### 空间操作函数

- `ST_Buffer(geom, distance)` - 创建缓冲区
- `ST_Union(geom1, geom2)` - 合并几何
- `ST_Intersection(geom1, geom2)` - 求交集
- `ST_Difference(geom1, geom2)` - 求差集
- `ST_ConvexHull(geom)` - 计算凸包

### 空间分析函数

- `ST_Centroid(geom)` - 计算中心点
- `ST_Envelope(geom)` - 计算边界框
- `ST_Transform(geom, srid)` - 坐标系转换
- `ST_Simplify(geom, tolerance)` - 简化几何

### 空间索引操作符

- `geom && ST_MakeEnvelope(...)` - 快速边界框过滤（使用空间索引）
- `ST_MakeEnvelope(minx, miny, maxx, maxy, srid)` - 创建边界框

### 几何转换函数

- `ST_AsText(geom)` - 转为WKT格式
- `ST_GeomFromText(wkt, srid)` - 从WKT创建几何
- `ST_AsGeoJSON(geom)` - 转为GeoJSON格式

---

## 常见问题

### 问题1：找不到模块

**错误**: `ModuleNotFoundError: No module named 'core'`

**解决方案**: 
- 确保 `cwd` 设置为项目根目录
- 或设置 `PYTHONPATH` 环境变量指向项目根目录

### 问题2：找不到配置文件

**错误**: `FileNotFoundError: config/database.ini`

**解决方案**: 
- 确保 `cwd` 设置为项目根目录
- 或使用绝对路径配置数据库连接

### 问题3：Python版本不兼容

**错误**: Python版本过低

**解决方案**: 
- 确保使用Python 3.8或更高版本
- 在虚拟环境中安装正确的Python版本

### 问题4：数据库连接失败

**错误**: 无法连接到PostgreSQL

**解决方案**: 
- 确保PostgreSQL服务正在运行
- 检查 `config/database.ini` 配置是否正确
- 确保数据库已启用PostGIS扩展

### 问题5：查询结果为空

**可能原因**：
1. 没有使用正确的图幅代码过滤
2. 空间范围不正确
3. name字段为空，不能仅通过名称查询

**解决方案**：
- 先使用`list_tile_codes`查看可用图幅
- 使用`verify_import`查看字段说明
- 结合空间范围和图幅代码查询

---

## 最佳实践

1. **先查看图幅**：使用`list_tile_codes`查看有哪些图幅可用
2. **先查看表结构**：使用`list_tables`了解有哪些表可用
3. **查看字段说明**：使用`verify_import`查看字段说明，**不要猜测字段含义**
4. **根据目的地确定图幅**：根据查询目的地的地理位置确定需要查询的图幅，不要只查询F49
5. **简单查询用query_data**：对于简单的空间过滤和属性查询
6. **复杂分析用execute_sql**：对于需要计算、统计、空间关系的分析
7. **使用空间索引**：在WHERE子句中使用`geom && ST_MakeEnvelope(...)`可以快速过滤
8. **注意坐标系**：面积和距离计算使用`::geography`类型，单位是米
9. **转换单位**：面积除以1000000得到平方公里，距离除以1000得到公里
10. **不要依赖name字段**：大多数表的name字段为空，不能仅通过名称查询

---

## 相关文档

- [字段说明文档](FIELD_SPEC.md) - 详细的字段说明
- [表使用指南](TABLE_USAGE_GUIDE.md) - 表用途和单位转换
- [图幅编号指南](TILE_CODE_GUIDE.md) - 如何确定图幅代码
- [查询示例](QUERY_EXAMPLES.md) - 更多查询示例

