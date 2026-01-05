# 1:100万基础地理信息PostGIS MCP服务

**China 1M GeoData PostGIS MCP Service**

基于PostgreSQL/PostGIS的MCP（Model Context Protocol）服务，专门为**全国地理信息资源目录服务系统**下载的地理数据定制化开发。提供PostGIS空间数据的查询、分析和交互能力，支持1:100万公众版基础地理信息数据（2021）的导入和管理。

## 📋 项目简介

本项目是一个基于MCP协议的**PostGIS空间数据服务**，专门为全国地理信息资源目录服务系统的1:100万基础地理信息数据定制化开发，专注于提供PostgreSQL/PostGIS数据库的空间查询、分析和交互能力：

- ✅ **PostgreSQL/PostGIS**：数据导入到PostgreSQL，利用空间索引实现高性能查询
- ✅ **GDB格式支持**：支持导入GDB地理数据库文件
- ✅ **通用化配置**：通过JSON/YAML配置文件定义数据规格
- ✅ **自动检测**：自动识别数据规格
- ✅ **数据验证**：自动验证和修复无效几何
- ✅ **MCP标准**：符合Model Context Protocol标准，可与AI助手集成
- ✅ **SQL查询**：支持执行复杂SQL查询进行数据分析

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

### 核心定位

本项目是**1:100万基础地理信息PostGIS MCP服务**，主要功能包括：
- ✅ **PostGIS空间查询**：提供空间数据查询和分析能力
- ✅ **SQL执行**：支持执行PostGIS空间SQL查询
- ✅ **数据导入**：支持GDB等格式导入（为服务提供数据基础）
- ✅ **数据验证**：验证PostGIS数据的完整性和有效性

### 数据来源与定制

本项目专门为**全国地理信息资源目录服务系统**下载的地理数据定制化开发：

#### 1:100万公众版基础地理信息数据（2021）

- **数据范围**：覆盖全国陆地范围和包括台湾岛、海南岛、钓鱼岛、南海诸岛在内的主要岛屿及其临近海域
- **图幅数量**：共77幅1:100万标准图幅
- **现势性**：整体现势性为2019年
- **坐标系**：采用2000国家大地坐标系，1985国家高程基准，经纬度坐标
- **数据来源**：经自然资源部授权，全国地理信息资源目录服务系统提供免费下载服务
- **数据内容**：包含9个数据集
  - 水系
  - 居民地及设施
  - 交通
  - 管线
  - 境界与政区
  - 地貌与土质
  - 植被
  - 地名及注记
  - 定位基础（测量控制点、坐标网）

#### 数据格式

- **分发格式**：采用1:100万标准图幅分发，每个图幅为独立的GDB地理数据库文件
- **数据特点**：保存要素间空间关系和相关属性信息
- **扩展支持**：理论上也支持1:25万全国基础地理数据库

#### 定制化特性

