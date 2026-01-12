# Scripts 目录说明

本目录包含项目所需的各种工具脚本，按功能分类如下：

## 🚀 统一工具集（推荐）

### setup_unified_database.py ⭐⭐⭐ **强烈推荐**
**统一的分析导入工具集**，整合了所有步骤，一键完成从解析到导入的完整流程。

**功能**：
- 自动执行：解析图幅结构 → 创建统一表结构 → 导入所有图幅数据
- 支持跳过某些步骤（如果已执行过）
- 自动查找参考图幅和GDB文件
- 完整的进度显示和错误处理

**使用示例**：
```bash
# 完整流程（自动执行所有步骤）
python scripts/setup_unified_database.py

# 指定参考图幅和GDB目录
python scripts/setup_unified_database.py --reference-gdb F49.gdb --gdb-dir .

# 只执行导入步骤（表结构已创建）
python scripts/setup_unified_database.py --skip-parse --skip-create

# 强制重新创建表结构
python scripts/setup_unified_database.py --force

# 自定义参数
python scripts/setup_unified_database.py --srid 4326 --batch-size 2000
```

**选项说明**：
- `--reference-gdb, -r`: 参考图幅GDB路径（默认自动查找F49.gdb）
- `--gdb-dir, -d`: 包含所有GDB文件的目录（默认: 当前目录）
- `--output, -o`: 分析结果输出目录（默认: analysis/）
- `--srid`: 坐标系SRID（默认: 4326）
- `--batch-size`: 批量插入大小（默认: 1000）
- `--force, -f`: 强制重新创建表（会删除已存在的表）
- `--skip-parse`: 跳过解析步骤（使用已有分析结果）
- `--skip-create`: 跳过创建表结构步骤
- `--skip-import`: 跳过导入数据步骤

**相关文档**：`docs/UNIFIED_SCHEMA_GUIDE.md`

---

## 📊 数据分析和结构设计

### parse_tile_schema.py ⭐ **推荐**
完全解析图幅的所有图层和所有字段，从零设计全新的表结构。

**用途**：
- 分析GDB图幅的完整结构
- 生成PostgreSQL表结构设计
- 生成表结构SQL和摘要文档

**使用示例**：
```bash
python scripts/parse_tile_schema.py F49.gdb --output analysis
```

**输出**：
- `{tile_code}_complete_analysis.json` - 完整分析结果
- `{tile_code}_table_designs.sql` - 表结构SQL
- `{tile_code}_table_summary.md` - 表结构摘要

### generate_field_spec.py
基于分析结果生成字段说明文档。

**使用示例**：
```bash
python scripts/generate_field_spec.py analysis/F49_complete_analysis.json docs/FIELD_SPEC.md
```

## 🗄️ 数据库表结构管理

### create_unified_schema.py ⭐ **重要**
基于分析结果创建统一的PostGIS表结构（所有图幅共享）。

**用途**：
- 创建所有图幅共享的统一表结构
- 自动创建索引和约束
- 支持强制重新创建

**使用示例**：
```bash
# 创建统一表结构
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json

# 强制重新创建（会删除已存在的表）
python scripts/create_unified_schema.py --force
```

**相关文档**：`docs/UNIFIED_SCHEMA_GUIDE.md`

## 📥 数据导入

### import_all_tiles.py ⭐ **推荐**
导入所有图幅的数据到统一表结构。

**用途**：
- 批量导入所有图幅数据
- 自动提取图幅代码
- 批量插入优化

**使用示例**：
```bash
# 导入当前目录下的所有GDB文件
python scripts/import_all_tiles.py

# 导入指定目录
python scripts/import_all_tiles.py --gdb-dir .

# 只导入单个文件
python scripts/import_all_tiles.py --gdb F49.gdb
```

**相关文档**：`docs/UNIFIED_SCHEMA_GUIDE.md`

## 🔍 数据查询和验证

### verify_data.py
验证已导入的数据完整性。

**使用示例**：
```bash
python scripts/verify_data.py
```

### check.py ⭐ **推荐**
统一检查工具，整合了数据库连接检查、GDB图层检查和几何数据质量检查。

**功能**：
- 检查数据库连接和PostGIS扩展
- 检查GDB文件中的图层信息
- 检查几何数据质量

**使用示例**：
```bash
# 检查数据库连接
python scripts/check.py --connection

# 检查GDB文件
python scripts/check.py --layers F49.gdb

# 检查几何数据质量
python scripts/check.py --geometry

# 执行所有检查
python scripts/check.py --all
```

**选项说明**：
- `--connection, -c`: 检查数据库连接和PostGIS
- `--layers, -l GDB_PATH`: 检查GDB文件中的图层信息
- `--geometry, -g`: 检查几何数据质量
- `--all, -a`: 执行所有检查

## 🗑️ 数据库管理

### reset_database.py
重置数据库，删除所有导入的地理数据表。

**使用示例**：
```bash
# 交互式重置
python scripts/reset_database.py

# 直接重置（跳过确认）
python scripts/reset_database.py --yes
```

## 🐳 Docker 数据导入（跨平台）

