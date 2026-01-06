# 表用途和单位转换指南

本文档帮助LLM正确理解各个表的用途和单位转换方法，避免常见错误。

## 表用途速查表

| 表名 | 用途 | 几何类型 | 重要说明 |
|------|------|----------|----------|
| **boua** | 行政境界(面) | MultiPolygon | ⚠️ **只包含区/县/县级市，不包含地级市**。同一行政区域可能被分割成多个记录，查询时必须使用`GROUP BY name/pac`和`ST_Union(geom)`合并 |
| **boul** | 行政境界(线) | MultiLineString | 行政边界线 |
| **boup** | 行政境界(点) | Point | 行政边界点 |
| **brga** | 区域界线(面) | MultiPolygon | 可能包含自然保护区等区域边界 |
| **brgl** | 区域界线(线) | MultiLineString | 区域边界线 |
| **brgp** | 区域界线(点) | Point | 区域边界点 |
| **hyda** | 水系(面) | MultiPolygon | 湖泊、水库、池塘等水域 |
| **hydl** | 水系(线) | MultiLineString | 河流、沟渠等 |
| **hydp** | 水系(点) | Point | 泉、井等 |
| **lrdl** | 公路 | MultiLineString | 道路网络 |
| **lrrl** | 铁路 | MultiLineString | 铁路网络 |
| **resa** | 居民地(面) | MultiPolygon | 城市、城镇等居民区 |
| **resp** | 居民地(点) | Point | 村庄、居民点 |
| **vega** | 植被(面) | MultiPolygon | 可能包含自然保护区 |
| **agnp** | 地名(点) | Point | 自然地名，可能包含保护区名称 |
| **aanp** | 地名(点) | Point | 行政地名 |

## 单位转换指南

### ⚠️ 重要：shape_area和shape_length字段

**这些字段的单位是度²（平方度）和度，不能直接转换为平方公里或公里！**

#### shape_area字段

- **单位**：度²（平方度）
- **错误用法**：`shape_area * 12341`（不能这样做）
- **正确用法**：`ST_Area(geom::geography) / 1000000`（得到平方公里）
  - `ST_Area(geom::geography)`返回**平方米**
  - 除以1000000得到**平方公里**

**原因**：度²到平方公里的转换不是线性的，在不同纬度下，1度²对应的实际面积不同。

#### shape_length字段

- **单位**：度
- **错误用法**：`shape_length * 111`（不能这样做）
- **正确用法**：`ST_Length(geom::geography) / 1000`（得到公里）
  - `ST_Length(geom::geography)`返回**米**
  - 除以1000得到**公里**

**原因**：度到公里的转换不是线性的，在不同纬度下，1度对应的实际长度不同。

### 正确的单位转换公式

```sql
-- 计算面积（平方公里）
ST_Area(geom::geography) / 1000000

-- 计算长度（公里）
ST_Length(geom::geography) / 1000

-- 计算距离（公里）
ST_Distance(geom1::geography, geom2::geography) / 1000

-- 计算面积（公顷）
ST_Area(geom::geography) / 10000

-- 计算面积（平方米）
ST_Area(geom::geography)
```

## 常见查询场景

### 1. 查询行政区域面积（boua表）

**重要特点**：
- **数据层级限制**：boua表只包含区/县/县级市，不包含地级市、省级行政区
- **数据分割特性**：同一个行政区域可能被分割成多个记录，原因包括：
  - 跨图幅分割：行政区域跨越多个1:100万图幅（如F49和F50）
  - 地理要素分割：被河流、道路、其他行政区域等地理要素分割
  - 数据组织方式：数据本身的组织方式导致同一区域被分割存储

**查询时必须合并**：查询某个行政区域时，必须将所有相同`name`或`pac`的记录合并视为一个整体。

```sql
-- ✅ 正确：合并所有分割的部分
SELECT 
    name,
    pac,
    COUNT(*) as part_count,  -- 该行政区域被分割成几部分
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2,
    ST_AsText(ST_Centroid(ST_Union(geom))) as centroid
FROM boua
WHERE name = '香洲区'
GROUP BY name, pac;

-- ❌ 错误：没有合并，可能返回多条记录，面积不准确
SELECT name, ST_Area(geom::geography) / 1000000 as area_km2
FROM boua
WHERE name = '香洲区';
```

**使用PAC代码查询（如果name为空）**：
```sql
-- 使用PAC代码查询（适用于name字段为空的情况）
SELECT 
    pac,
    MAX(name) as name,  -- 如果有name值
    COUNT(*) as part_count,
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2
FROM boua
WHERE pac = 440402
GROUP BY pac;
```

