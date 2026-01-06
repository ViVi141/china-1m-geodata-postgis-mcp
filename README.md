# 1:100万基础地理信息PostGIS MCP服务

**China 1M GeoData PostGIS MCP Service**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-2.5+-green.svg)](https://postgis.net/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个专为**全国地理信息资源目录服务系统**的1:100万基础地理信息数据设计的PostGIS MCP服务，通过Model Context Protocol（MCP）协议让AI助手能够直接访问和查询PostgreSQL/PostGIS中的空间地理数据。

## 📋 项目简介

本项目是一个**企业级PostGIS空间数据MCP服务**，专注于将1:100万公众版基础地理信息数据（2021）导入PostgreSQL/PostGIS，并通过MCP协议提供强大的空间查询、分析和交互能力。项目支持Docker一键部署，提供完整的工具链，让地理数据查询变得简单高效。

### 🌟 核心特性

- 🚀 **MCP协议集成**：符合Model Context Protocol标准，可与Claude、GPT等AI助手无缝集成
- 🗄️ **统一表结构**：智能设计统一表结构，支持多图幅数据统一管理和查询
- ⚡ **高性能查询**：基于PostgreSQL/PostGIS空间索引（GIST），实现毫秒级空间查询
- 🔧 **一键部署**：支持Docker Compose一键部署，包含PostgreSQL、MCP服务、Supergateway网关
- 📊 **完整工具链**：提供从数据解析、表结构设计、数据导入到验证的完整工具集
- 🛡️ **数据质量保障**：自动验证和修复无效几何，确保数据完整性
- 📚 **详细文档**：提供完整的文档体系，包括字段说明、表用途指南、查询示例等
- 🌐 **远程访问**：支持Supergateway网关，实现HTTP/SSE/WebSocket远程访问

### 与PostgreMCP的区别

**PostgreMCP** 专注于数据库管理和优化（分析、调试、配置），而**我们的服务**专注于PostGIS空间数据操作：

| 功能 | PostgreMCP | 我们的服务 |
|------|-----------|-----------|
| 数据库管理 | ✅ 分析、优化、调试 | ❌ |
| PostGIS空间查询 | ❌ | ✅ 空间查询、空间分析 |
| 地理数据导入 | ❌ | ✅ GDB导入到PostGIS（为服务提供数据） |
| SQL查询 | ❌ | ✅ 支持PostGIS空间SQL查询 |
| PostGIS支持 | ❌ | ✅ 专门支持PostGIS |

**两个服务可以互补使用**：使用我们的服务进行PostGIS空间数据查询和分析，使用PostgreMCP优化数据库性能。

### 💡 使用场景

- 🤖 **AI助手集成**：让Claude、GPT等AI助手能够理解和查询中国地理数据
- 🗺️ **地理信息查询**：快速查询行政区划、水系、交通等地理要素
- 📊 **空间分析**：进行缓冲区分析、空间相交、距离计算等复杂空间分析
- 🔍 **地理位置定位**：根据经纬度查询周边地理要素，或根据地名查找坐标
- 📈 **数据可视化**：为GIS应用、地图服务提供后端数据支持
- 🏛️ **政务应用**：支持政务系统中对地理数据的查询和分析需求

### 核心功能

- ✅ **空间数据查询**：支持空间过滤、属性过滤、复杂空间分析查询
- ✅ **PostGIS SQL执行**：支持所有PostGIS空间函数（ST_Area、ST_Distance、ST_Buffer等）
- ✅ **GDB数据导入**：支持批量导入GDB格式地理数据库，自动识别图幅代码
- ✅ **统一表结构**：智能解析并创建统一表结构，多图幅数据共享表设计
- ✅ **数据验证**：自动验证几何有效性，修复无效几何，统计导入结果
- ✅ **图幅管理**：自动识别和管理1:100万标准图幅代码（F49、G50等）
- ✅ **字段说明**：自动生成字段说明文档，帮助理解数据含义

### 📍 数据来源与定制

本项目专门为**全国地理信息资源目录服务系统**的1:100万公众版基础地理信息数据（2021）定制化开发，经过深度优化，可直接用于生产环境。

#### 数据概况

**1:100万公众版基础地理信息数据（2021）**
- 📦 **覆盖范围**：全国陆地及主要岛屿（台湾岛、海南岛、钓鱼岛、南海诸岛等）
- 🗺️ **图幅数量**：77幅1:100万标准图幅
- 📅 **数据现势性**：2019年
- 🌐 **坐标系**：2000国家大地坐标系（CGCS2000），1985国家高程基准，经纬度坐标（SRID: 4326）
- 📊 **数据来源**：自然资源部授权，全国地理信息资源目录服务系统免费提供

**9大地理要素数据集**：
1. 🌊 **水系**：河流、湖泊、水库等水体要素
2. 🏘️ **居民地及设施**：城市、乡镇、村庄等居住区域
3. 🛣️ **交通**：公路、铁路、机场等交通设施
4. 🔌 **管线**：输油管道、输电线路等管线要素
5. 🗺️ **境界与政区**：省、市、县等行政边界
6. ⛰️ **地貌与土质**：地形、地质特征
7. 🌳 **植被**：森林、草地等植被覆盖
8. 📍 **地名及注记**：地名、地理标注信息
9. 📐 **定位基础**：测量控制点、坐标网格

#### 项目优势

- 🎯 **开箱即用**：内置完整的数据规格配置（`china_1m_2021`），无需手动配置
- 🤖 **智能识别**：自动识别图幅代码（F49、G50等），自动提取图幅信息
- 🔄 **统一管理**：统一的表结构设计，多图幅数据无缝整合
- 📋 **完整工具链**：从数据解析到导入验证的完整自动化流程
- 🔍 **字段说明**：自动生成字段说明文档，降低使用门槛

### 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    AI助手 (Claude/GPT)                   │
│                  通过MCP协议通信                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              MCP服务器 (mcp_server.py)                   │
│  • list_tile_codes  • list_tables  • verify_import     │
│  • query_data  • execute_sql                            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│          PostgreSQL/PostGIS 数据库                       │
│  • 空间索引(GIST)  • 空间数据类型  • PostGIS函数        │
│  • 统一表结构  • 多图幅数据整合                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              数据导入工具链                              │
│  • parse_tile_schema  • create_unified_schema          │
│  • import_all_tiles  • verify_data                      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            GDB地理数据库文件 (1:100万)                   │
│  F49.gdb  F50.gdb  G49.gdb  G50.gdb ... (77幅)         │
└─────────────────────────────────────────────────────────┘
```

**部署方式**：
- 🐳 **Docker部署**（推荐）：使用docker-compose一键部署，支持本地和远程访问
- 💻 **本地部署**：直接运行Python脚本，适合开发和测试环境

## 🚀 快速开始

### 系统要求

- **Python 3.8+**
- **PostgreSQL 9.5+** (推荐PostgreSQL 12+) - **必需**
- **PostGIS 2.5+** 扩展 - **必需**
- **GDAL/OGR库**（用于读取GDB文件）

### 1. 安装依赖

#### Windows (推荐使用conda)
```bash
conda install -c conda-forge gdal fiona shapely psycopg2
pip install -r requirements.txt
```

#### Linux/Mac
```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev python3-gdal

# 或使用conda
conda install -c conda-forge gdal fiona shapely psycopg2

pip install -r requirements.txt
```

### 2. 配置数据库

#### 方式1：使用Docker（推荐）

**使用Docker Compose：**
```bash
# 复制docker-compose.yml
# 设置密码（可选，默认postgres）
export POSTGRES_PASSWORD=your_password

# 启动PostgreSQL/PostGIS
docker-compose up -d

# 查看日志
docker-compose logs -f postgres
```

**Docker Compose会自动：**
- 创建数据库 `gis_data`
- 启用PostGIS扩展
- 配置数据持久化

详见 `docker-compose.yml` 和 `init.sql`

**使用1Panel部署（推荐1Panel用户）：**

如果您使用1Panel管理服务器，可以使用1Panel的可视化MCP服务配置：
1. 先启动基础服务：`docker-compose up -d`
2. 在1Panel中添加MCP服务，类型选择 `npx`，启动命令填写：`docker exec -i geodata-mcp-server python /app/mcp_server.py`
3. 详细配置说明请查看 [Docker快速开始指南](README_DOCKER.md#方式3基础版--1panel-mcp服务推荐用于1panel用户)

#### 方式2：本地PostgreSQL

**创建数据库和启用PostGIS：**
```sql
CREATE DATABASE gis_data;
\c gis_data
CREATE EXTENSION postgis;
```

### 3. 配置连接信息

```bash
# 复制配置模板
cp config/database.ini.example config/database.ini

# 编辑配置文件，填写数据库连接信息
# Windows: notepad config/database.ini
# Linux/Mac: nano config/database.ini
```

### 4. 运行MCP服务器

#### 作为MCP服务器运行
```bash
# 激活虚拟环境（如果使用）
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 启动MCP服务器
python mcp_server.py
```

#### 在MCP客户端中配置

在MCP客户端配置文件中添加配置。详细配置说明请查看 [MCP服务完整指南](docs/MCP_GUIDE.md)。

**基本配置示例（使用绝对路径）：**

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "python",
      "args": [
        "C:/Users/YourUsername/Desktop/gdb_mcp/mcp_server.py"
      ],
      "cwd": "C:/Users/YourUsername/Desktop/gdb_mcp"
    }
  }
}
```

**使用虚拟环境（推荐）：**

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

**注意：**
- 必须使用**绝对路径**
- 推荐设置 `cwd` 为项目根目录
- 推荐使用虚拟环境
- **Docker 部署用户**：请查看 [Docker 部署后的 MCP 配置指南](docs/MCP_DOCKER_CONFIG.md) ⭐
- 详细配置说明和常见问题请查看 [MCP服务完整指南](docs/MCP_GUIDE.md)

## 📊 数据规格配置

### 默认规格

项目已内置**1:100万公众版基础地理信息数据（2021）**的完整规格配置（`specs/china_1m_2021.json`），包含所有9个数据集的图层映射配置。

### 创建自定义规格

创建JSON或YAML格式的规格配置文件：

```json
{
  "name": "my_custom_spec",
  "description": "自定义数据规格",
  "version": "1.0.0",
  "default_srid": 4326,
  "tile_code_pattern": "auto",
  "layer_mapping": {
    "LAYER1": {
      "table_name": "custom_table_1",
      "description": "图层1描述",
      "category": "分类1"
    }
  }
}
```

保存到 `specs/` 目录，即可在MCP服务中使用。

## 🛠️ MCP工具

**注意：MCP服务专注于数据查询和分析，不提供数据导入功能。数据导入应使用脚本完成。**

**推荐工作流程（统一表结构）：**

**方式1：使用统一工具集（最简单）⭐⭐⭐**
```bash
python scripts/setup_unified_database.py
```

**方式2：分步执行**
1. 使用 `scripts/parse_tile_schema.py` 解析图幅结构
2. 使用 `scripts/create_unified_schema.py` 创建统一表结构
3. 使用 `scripts/import_all_tiles.py` 导入所有图幅数据

详细说明请查看 [统一表结构导入指南](docs/UNIFIED_SCHEMA_GUIDE.md)。

**重要提示：**
1. **查询前必须先使用 `list_tile_codes` 查看有哪些图幅可用**，然后根据目的地地理位置确定需要查询的图幅。不要只查询F49图幅！详细说明请查看 [图幅编号指南](docs/TILE_CODE_GUIDE.md)。
2. **查询前必须先使用 `verify_import` 查看字段说明**，了解每个字段的含义，不要猜测字段含义。详细字段说明请查看 [字段说明文档](docs/FIELD_SPEC.md)。

### 1. list_tile_codes

列出数据库中所有已导入的图幅代码。**这是查询数据的第一步，必须先执行！**图幅编号是全球通用的1:100万图幅编号（如F49、F50、G49、G50等），每个图幅覆盖约6°×4°的地理范围。根据查询目的地的地理位置确定需要查询的图幅，例如：惠州市主要在F49和F50图幅，广州市主要在F49图幅。

**参数：**
- `database_config` (可选): 数据库连接配置

**返回：** 图幅代码列表，包含每个图幅在各表中的记录数统计

### 2. list_tables

列出PostgreSQL/PostGIS数据库中所有已导入的地理数据表。返回每个表的名称、记录数、坐标系(SRID)等信息。**在查询数据之前，应该先使用此工具查看可用的表，不要盲目猜测表名。**

**参数：**
- `database_config` (可选): 数据库连接配置

**返回：** 表列表，包含表名、记录数、坐标系等信息

### 3. verify_import

验证PostgreSQL/PostGIS中已导入的数据，检查数据完整性、坐标系、几何有效性、空间范围等。返回每个表的记录数、坐标系(SRID)、边界框(bbox)、无效几何数量、字段信息（包含字段说明）等。**这是了解表结构和字段含义的重要工具，在查询数据前必须先使用此工具查看字段说明，不要猜测字段含义。**详细字段说明请查看 [字段说明文档](docs/FIELD_SPEC.md)。

**参数：**
- `table_name` (可选): 要验证的表名（建议先使用list_tables查看可用表），如果不提供则验证所有表
- `database_config` (可选): 数据库连接配置

### 4. query_data

查询PostgreSQL/PostGIS中的空间数据，支持空间过滤和属性过滤。**适用于简单的空间查询，如：按边界框查询、按几何相交查询、按属性过滤等。对于复杂的空间分析（如计算面积、距离、缓冲区、空间连接等），应使用execute_sql工具配合PostGIS函数。**

**参数：**
- `table_name` (必需): 表名（必须先使用list_tables查看可用表）
- `spatial_filter` (可选): 空间过滤条件
  - `bbox`: 边界框 [minx, miny, maxx, maxy]，单位为度（经纬度）
  - `geometry`: WKT格式的几何对象，如 'POINT(113.3 23.1)' 或 'POLYGON((...))'
- `attribute_filter` (可选): 属性过滤条件，键值对形式，如 {"tile_code": "F49"}
- `limit` (可选): 返回记录数限制（默认100）
- `database_config` (可选): 数据库连接配置

### 5. execute_sql

在PostgreSQL/PostGIS数据库中执行SQL查询。**这是进行复杂空间分析和计算的主要工具。**支持所有PostGIS空间函数，如：ST_Area(计算面积)、ST_Distance(计算距离)、ST_Buffer(缓冲区)、ST_Intersects(相交判断)、ST_Within(包含判断)、ST_Union(合并)、ST_Intersection(求交)、ST_Centroid(中心点)、ST_Envelope(边界框)等。

**适用场景：**
- 空间分析（面积、距离、缓冲区、空间关系判断）
- 空间计算（合并、求交、简化、转换坐标系）
- 复杂查询（多表连接、聚合统计、空间分组）
- 数据统计（按区域统计、按图幅统计等）

**参数：**
- `sql` (必需): 要执行的SQL SELECT语句。可以使用PostGIS空间函数，例如：
  - 计算面积：`ST_Area(geom::geography)/1000000`（转换为平方公里）
  - 计算距离：`ST_Distance(geom1::geography, geom2::geography)/1000`（转换为公里）
  - 空间过滤：`ST_Intersects(geom1, geom2)` 或 `geom && ST_MakeEnvelope(...)`
- `database_config` (可选): 数据库连接配置

**注意：** 出于安全考虑，只允许执行SELECT查询语句。详细的使用指南和PostGIS函数参考请查看 [MCP服务完整指南](docs/MCP_GUIDE.md)。

## 📁 项目结构

```
.
├── mcp_server.py              # MCP服务器主文件
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── config_manager.py      # 配置管理
│   ├── spec_loader.py         # 规格加载器
│   ├── data_importer.py       # 数据导入器
│   └── gdb_importer.py        # GDB导入器
├── specs/                     # 数据规格配置
│   └── china_1m_2021.json     # 1:100万数据规格
├── config/                    # 配置文件
│   ├── database.ini.example  # 数据库配置模板
│   └── database.ini          # 数据库配置（不提交）
├── scripts/                   # 工具脚本（详见 scripts/README.md）
│   ├── setup_unified_database.py  # ⭐⭐⭐ 统一工具集（强烈推荐）
│   ├── parse_tile_schema.py   # ⭐ 完全解析图幅结构
│   ├── create_unified_schema.py  # ⭐ 创建统一表结构
│   ├── import_all_tiles.py    # ⭐ 导入所有图幅数据
│   ├── check.py               # ⭐ 统一检查工具（连接/图层/几何质量）
│   ├── generate_field_spec.py # 生成字段说明文档
│   ├── verify_data.py         # 验证导入数据
│   ├── reset_database.py      # 重置数据库
│   ├── start_mcp.bat/sh       # 启动MCP（Windows/Linux）
│   └── start-supergateway.bat/sh  # 启动Supergateway（Windows/Linux）
├── examples/                  # 示例代码
│   ├── __init__.py
│   └── example_usage.py       # 使用示例
├── docs/                      # 文档目录
│   ├── UNIFIED_SCHEMA_GUIDE.md  # ⭐ 统一表结构导入指南
│   ├── MCP_GUIDE.md            # ⭐ MCP服务完整指南（配置、工具使用、查询流程）
│   ├── MCP_DOCKER_CONFIG.md    # ⭐ Docker部署后的MCP配置指南
│   ├── FIELD_SPEC.md           # 字段说明文档
│   ├── TABLE_USAGE_GUIDE.md    # ⭐ 表用途和单位转换指南（重要）
│   ├── TILE_CODE_GUIDE.md     # 图幅编号指南
│   ├── QUERY_EXAMPLES.md       # 查询示例
│   ├── DOCKER_GUIDE.md         # Docker编排使用指南
│   ├── DOCKER_LINUX_DEPLOY.md  # Linux Docker完整部署指南
│   └── DOCKER_WINDOWS_DEPLOY.md # Windows Docker部署指南
├── docker-compose.yml         # Docker Compose配置
├── docker-compose.alpine.yml  # Alpine版本配置
├── init.sql                   # 数据库初始化脚本
├── requirements.txt           # Python依赖
├── package.json               # MCP服务配置
├── .gitignore                 # Git忽略文件
└── README.md                  # 本文件
```

## 🔧 技术特性

### 1:100万基础地理信息PostGIS MCP服务核心能力
- ⚡ **高性能空间查询**：利用PostgreSQL的空间索引（GIST）实现快速空间查询
- 🔍 **复杂空间分析**：支持PostGIS空间函数，进行复杂的空间分析和计算
- 👥 **并发访问**：支持多用户同时进行空间查询
- 📊 **数据管理**：ACID事务、数据完整性、备份恢复
- 🗺️ **空间数据支持**：完整支持PostGIS空间数据类型和函数

### 坐标系支持
- **1:100万数据**：采用2000国家大地坐标系，1985国家高程基准，经纬度坐标（SRID: 4326）
- **默认坐标系**：WGS84 (SRID: 4326)
- **支持自定义坐标系**：可通过配置指定目标坐标系
- **自动坐标系转换**：支持坐标系自动转换

### 数据导入功能（为服务提供数据）
- ✅ 支持GDB格式导入
- ✅ 自动验证几何有效性
- ✅ 自动修复无效几何（使用buffer(0)方法）
- ✅ 跳过无法修复的记录并统计
- ✅ 自动清理字段名，符合PostgreSQL命名规范
- ✅ 批量插入（可配置批量大小）
- ✅ 自动创建空间索引（GIST）
- ✅ 自动创建图幅代码索引
- ✅ 导入后自动运行ANALYZE优化统计信息
- ✅ 详细的进度日志，实时显示导入状态

## 📝 使用示例

### 通过MCP客户端调用

在支持MCP的AI助手中，可以直接调用工具进行数据查询和分析：

**注意：数据导入应使用脚本完成，不在MCP服务中提供。**

**推荐导入方式（统一表结构）：**

**方式1：使用统一工具集（推荐）⭐⭐⭐**
```bash
# 一键完成所有步骤
python scripts/setup_unified_database.py
```

**方式2：分步执行**
```bash
# 1. 解析图幅结构
python scripts/parse_tile_schema.py F49.gdb --output analysis

# 2. 创建统一表结构
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json

# 3. 导入所有图幅数据
python scripts/import_all_tiles.py
```

详细说明请查看 [统一表结构导入指南](docs/UNIFIED_SCHEMA_GUIDE.md)。

**1. 列出图幅代码（必须先执行）**

查看数据库中有哪些图幅可用：
```
列出数据库中所有已导入的图幅代码
```

**2. 列出已导入的表**
```
列出PostgreSQL中所有已导入的地理数据表
```

**3. 验证数据**
```
验证 water_system_area 表的数据
```

**3. 查询数据**
```
查询 road 表中在边界框 [110, 20, 120, 30] 内的所有记录
```

**4. 执行复杂SQL查询**
```
执行SQL查询：SELECT COUNT(*) as count, tile_code FROM water_system_area GROUP BY tile_code
```

### 使用工具脚本

**推荐工作流程（统一表结构）：**

**方式1：使用统一工具集（推荐）⭐⭐⭐**
```bash
# 一键完成所有步骤
python scripts/setup_unified_database.py

# 验证数据
python scripts/verify_data.py
```

**方式2：分步执行**
```bash
# 1. 解析图幅结构（首次设置）
python scripts/parse_tile_schema.py F49.gdb --output analysis

# 2. 创建统一表结构
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json

# 3. 导入所有图幅数据
python scripts/import_all_tiles.py

# 4. 验证数据
python scripts/verify_data.py
```

**其他常用脚本：**

```bash
# 统一检查工具（推荐）
python scripts/check.py --connection    # 检查数据库连接和PostGIS
python scripts/check.py --layers F49.gdb  # 检查GDB图层信息
python scripts/check.py --geometry      # 检查几何数据质量
python scripts/check.py --all           # 执行所有检查

# 验证数据
python scripts/verify_data.py

# 重置数据库
python scripts/reset_database.py
```

**详细说明：**
- 统一表结构导入：查看 [统一表结构导入指南](docs/UNIFIED_SCHEMA_GUIDE.md)
- 脚本功能说明：查看 [scripts/README.md](scripts/README.md)

## 🛠️ 故障排除

### 问题1: 无法读取.gdb文件
**解决方案**: 
- 确保已安装GDAL并支持FileGDB驱动
- 检查: `python -c "import fiona; print(fiona.supported_drivers)"`

### 问题2: 连接PostgreSQL失败
**解决方案**:
- 检查PostgreSQL服务是否运行
- 验证config/database.ini中的连接信息
- 检查防火墙设置

### 问题3: PostGIS扩展不可用
**解决方案**:
- 确保PostgreSQL服务器上已安装PostGIS
- 在数据库中执行: `CREATE EXTENSION postgis;`
- Docker环境: 参考上面的Docker安装步骤

### 问题4: MCP库导入错误
**解决方案**:
- 确保已安装MCP库: `pip install mcp`
- 检查Python版本（需要3.8+）

### 问题5: 数据必须先导入才能查询
**解决方案**:
- 使用 `scripts/setup_unified_database.py` 或 `scripts/import_all_tiles.py` 导入数据
- 导入完成后才能使用MCP服务的 `query_data` 工具查询
- 使用 `list_tables` 查看已导入的表

### 问题6: 导入时没有进度显示
**解决方案**:
- 检查日志输出（输出到stderr）
- 确保日志级别设置为INFO
- 查看终端输出，日志会实时显示进度

## 📄 许可证

MIT License

## 👤 作者

**ViVi141**  
Email: 747384120@qq.com

## 🤝 贡献

欢迎提交Issue和Pull Request。

## 📚 相关文档

### 核心文档（必读）
- [统一表结构导入指南](docs/UNIFIED_SCHEMA_GUIDE.md) - ⭐ **推荐**：统一表结构创建和导入指南
- [MCP服务完整指南](docs/MCP_GUIDE.md) - ⭐ **重要**：MCP配置、工具使用和查询工作流程的完整指南

### 参考文档
- [表用途和单位转换指南](docs/TABLE_USAGE_GUIDE.md) - **⭐ 重要：各表用途速查表和单位转换方法，包含boua表查询指南，帮助LLM避免常见错误**
- [字段说明文档](docs/FIELD_SPEC.md) - **所有表的字段详细说明，帮助LLM正确理解字段含义，避免猜测**
- [图幅编号指南](docs/TILE_CODE_GUIDE.md) - **1:100万图幅编号说明，如何根据地理位置确定图幅**
- [查询示例](docs/QUERY_EXAMPLES.md) - **常用PostGIS空间查询示例，包含自然保护区查询等实际案例**

### Docker部署文档
- [Docker快速开始指南](README_DOCKER.md) - **Docker快速启动指南**
- [Docker编排使用指南](docs/DOCKER_GUIDE.md) - **Docker Compose详细使用说明**
- [Docker部署后的MCP配置指南](docs/MCP_DOCKER_CONFIG.md) - **⭐ Docker部署后的MCP客户端配置**
- [Linux Docker完整部署指南](docs/DOCKER_LINUX_DEPLOY.md) - **Linux系统完整部署步骤（含Supergateway）**
- [Windows Docker部署指南](docs/DOCKER_WINDOWS_DEPLOY.md) - **Windows系统Docker部署步骤（含Supergateway）**

### 开发和测试文档
- [脚本说明](scripts/README.md) - 所有脚本的功能说明和使用方法

---

**版本**: 1.0.0  
**最后更新**: 2026-01
