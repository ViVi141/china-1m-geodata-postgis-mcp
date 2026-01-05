# MCP工具使用指南

本文档帮助LLM理解如何使用PostGIS MCP服务的各种工具，以及何时使用哪个工具。

## 工具使用流程（必须按顺序执行）

### 标准查询流程

**注意：数据导入应通过脚本完成（`scripts/import_data.py`），MCP服务不提供导入功能。**

**步骤1：查看图幅代码（必须首先执行）**
- 使用工具：`list_tile_codes`
- 用途：查看数据库中有哪些图幅可用
- 返回：图幅代码列表，包含每个图幅在各表中的记录数统计
- 何时使用：**这是查询数据的第一步，必须首先执行！**
- 重要：根据查询目的地的地理位置确定需要查询的图幅，不要只查询F49图幅

**步骤2：查看可用的表（第二步）**
- 使用工具：`list_tables`
- 用途：查看数据库中所有已导入的地理数据表
- 返回：表列表，包括表名、记录数、坐标系(SRID)
- 何时使用：在list_tile_codes之后执行
- 重要：了解各表的用途，不要盲目猜测表名

**步骤3：查看字段说明（第三步，必须执行）**
- 使用工具：`verify_import`
- 用途：验证数据完整性、坐标系、几何有效性等，**最重要的是查看字段说明**
- 返回：每个表的记录数、坐标系、边界框、无效几何数量、字段信息（包含字段说明）
- 何时使用：在list_tables之后执行，**必须执行，不要猜测字段含义**
- 重要提示：
  - name字段在1:100万数据中经常为空，不能仅通过名称查询
  - 需要使用空间范围(bbox)和图幅代码(tile_code)进行查询
  - 自然保护区可能在vegetation_area或regional_boundary_area表中，不在administrative_boundary_area表中
- 详细说明：字段详细说明请查看 [字段说明文档](FIELD_SPEC.md)

**步骤4：查询数据（最后执行）**
- 使用工具：`query_data` 或 `execute_sql`
- 用途：根据前面的信息进行数据查询和分析
- 何时使用：在前三步完成后执行

### 2. 数据查询和分析阶段

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

## 工具选择决策树

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

**重要提示：**
1. **必须按顺序执行**：list_tile_codes → list_tables → verify_import → query_data/execute_sql
2. **数据导入应使用脚本**：`scripts/import_data.py`，不在MCP服务中提供
3. **不要只查F49图幅**：根据目的地地理位置确定需要查询的图幅
4. **不要猜测表名和字段**：必须使用工具查看

## 常用PostGIS函数参考

### 空间测量函数
- `ST_Area(geom::geography)` - 计算面积（平方米），转换为平方公里需除以1000000
- `ST_Distance(geom1::geography, geom2::geography)` - 计算距离（米），转换为公里需除以1000
- `ST_Length(geom::geography)` - 计算长度（米）
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

## 使用示例

### 示例1：查询某个区域的行政区域面积

```sql
-- 使用execute_sql
SELECT 
    COUNT(*) as count,
    SUM(ST_Area(geom::geography) / 1000000) as total_area_km2
FROM administrative_boundary_area
WHERE geom && ST_MakeEnvelope(112.95, 22.75, 113.55, 23.35, 4326)
  AND ST_IsValid(geom)
```

### 示例2：查询某个边界框内的道路

```json
{
  "name": "query_data",
  "arguments": {
    "table_name": "road",
    "spatial_filter": {
      "bbox": [113.0, 23.0, 113.5, 23.5]
    },
    "limit": 100
  }
}
```

### 示例3：计算两个区域的距离

```sql
-- 使用execute_sql
SELECT 
    ST_Distance(
        (SELECT geom FROM administrative_boundary_area WHERE id = 1),
        (SELECT geom FROM administrative_boundary_area WHERE id = 2)
    ) / 1000 as distance_km
```

### 示例4：查找相交的区域

```sql
-- 使用execute_sql
SELECT 
    a1.id as id1,
    a2.id as id2,
    ST_Area(ST_Intersection(a1.geom, a2.geom)::geography) / 1000000 as intersection_area_km2
FROM administrative_boundary_area a1
JOIN administrative_boundary_area a2 ON ST_Intersects(a1.geom, a2.geom)
WHERE a1.id < a2.id
```

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

## 常见错误避免

1. **不要盲目查表**：先使用`list_tables`查看可用表，不要猜测表名
2. **不要猜测字段含义**：先使用`verify_import`查看字段说明，或查看[字段说明文档](FIELD_SPEC.md)
3. **不要只查F49图幅**：先使用`list_tile_codes`查看有哪些图幅，根据目的地确定需要查询的图幅
4. **不要依赖name字段**：大多数表的name字段为空，不能仅通过名称查询
5. **不要用query_data做复杂计算**：复杂计算应使用`execute_sql`
6. **注意几何有效性**：在计算前使用`ST_IsValid(geom)`检查
7. **使用空间索引**：使用`&&`操作符进行快速边界框过滤
8. **单位转换**：记住`::geography`类型返回的是米，需要转换为公里或平方公里