### run_importer.py ⭐⭐⭐ **推荐（Docker环境）**
跨平台数据导入脚本，自动检测平台并使用正确的 docker-compose 命令语法。

**功能**：
- 自动检测当前平台（Windows PowerShell/CMD、Linux/macOS Bash）
- 自动处理平台差异，无需担心续行符问题
- 统一的使用接口，跨平台一致

**使用示例**：

**方式1：直接使用 Python 脚本（所有平台通用）：**
```bash
# Windows PowerShell / CMD / Linux / macOS 通用
# 重置数据库并导入数据
python scripts/run_importer.py python main.py --reset-and-import --gdb-dir /app/data

# 查看帮助
python scripts/run_importer.py python main.py --help

# 验证数据
python scripts/run_importer.py python scripts/verify_data.py

# 只导入数据（不重置）
python scripts/run_importer.py python scripts/import_all_tiles.py
```

**方式2：使用平台特定包装脚本（更简洁）：**
```bash
# Windows (CMD/PowerShell)
scripts\run_importer.bat python main.py --reset-and-import --gdb-dir /app/data

# Linux/macOS
./scripts/run_importer.sh python main.py --reset-and-import --gdb-dir /app/data
```

**注意**：
- 容器内的路径使用 `/app/data` 作为 GDB 文件目录
- 如果 GDB 文件在项目根目录，使用 `--gdb-dir /app/data`
- 脚本会自动处理平台差异，无需担心续行符问题

**相关文档**：`docs/DOCKER_GUIDE.md`

---

## 🚀 服务启动

### start_mcp.bat / start_mcp.sh
在虚拟环境中启动MCP服务器（本地开发使用）。

**使用示例**：
```bash
# Windows
scripts\start_mcp.bat

# Linux/Mac
./scripts/start_mcp.sh
```

### start-supergateway.bat / start-supergateway.sh
启动Supergateway服务，将Docker容器中的MCP服务器暴露为HTTP/SSE/WebSocket服务。

**使用示例**：
```bash
# 先启动基础服务
docker-compose up -d

# Windows - 启动Supergateway
scripts\start-supergateway.bat

# Linux/Mac - 启动Supergateway
./scripts/start-supergateway.sh
```

**注意**：此脚本需要在宿主机上运行，连接到Docker容器中的MCP服务器。适用于需要远程访问MCP服务的场景。

## 📋 标准工作流程

### 方式1：使用统一工具集（推荐）⭐⭐⭐

```bash
# 一键完成所有步骤
python scripts/setup_unified_database.py
```

就这么简单！工具会自动：
1. 查找参考图幅（F49.gdb）
2. 解析图幅结构
3. 创建统一表结构
4. 导入所有图幅数据

### 方式2：分步执行

如果需要分步执行或自定义参数：

```bash
# 步骤1：解析图幅结构
python scripts/parse_tile_schema.py F49.gdb --output analysis

# 步骤2：创建统一表结构
python scripts/create_unified_schema.py --analysis analysis/F49_complete_analysis.json

# 步骤3：导入所有图幅数据
python scripts/import_all_tiles.py
```

### 2. 日常使用

```bash
# 验证数据
python scripts/verify_data.py

# 检查数据库连接
python scripts/check.py --connection

# 检查所有内容
python scripts/check.py --all
```

### 3. 重置和重新导入

```bash
# 重置数据库
python scripts/reset_database.py --yes

# 重新导入数据
python scripts/import_all_tiles.py
```

## 📝 脚本分类总结

| 类别 | 脚本 | 状态 | 说明 |
|------|------|------|------|
| **统一工具** | `setup_unified_database.py` | ⭐⭐⭐ 强烈推荐 | 统一工具集，一键完成所有步骤 |
| **分析** | `parse_tile_schema.py` | ⭐ 推荐 | 完全解析图幅结构 |
| | `generate_field_spec.py` | ✅ 可用 | 生成字段说明（开发工具） |
| **表结构** | `create_unified_schema.py` | ⭐ 重要 | 创建统一表结构 |
| **导入** | `import_all_tiles.py` | ⭐ 推荐 | 导入所有图幅 |
| **验证** | `verify_data.py` | ✅ 可用 | 验证数据 |
| | `check.py` | ⭐ 推荐 | 统一检查工具（连接/图层/几何质量） |
| **管理** | `reset_database.py` | ✅ 可用 | 重置数据库 |
| **Docker导入** | `run_importer.py` | ⭐⭐⭐ 推荐 | 跨平台Docker数据导入脚本 |
| **启动** | `start_mcp.*` | ✅ 可用 | 启动MCP（本地） |
| | `start-supergateway.*` | ✅ 可用 | 启动Supergateway（Docker） |

## 🔗 相关文档

- [统一表结构导入指南](../docs/UNIFIED_SCHEMA_GUIDE.md)
- [MCP服务完整指南](../docs/MCP_GUIDE.md) - MCP配置、工具使用和查询工作流程
- [表使用指南](../docs/TABLE_USAGE_GUIDE.md) - 表用途和单位转换
- [字段说明文档](../docs/FIELD_SPEC.md)

