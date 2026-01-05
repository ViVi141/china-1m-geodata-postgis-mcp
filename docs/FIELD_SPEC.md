# 数据字段说明

本文档基于实际GDB图层分析结果生成，详细说明1:100万基础地理信息数据中所有表的字段含义，帮助LLM正确理解和使用字段。

## 说明

- **大部分字段说明**基于F49和G49图幅的实际数据分析生成，包含空值率统计和示例值
- **部分图层**（RESL、VEGL、PIPP）在分析图幅中未找到数据，字段说明基于数据规格推断
- 如需更完整的字段说明，建议分析更多图幅的GDB文件

## 通用字段

所有表都包含以下通用字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INTEGER | 主键，自动递增的唯一标识符 |
| `geom` | GEOMETRY | PostGIS几何对象，存储空间数据（点、线、面） |
| `tile_code` | VARCHAR(10) | 图幅代码，1:100万图幅编号（如F49、F50、G49、G50等） |

## 各表字段说明

### 交通

#### railway (铁路)

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：410101、410102、410103、430101、430102 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（空值率16.4%） |
| `rn` | VARCHAR(7) | 路线编号（Route Number），如国道、省道编号（注意：空值率52.4%，该字段可能经常为空） |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |
| `type` | VARCHAR(20) | 类型字段，存储要素的类型分类（注意：空值率56.7%，该字段可能经常为空），示例值：电、电/高架、高架、高铁、高铁/高架 |

#### road (公路)

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（空值率8.3%） |
| `rn` | VARCHAR(7) | 路线编号（Route Number），如国道、省道编号（空值率8.0%） |
| `rteg` | VARCHAR(4) | 道路等级（Road Grade），如一级、二级、三级、四级、等外（空值率7.3%） |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |
| `type` | VARCHAR(20) | 类型字段，存储要素的类型分类（注意：空值率100.0%，该字段可能经常为空） |

#### transport_facility_line (交通附属设施(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `brglev` | INTEGER | 桥梁等级（Bridge Level），1表示一级，2表示二级等（空值率39.7%），示例值：1、2 |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率65.9%，该字段可能经常为空） |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### transport_facility_point (交通附属设施(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `angle` | INTEGER | 角度，用于标注要素的旋转角度（度）（注意：空值率79.7%，该字段可能经常为空） |
| `brglev` | INTEGER | 桥梁等级（Bridge Level），1表示一级，2表示二级等（注意：空值率66.7%，该字段可能经常为空），示例值：1 |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（空值率44.0%） |
| `period` | VARCHAR(20) | 时期/时段信息，如河流的丰水期、枯水期等（注意：空值率99.9%，该字段可能经常为空），示例值：1-12 |
| `rn` | VARCHAR(7) | 路线编号（Route Number），如国道、省道编号（注意：空值率83.0%，该字段可能经常为空） |

### 地名及注记

#### place_name_natural (自然地名)

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `class` | VARCHAR(3) | 分类代码，用于标识地名或要素的分类 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空） |
| `pinyin` | VARCHAR(60) | 拼音字段，存储名称的拼音（通常为空）（注意：空值率100.0%，该字段可能经常为空） |

#### place_name_residential (居民地地名)

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `class` | VARCHAR(3) | 分类代码，用于标识地名或要素的分类 |
| `gnid` | VARCHAR(12) | 地名ID（Geographic Name ID），12位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空） |
| `pinyin` | VARCHAR(60) | 拼音字段，存储名称的拼音（通常为空）（注意：空值率100.0%，该字段可能经常为空） |
| `xzname` | VARCHAR(60) | 行政名称，所属行政区划名称（注意：空值率90.5%，该字段可能经常为空） |

### 地貌与土质

#### terrain_area (地貌与土质(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：750702 |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里，示例值：0.00115206248255013、0.0014829958295131023 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算，示例值：0.1776200202851556、0.22826568620869844 |

#### terrain_line (地貌与土质(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `elev` | DOUBLE PRECISION | 高程值（Elevation），单位：米（空值率0.2%），示例值：1000.0、200.0、50.0、500.0 |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：710101、710106、750600 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### terrain_point (地貌与土质(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `angle` | INTEGER | 角度，用于标注要素的旋转角度（度）（注意：空值率91.2%，该字段可能经常为空） |
| `elev` | DOUBLE PRECISION | 高程值（Elevation），单位：米（空值率12.9%） |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：720100、750101、750300 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率92.5%，该字段可能经常为空） |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