- ✅ **数据规格配置**：内置1:100万数据规格配置（`china_1m_2021`）
- ✅ **自动识别**：自动识别图幅代码（F49、G49等）
- ✅ **图层映射**：自动映射GDB图层到PostgreSQL表
- ✅ **图幅管理**：支持多图幅数据统一管理和查询

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
在MCP客户端配置文件中添加：
```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

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

### 1. import_geodata

导入GDB地理数据到PostgreSQL/PostGIS数据库。此功能为1:100万基础地理信息PostGIS MCP服务提供数据基础，导入后可通过其他工具进行空间查询和分析。

**参数：**
- `data_path` (必需): GDB文件路径（.gdb目录）
- `spec_name` (可选): 数据规格名称，如果不提供则自动检测
- `database_config` (可选): 数据库连接配置，如果不提供则使用默认配置
- `options` (可选): 导入选项
  - `srid`: 目标坐标系SRID（默认4326）
  - `batch_size`: 批量插入大小（默认1000）
  - `skip_invalid`: 跳过无效几何（默认true）
  - `create_indexes`: 创建索引（默认true）

**注意：** 数据必须先导入PostgreSQL才能进行空间查询和分析。导入功能为1:100万基础地理信息PostGIS MCP服务提供数据基础。

### 2. verify_import

验证PostgreSQL/PostGIS中已导入的数据，检查数据完整性、坐标系、几何有效性等。

**参数：**
- `table_name` (可选): 要验证的表名，如果不提供则验证所有表
- `database_config` (可选): 数据库连接配置

### 3. query_data

查询PostgreSQL/PostGIS中的空间数据，支持空间过滤和属性过滤。

**参数：**
- `table_name` (必需): 表名
- `spatial_filter` (可选): 空间过滤条件
  - `bbox`: 边界框 [minx, miny, maxx, maxy]
  - `geometry`: WKT格式的几何对象
- `attribute_filter` (可选): 属性过滤条件
- `limit` (可选): 返回记录数限制（默认100）
- `database_config` (可选): 数据库连接配置

### 4. list_specs

列出所有可用的数据规格配置（用于数据导入）。

### 5. get_spec

获取指定数据规格的详细信息（用于数据导入）。

**参数：**
- `spec_name` (必需): 数据规格名称

### 6. register_spec

注册新的数据规格配置（用于数据导入）。

**参数：**
- `spec_name` (必需): 数据规格名称
- `spec_config` (必需): 数据规格配置（JSON对象）

### 7. list_tables

列出PostgreSQL/PostGIS数据库中所有包含空间数据的表。

**参数：**
- `database_config` (可选): 数据库连接配置

**返回：** 表列表，包含表名、记录数、坐标系等信息

### 8. execute_sql

在PostgreSQL/PostGIS数据库中执行SQL查询。支持PostGIS空间函数，用于复杂空间查询和分析。

**参数：**
- `sql` (必需): 要执行的SQL语句（仅支持SELECT查询）
- `database_config` (可选): 数据库连接配置

**注意：** 出于安全考虑，只允许执行SELECT查询语句。

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
├── scripts/                   # 工具脚本
│   ├── start_docker.bat       # Windows启动Docker
│   ├── start_docker.sh        # Linux/Mac启动Docker
│   ├── start_mcp.bat          # Windows启动MCP
│   ├── start_mcp.sh           # Linux/Mac启动MCP
│   ├── reset_database.py      # 重置数据库
│   ├── reset_database.bat      # Windows重置脚本
│   ├── reset_database.sh      # Linux/Mac重置脚本
│   ├── check_connection.py    # 测试数据库连接
│   ├── import_data.py         # 导入GDB数据
│   ├── verify_data.py         # 验证导入数据
│   ├── query_data.py          # 查询数据
│   ├── check_geometry_quality.py  # 检查几何质量
│   └── check_layers.py        # 检查GDB图层
├── examples/                  # 示例代码
│   ├── __init__.py
│   └── example_usage.py       # 使用示例
├── docs/                      # 文档目录
│   ├── DATA_SPEC.md           # 数据规格说明
│   └── QUICK_TEST.md          # 快速开发与测试
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

在支持MCP的AI助手中，可以直接调用工具：

**1. 导入数据（必须先执行）**

导入全国地理信息资源目录服务系统下载的1:100万图幅数据：
```
请导入 /path/to/F49.gdb 文件到PostgreSQL数据库，使用 china_1m_2021 规格
```

支持批量导入多个图幅，例如：
```
请导入 /path/to/gdb_directory 目录下的所有GDB文件
```

**2. 列出已导入的表**
```
列出PostgreSQL中所有已导入的地理数据表
```

**3. 验证数据**
```
验证 water_system_area 表的数据
```

**4. 查询数据**
```
查询 road 表中在边界框 [110, 20, 120, 30] 内的所有记录
```

**5. 执行复杂SQL查询**
```
执行SQL查询：SELECT COUNT(*) as count, tile_code FROM water_system_area GROUP BY tile_code
```

### 使用工具脚本

```bash
# 测试数据库连接
python scripts/check_connection.py

# 导入数据（支持指定GDB文件或目录）
python scripts/import_data.py <gdb_path>
python scripts/import_data.py --dir <directory>  # 批量导入目录中的所有GDB

# 验证数据
python scripts/verify_data.py

# 查询数据
python scripts/query_data.py

# 检查几何质量
python scripts/check_geometry_quality.py

# 检查GDB图层信息（支持指定GDB文件或目录）
python scripts/check_layers.py <gdb_path>
python scripts/check_layers.py --dir <directory>  # 批量检查目录中的所有GDB
```

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
- 使用 `import_geodata` 工具先导入数据
- 导入完成后才能使用 `query_data` 查询
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

- [数据规格说明](docs/DATA_SPEC.md) - 数据字段和规格说明
- [快速开发与测试](docs/QUICK_TEST.md) - 快速开发指南和测试步骤

---

**版本**: 1.0.0  
**最后更新**: 2026-01
