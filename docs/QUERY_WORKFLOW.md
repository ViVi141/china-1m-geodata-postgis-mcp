# 标准查询工作流程

本文档说明使用MCP服务进行数据查询的标准工作流程，帮助LLM按正确顺序执行查询。

## 必须遵循的查询流程

### 完整流程（必须按顺序执行）

```
1. list_tile_codes  →  查看有哪些图幅可用
2. list_tables      →  查看有哪些表可用
3. verify_import    →  查看字段说明（必须执行）
4. query_data/execute_sql  →  执行查询
```

## 详细步骤说明

### 步骤1：查看图幅代码（必须首先执行）

**工具**：`list_tile_codes`

**目的**：
- 了解数据库中有哪些图幅的数据
- 根据查询目的地的地理位置确定需要查询的图幅

**示例**：
```json
{
  "name": "list_tile_codes",
  "arguments": {}
}
```

**返回信息**：
- 所有可用的图幅代码（如F49、F50、G49、G50等）
- 每个图幅在各表中的记录数统计

**重要提示**：
- 不要只查询F49图幅
- 根据目的地地理位置确定图幅：
  - 深圳市、惠州市：主要在F49和F50图幅
  - 广州市：主要在F49图幅
  - 详细说明请查看 [图幅编号指南](TILE_CODE_GUIDE.md)

### 步骤2：查看可用的表

**工具**：`list_tables`

**目的**：
- 了解数据库中有哪些表可用
- 了解各表的用途

**示例**：
```json
{
  "name": "list_tables",
  "arguments": {}
}
```

**重要提示**：
- 不要猜测表名
- 了解各表的用途：
  - `administrative_boundary_area`：行政境界面，**不是自然保护区**
  - `regional_boundary_area`：区域界线面，**可能包含自然保护区**
  - `vegetation_area`：植被面，**可能包含自然保护区**
  - `place_name_natural`：自然地名，包含地名但可能不完整

### 步骤3：查看字段说明（必须执行）

**工具**：`verify_import`

**目的**：
- 了解表的结构
- **最重要的是查看字段说明，了解每个字段的含义**

**示例**：
```json
{
  "name": "verify_import",
  "arguments": {
    "table_name": "vegetation_area"
  }
}
```

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

### 步骤4：执行查询

**工具**：`query_data` 或 `execute_sql`

**目的**：根据前面的信息进行数据查询和分析

**重要提示**：
1. **必须使用图幅过滤**：使用`attribute_filter: {"tile_code": "F49"}`或SQL中的`WHERE tile_code IN ('F49', 'F50')`
2. **必须使用空间范围**：使用`spatial_filter.bbox`或SQL中的`geom && ST_MakeEnvelope(...)`
3. **不能仅通过名称查询**：name字段经常为空
4. **计算面积**：使用`ST_Area(geom::geography)/1000000`转换为平方公里

## 查询示例：查找莲花山自然保护区面积

### 正确的查询流程

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
✅ **正确**：使用`list_tables`查看可用表，使用`verify_import`查看字段说明，确认自然保护区可能在`vegetation_area`或`regional_boundary_area`表中

❌ **错误3**：不查看字段说明，猜测字段含义
✅ **正确**：使用`verify_import`查看字段说明，了解name字段经常为空

❌ **错误4**：只查询F49图幅
✅ **正确**：根据目的地地理位置确定需要查询的图幅，如果跨图幅则查询多个图幅

❌ **错误5**：仅通过name字段查询"莲花山"
✅ **正确**：name字段可能为空，必须结合空间范围和图幅代码查询

## 表用途说明

| 表名 | 用途 | 是否包含自然保护区 |
|------|------|------------------|
| `administrative_boundary_area` | 行政境界面（省、市、县、乡等行政区域） | ❌ 不包含 |
| `regional_boundary_area` | 区域界线面（自然文化区、特殊地区、开发区、保税区等） | ✅ 可能包含 |
| `vegetation_area` | 植被面（耕地、园地、林地、草地、城市绿地等） | ✅ 可能包含 |
| `place_name_natural` | 自然地名（山名、水系名、自然地域名等） | ⚠️ 只有地名，可能不完整 |

## 重要提醒

1. **必须按顺序执行**：list_tile_codes → list_tables → verify_import → query_data/execute_sql
2. **不要跳过步骤**：每个步骤都有其重要性
3. **不要猜测**：不要猜测表名、字段含义、图幅代码
4. **查看文档**：遇到不确定的情况，查看相关文档（FIELD_SPEC.md、TILE_CODE_GUIDE.md）