### 境界与政区

#### administrative_boundary_area (行政境界(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（空值率3.6%） |
| `pac` | INTEGER | 属性分类代码（Property Attribute Code），用于标识要素的分类 |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### administrative_boundary_line (行政境界(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### administrative_boundary_point (行政境界(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `bno` | VARCHAR(12) | 边界编号（Boundary Number），用于标识边界点，示例值：佳蓬列岛、围夹岛、大帆石 |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：620600 |

#### regional_boundary_area (区域界线(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：670101 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空） |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### regional_boundary_line (区域界线(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：670102 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### regional_boundary_point (区域界线(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：670101 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空） |

### 定位基础

#### control_points (测量控制点)

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |

#### coordinate_grid (坐标网)

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：120100、120300、120400、120401 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

### 居民地及设施

#### facility_area (设施(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：321200、330300 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率100.0%，该字段可能经常为空） |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### facility_line (设施(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空） |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### facility_point (设施(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（空值率21.5%） |

#### residential_area (居民地(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：310200 |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### residential_line (居民地(线))

**几何类型**: MultiLineString

**注意**: 该图层在F49和G49图幅中未找到数据，以下字段说明基于数据规格推断。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### residential_point (居民地(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `angle` | INTEGER | 角度，用于标注要素的旋转角度（度）（注意：空值率99.8%，该字段可能经常为空），示例值：0、52 |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |

### 植被

#### vegetation_area (植被(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |
| `type` | VARCHAR(20) | 类型字段，存储要素的类型分类（注意：空值率98.3%，该字段可能经常为空），示例值：桔、灌、疏 |

#### vegetation_line (植被(线))

**几何类型**: MultiLineString

**注意**: 该图层在F49和G49图幅中未找到数据，以下字段说明基于数据规格推断。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### vegetation_point (植被(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |

### 水系

#### water_facility_area (水系附属设施(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：250400 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率100.0%，该字段可能经常为空） |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### water_facility_line (水系附属设施(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率78.9%，该字段可能经常为空） |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### water_facility_point (水系附属设施(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率98.0%，该字段可能经常为空），示例值：三叉塘副坝、大良水库西干渡槽、峰江水闸、铁岗分洪闸 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### water_system_area (水系(面))

**几何类型**: MultiPolygon

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `hydc` | VARCHAR(8) | 水系代码（Hydrography Code），用于标识水系要素的唯一代码（注意：空值率85.8%，该字段可能经常为空） |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率85.8%，该字段可能经常为空） |
| `period` | VARCHAR(20) | 时期/时段信息，如河流的丰水期、枯水期等（注意：空值率100.0%，该字段可能经常为空） |
| `shape_area` | DOUBLE PRECISION | 几何形状的面积（度²），使用PostGIS的ST_Area计算，需转换为平方公里 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |
| `vol` | VARCHAR(2) | 容量/规模，如水库的容量等级（大、中、小）（注意：空值率90.5%，该字段可能经常为空），示例值：中、大 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### water_system_line (水系(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `hydc` | VARCHAR(8) | 水系代码（Hydrography Code），用于标识水系要素的唯一代码（注意：空值率54.0%，该字段可能经常为空） |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率53.3%，该字段可能经常为空） |
| `period` | VARCHAR(20) | 时期/时段信息，如河流的丰水期、枯水期等（注意：空值率99.8%，该字段可能经常为空），示例值：5-9 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

#### water_system_point (水系(点))

**几何类型**: Point

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `angle` | INTEGER | 角度，用于标注要素的旋转角度（度）（空值率19.8%） |
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码，示例值：240101、250700、260200、260700、260800 |
| `name` | VARCHAR(60) | 名称字段，存储要素的中文名称（可能为空）（注意：空值率80.0%，该字段可能经常为空） |

**重要提示**: `name`字段空值率较高，不能仅通过名称查询，建议结合空间查询和`pac`/`gb`等分类代码使用。

### 管线

#### pipeline (管线(线))

**几何类型**: MultiLineString

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
| `shape_length` | DOUBLE PRECISION | 几何形状的边界长度（度），使用PostGIS的ST_Length计算 |

#### pipeline_point (管线(点))

**几何类型**: Point

**注意**: 该图层在F49和G49图幅中未找到数据，以下字段说明基于数据规格推断。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `gb` | INTEGER | GB/T 2260-2007 中华人民共和国行政区划代码，6位数字代码 |
