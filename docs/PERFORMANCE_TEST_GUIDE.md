# 性能测试和压测指南

本指南介绍如何对Docker部署的MCP服务进行性能测试和压测。

## 📋 目录

- [测试工具](#测试工具)
- [基本性能测试](#基本性能测试)
- [并发压测](#并发压测)
- [Docker环境压测](#docker环境压测)
- [资源监控](#资源监控)
- [测试报告](#测试报告)
- [性能优化建议](#性能优化建议)

## 🛠️ 测试工具

项目提供了三个测试工具：

1. **performance_test.py** - 完整的性能测试工具（基本测试 + 并发压测）
2. **docker_load_test.py** - Docker环境专用压测工具（带资源监控）
3. **monitor_docker.py** - Docker容器资源监控工具

## 📊 基本性能测试

### 运行基本性能测试

基本性能测试会测试所有MCP工具的性能，包括：
- `list_tile_codes` - 列出图幅代码
- `list_tables` - 列出数据表
- `verify_import` - 验证数据
- `query_data` - 空间数据查询
- `execute_sql` - SQL查询

```bash
# 运行基本性能测试
python scripts/performance_test.py
```

### 测试结果示例

```
================================================================================
开始基本性能测试
================================================================================

[测试1] list_tile_codes - 列出图幅代码
  ✓ 成功 - 耗时: 0.123秒
  ✓ 图幅数量: 2

[测试2] list_tables - 列出数据表
  ✓ 成功 - 耗时: 0.456秒
  ✓ 表数量: 9

...
```

## 🚀 并发压测

### 基本并发压测

```bash
# 10个并发，100个请求
python scripts/performance_test.py --concurrent 10 --requests 100
```

### 测试特定工具

```bash
# 只测试 query_data 工具
python scripts/performance_test.py --tool query_data --concurrent 10 --requests 100

# 只测试 execute_sql 工具
python scripts/performance_test.py --tool execute_sql --concurrent 10 --requests 100
```

### 压测结果示例

```
并发压测结果:
--------------------------------------------------------------------------------

query_data:
  总请求数: 100
  成功请求: 100
  失败请求: 0
  成功率: 100.00%
  总耗时: 12.34秒
  QPS: 8.10
  最小响应时间: 0.045秒
  最大响应时间: 0.234秒
  平均响应时间: 0.123秒
  中位数响应时间: 0.118秒
  P95响应时间: 0.189秒
  P99响应时间: 0.212秒
```

## 🐳 Docker环境压测

### 使用 docker_load_test.py

`docker_load_test.py` 专门用于Docker环境，会自动监控容器资源使用情况。

```bash
# 基本压测（10并发，100请求）
python scripts/docker_load_test.py

# 如果连接失败，指定数据库主机（本地运行）
python scripts/docker_load_test.py --host localhost --port 5432

# 高并发压测（20并发，500请求）
python scripts/docker_load_test.py --concurrent 20 --requests 500

# 持续压测（10并发，持续60秒）
python scripts/docker_load_test.py --concurrent 10 --duration 60

# 测试特定工具
python scripts/docker_load_test.py --tool query_data --concurrent 5 --requests 100
```

### 压测结果包含

- 请求统计（总数、成功、失败、成功率）
- QPS（每秒请求数）
- 响应时间统计（最小、最大、平均、中位数、P95、P99）
- 容器资源使用情况（CPU、内存、网络、IO）

## 📈 资源监控

### 实时监控容器资源

```bash
# 监控所有相关容器（每5秒刷新）
python scripts/monitor_docker.py

# 监控特定容器
python scripts/monitor_docker.py --container geodata-postgres

# 监控并保存日志
python scripts/monitor_docker.py --output monitor.log

# 只获取一次统计信息
python scripts/monitor_docker.py --once
```

### 监控输出示例

```
================================================================================
容器资源监控 - 2026-01-15 10:30:45
================================================================================

容器: geodata-postgres
  CPU使用率: 15.23%
  内存使用: 256MiB / 2GiB
  内存百分比: 12.50%
  网络IO: 1.2MB / 856KB
  块IO: 12MB / 8MB
  进程数: 15

容器: geodata-mcp-server
  CPU使用率: 2.45%
  内存使用: 128MiB / 512MiB
  内存百分比: 25.00%
  网络IO: 234KB / 156KB
  块IO: 2MB / 1MB
  进程数: 3
================================================================================
```

## 📄 测试报告

### 生成文本报告

```bash
# 生成文本报告（默认）
python scripts/performance_test.py --report text
```

### 生成JSON报告

```bash
# 生成JSON报告
python scripts/performance_test.py --report json --output report.json
```

### 生成HTML报告

```bash
# 生成HTML报告
python scripts/performance_test.py --report html --output report.html
```

### HTML报告示例

HTML报告包含：
- 基本性能测试结果表格
- 并发压测结果表格
- 响应时间统计图表（如果支持）
- 资源使用情况

## ⚙️ 性能优化建议

### 1. 连接池配置

确保连接池大小合适：

```python
# 在 core/connection_pool.py 中调整
minconn=5   # 最小连接数
maxconn=20  # 最大连接数（根据并发需求调整）
```

### 2. 缓存配置

元数据查询（`list_tile_codes`、`list_tables`）会自动缓存10分钟，可以调整缓存时间：

```python
# 在 core/cache_manager.py 中调整
CACHE_TTL = 600  # 缓存时间（秒）
```

### 3. PostgreSQL配置

在 `docker-compose.yml` 中优化PostgreSQL配置：

```yaml
command:
  - "postgres"
  - "-c"
  - "shared_buffers=256MB"      # 根据内存调整
  - "-c"
  - "max_connections=200"       # 根据并发需求调整
  - "-c"
  - "work_mem=16MB"             # 根据查询复杂度调整
  - "-c"
  - "effective_cache_size=1GB"  # 根据内存调整
```

### 4. 索引优化

确保已创建必要的索引：

```sql
-- 空间索引（GIST）
CREATE INDEX IF NOT EXISTS idx_boua_geom ON boua USING GIST (geom);

-- 图幅代码索引
CREATE INDEX IF NOT EXISTS idx_boua_tile_code ON boua (tile_code);
```

### 5. 查询优化

- 使用空间索引：确保查询条件使用 `geom && ST_MakeEnvelope(...)`
- 限制返回记录数：使用 `LIMIT` 子句
- 避免全表扫描：使用 `tile_code` 过滤

## 📊 性能基准

### 预期性能指标

| 工具 | 平均响应时间 | P95响应时间 | QPS (10并发) |
|------|------------|------------|-------------|
| list_tile_codes | < 0.2秒 | < 0.3秒 | > 50 |
| list_tables | < 0.5秒 | < 0.8秒 | > 20 |
| verify_import | < 1.0秒 | < 2.0秒 | > 10 |
| query_data (简单) | < 0.2秒 | < 0.5秒 | > 50 |
| query_data (空间过滤) | < 0.5秒 | < 1.0秒 | > 20 |
| execute_sql (简单) | < 0.3秒 | < 0.6秒 | > 30 |
| execute_sql (复杂) | < 2.0秒 | < 5.0秒 | > 5 |

**注意**：实际性能取决于数据量、硬件配置、网络延迟等因素。

## 🔍 故障排查

### 问题1: 数据库连接失败 - "could not translate host name 'postgres'"

**原因**：在本地运行脚本时，无法解析Docker服务名 "postgres"

**解决方案**：

**方案A：使用 --host 参数（推荐）**
```bash
python scripts/docker_load_test.py --host localhost --port 5432
```

**方案B：修改配置文件**
编辑 `config/database.ini`，将 `host = postgres` 改为 `host = localhost`

**方案C：脚本自动检测（已实现）**
脚本会自动检测运行环境，如果在本地运行会自动将 "postgres" 替换为 "localhost"

### 问题2: 压测时连接失败

**原因**：连接池耗尽或PostgreSQL最大连接数限制

**解决方案**：
1. 增加连接池大小
2. 增加PostgreSQL `max_connections` 配置
3. 减少并发数

### 问题2: 响应时间过长

**原因**：缺少索引、查询复杂、数据量大

**解决方案**：
1. 检查是否创建了空间索引
2. 优化查询SQL
3. 使用 `tile_code` 过滤减少数据量

### 问题3: 内存使用过高

**原因**：批量大小过大、连接数过多

**解决方案**：
1. 减少批量插入大小
2. 减少连接池大小
3. 增加Docker容器内存限制

## 📝 测试检查清单

在进行性能测试前，确保：

- [ ] Docker容器正常运行
- [ ] 数据库已导入数据
- [ ] 已创建必要的索引
- [ ] PostgreSQL配置已优化
- [ ] 连接池配置合理
- [ ] 缓存已启用

## 🎯 测试场景建议

### 场景1: 基本功能测试

```bash
python scripts/performance_test.py
```

### 场景2: 低并发压测

```bash
python scripts/docker_load_test.py --concurrent 5 --requests 50
```

### 场景3: 中等并发压测

```bash
python scripts/docker_load_test.py --concurrent 10 --requests 100
```

### 场景4: 高并发压测

```bash
python scripts/docker_load_test.py --concurrent 20 --requests 500
```

### 场景5: 持续压测

```bash
python scripts/docker_load_test.py --concurrent 10 --duration 60
```

### 场景6: 混合压测

同时运行多个工具压测：

```bash
# 终端1: 测试 query_data
python scripts/docker_load_test.py --tool query_data --concurrent 5 --requests 200

# 终端2: 测试 execute_sql
python scripts/docker_load_test.py --tool execute_sql --concurrent 5 --requests 200

# 终端3: 监控资源
python scripts/monitor_docker.py
```

## 📚 相关文档

- [MCP服务完整指南](MCP_GUIDE.md)
- [Docker部署指南](DOCKER_GUIDE.md)
- [性能监控模块](../core/performance_monitor.py)

---

**最后更新**: 2026-01
