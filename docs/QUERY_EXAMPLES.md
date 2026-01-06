# 查询示例

本文档提供一些常用的PostGIS空间查询示例，帮助更好地使用MCP服务进行数据分析。

## 惠州市自然保护区查询示例

### 1. 查询植被区域（可能包含自然保护区）

```sql
-- 查询惠州市范围内的植被区域
SELECT 
    id,
    tile_code,
    ST_Area(geom::geography) / 1000000 as area_km2,
    ST_AsText(ST_Centroid(geom)) as centroid
FROM vegetation_area
WHERE geom && ST_MakeEnvelope(114.0, 22.7, 115.0, 23.8, 4326)
  AND ST_IsValid(geom)
ORDER BY ST_Area(geom::geography) DESC
LIMIT 20
```

### 2. 查询区域边界（可能包含保护区边界）

```sql
-- 查询惠州市范围内的区域边界
SELECT 
    id,
    tile_code,
    ST_Area(geom::geography) / 1000000 as area_km2,
    ST_AsText(ST_Centroid(geom)) as centroid
FROM regional_boundary_area
WHERE geom && ST_MakeEnvelope(114.0, 22.7, 115.0, 23.8, 4326)
  AND ST_IsValid(geom)
ORDER BY ST_Area(geom::geography) DESC
LIMIT 20
```

### 3. 查询自然地名（包含保护区名称）

```sql
-- 查询惠州市范围内的自然地名，查找包含"保护"、"自然"等关键词的记录
SELECT 
    id,
    tile_code,
    name,
    ST_AsText(geom) as location
FROM place_name_natural
WHERE geom && ST_MakeEnvelope(114.0, 22.7, 115.0, 23.8, 4326)
  AND (name LIKE '%保护%' OR name LIKE '%自然%' OR name LIKE '%公园%')
ORDER BY id
```

### 4. 综合查询：查找大面积的植被或区域（可能是保护区）

```sql
-- 查找惠州市范围内面积较大的植被区域和区域边界
-- 这些可能是自然保护区
SELECT 
    'vegetation' as source_type,
    id,
    tile_code,
    ST_Area(geom::geography) / 1000000 as area_km2,
    ST_AsText(ST_Centroid(geom)) as centroid
FROM vegetation_area
WHERE geom && ST_MakeEnvelope(114.0, 22.7, 115.0, 23.8, 4326)
  AND ST_IsValid(geom)
  AND ST_Area(geom::geography) / 1000000 > 1  -- 面积大于1平方公里

UNION ALL

SELECT 
    'regional_boundary' as source_type,
    id,
    tile_code,
    ST_Area(geom::geography) / 1000000 as area_km2,
    ST_AsText(ST_Centroid(geom)) as centroid
FROM regional_boundary_area
WHERE geom && ST_MakeEnvelope(114.0, 22.7, 115.0, 23.8, 4326)
  AND ST_IsValid(geom)
  AND ST_Area(geom::geography) / 1000000 > 1

ORDER BY area_km2 DESC
LIMIT 30
```

### 5. 查询特定区域的详细信息

```sql
-- 查询惠东县、博罗县、龙门县范围内的所有相关数据
-- 这些县有已知的自然保护区

-- 惠东县范围（大致）：经度 114.5° - 115.2°，纬度 22.7° - 23.2°
SELECT 
    'huidong' as area,
    'vegetation' as table_name,
    COUNT(*) as count,
    SUM(ST_Area(geom::geography) / 1000000) as total_area_km2
FROM vegetation_area
WHERE geom && ST_MakeEnvelope(114.5, 22.7, 115.2, 23.2, 4326)
  AND ST_IsValid(geom)

UNION ALL

SELECT 
    'boluo' as area,
    'vegetation' as table_name,
    COUNT(*) as count,
    SUM(ST_Area(geom::geography) / 1000000) as total_area_km2
FROM vegetation_area
WHERE geom && ST_MakeEnvelope(114.0, 23.0, 114.8, 23.6, 4326)
  AND ST_IsValid(geom)

UNION ALL

SELECT 
    'longmen' as area,
    'vegetation' as table_name,
    COUNT(*) as count,
    SUM(ST_Area(geom::geography) / 1000000) as total_area_km2
FROM vegetation_area
WHERE geom && ST_MakeEnvelope(114.0, 23.4, 114.6, 23.9, 4326)
  AND ST_IsValid(geom)
```

## 行政区域查询示例（boua表）

### 查询某个行政区域的完整面积

**重要提示**：boua表只包含区/县/县级市，不包含地级市。同一个行政区域可能被分割成多个记录，查询时必须合并。

```sql
-- 查询香洲区的完整面积（合并所有分割的部分）
SELECT 
    name,
    pac,
    COUNT(*) as part_count,  -- 该区域被分割成几部分
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2,
    ST_AsText(ST_Centroid(ST_Union(geom))) as centroid
FROM boua
WHERE name = '香洲区'
  AND tile_code IN ('F49', 'F50')  -- 根据地理位置确定图幅
GROUP BY name, pac;
```

### 查询某个空间范围内的所有行政区域

```sql
-- 查询珠海市范围内的所有行政区域（合并分割的部分）
SELECT 
    name,
    pac,
    COUNT(*) as part_count,
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2
FROM boua
WHERE geom && ST_MakeEnvelope(113.0, 22.0, 114.0, 22.5, 4326)
  AND tile_code IN ('F49', 'F50')
  AND ST_IsValid(geom)
GROUP BY name, pac
ORDER BY total_area_km2 DESC;
```

### 查询被分割成多部分的行政区域

```sql
-- 查找跨图幅或被分割的行政区域
SELECT 
    name,
    pac,
    COUNT(*) as part_count,
    array_agg(DISTINCT tile_code) as tile_codes,
    ST_Area(ST_Union(geom)::geography) / 1000000 as total_area_km2
FROM boua
WHERE name IS NOT NULL
GROUP BY name, pac
HAVING COUNT(*) > 1  -- 只显示被分割成多部分的区域
ORDER BY part_count DESC
LIMIT 20;
```

**详细说明**：请查看 [表使用指南](TABLE_USAGE_GUIDE.md) 中的boua表查询部分

## 注意事项

1. **数据限制**：1:100万基础地理信息数据的分辨率有限，可能无法完整标注所有自然保护区
2. **名称字段**：很多表的`name`字段可能为空，需要通过空间位置和面积来判断
3. **数据来源**：实际的自然保护区信息可能需要结合其他数据源（如官方保护区名录）
4. **空间范围**：惠州市大致范围：经度 114.0° - 115.0°，纬度 22.7° - 23.8°
5. **boua表特点**：boua表只包含区/县/县级市，不包含地级市；同一行政区域可能被分割成多个记录，查询时必须使用GROUP BY和ST_Union合并

## 建议的查询策略

1. **先查看表结构**：使用`verify_import`查看每个表的字段信息
2. **空间范围查询**：使用边界框查询特定区域的数据
3. **面积筛选**：筛选面积较大的区域（可能是保护区）
4. **多表联合**：结合多个表的数据进行综合分析
5. **结合地名**：使用`place_name_natural`和`place_name_residential`查找相关地名