**查询被分割成多部分的行政区域**：
```sql
-- 查找被分割成多个部分的行政区域（可能跨图幅）
SELECT 
    name,
    pac,
    COUNT(*) as part_count,
    array_agg(DISTINCT tile_code) as tile_codes,  -- 分布在哪些图幅
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2
FROM boua
WHERE name IS NOT NULL
GROUP BY name, pac
HAVING COUNT(*) > 1  -- 只显示被分割成多部分的区域
ORDER BY part_count DESC, total_area_km2 DESC
LIMIT 20;
```

### 2. 查询水系面积（hyda表）

```sql
-- ✅ 正确：使用ST_Area计算面积
SELECT 
    name,
    ST_Area(geom::geography) / 1000000 as area_km2
FROM hyda
WHERE geom && ST_MakeEnvelope(113.0, 22.0, 114.0, 23.0, 4326)
ORDER BY area_km2 DESC;

-- ❌ 错误：不能使用shape_area直接转换
SELECT name, shape_area * 12341 as area_km2 FROM hyda;
```

### 3. 查询道路长度（lrdl表）

```sql
-- ✅ 正确：使用ST_Length计算长度
SELECT 
    name,
    rn,
    ST_Length(geom::geography) / 1000 as length_km
FROM lrdl
WHERE tile_code IN ('F49', 'F50')
ORDER BY length_km DESC;

-- ❌ 错误：不能使用shape_length直接转换
SELECT name, shape_length * 111 as length_km FROM lrdl;
```

### 4. 查询植被区域（vega表，可能包含自然保护区）

```sql
-- ✅ 正确：使用ST_Area计算面积
SELECT 
    name,
    type,
    ST_Area(geom::geography) / 1000000 as area_km2
FROM vega
WHERE geom && ST_MakeEnvelope(114.0, 22.7, 115.0, 23.8, 4326)
  AND ST_IsValid(geom)
ORDER BY area_km2 DESC;
```

## 常见错误

### ❌ 错误1：使用shape_area直接转换

```sql
-- 错误
SELECT shape_area * 12341 as area_km2 FROM boua;
```

**问题**：shape_area是度²，不能直接乘以常数转换为平方公里。

### ✅ 正确：使用ST_Area计算

```sql
-- 正确
SELECT ST_Area(geom::geography) / 1000000 as area_km2 FROM boua;
```

### ❌ 错误2：查询boua表时没有合并分割的部分

```sql
-- 错误：可能返回多条记录
SELECT name, ST_Area(geom::geography) / 1000000 as area_km2
FROM boua
WHERE name = '某区域';
```

**问题**：如果该区域被分割成多个部分，会返回多条记录，每条记录的面积只是部分面积。

### ✅ 正确：使用GROUP BY和ST_Union合并

```sql
-- 正确：合并所有分割的部分
SELECT 
    name,
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2
FROM boua
WHERE name = '某区域'
GROUP BY name;
```

### ❌ 错误3：只查询单个图幅

```sql
-- 错误：如果区域跨图幅，会遗漏数据
SELECT * FROM boua WHERE name = '某区域' AND tile_code = 'F49';
```

**问题**：如果该区域也分布在F50图幅，会遗漏F50的数据。

### ✅ 正确：查询所有相关图幅

```sql
-- 正确：查询所有相关图幅
SELECT * FROM boua 
WHERE name = '某区域' 
  AND tile_code IN ('F49', 'F50');  -- 根据地理位置确定图幅
```

## 查询工作流程

1. **查看图幅**：使用`list_tile_codes`查看有哪些图幅可用
2. **查看表**：使用`list_tables`查看有哪些表可用
3. **查看字段**：使用`verify_import`查看表的字段说明
4. **执行查询**：使用`execute_sql`执行SQL查询
   - 必须使用`ST_Area(geom::geography) / 1000000`计算面积
   - 必须使用`ST_Length(geom::geography) / 1000`计算长度
   - 查询boua表时必须使用`GROUP BY`和`ST_Union`合并
   - 必须查询所有相关图幅

## boua表最佳实践

1. **始终使用GROUP BY**：查询boua表时，如果查询某个行政区域，必须使用`GROUP BY name`或`GROUP BY pac`合并所有分割的部分

2. **使用ST_Union合并几何**：使用`ST_Union(geom)`将所有分割的几何部分合并成一个完整的几何对象

3. **查询所有相关图幅**：根据地理位置确定所有相关图幅，使用`tile_code IN (...)`查询所有图幅的数据

4. **检查分割情况**：使用`COUNT(*)`查看该区域被分割成几部分，如果`part_count > 1`，说明该区域被分割了

5. **使用PAC代码作为备选**：如果`name`字段为空，可以使用`pac`代码查询，相同行政区域的记录通常有相同的`pac`值

## 相关文档

- [字段说明文档](FIELD_SPEC.md) - 详细的字段说明
- [MCP服务指南](MCP_GUIDE.md) - MCP配置、工具使用和查询工作流程
- [图幅编号指南](TILE_CODE_GUIDE.md) - 如何确定图幅代码

