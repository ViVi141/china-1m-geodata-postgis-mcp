# 更新日志

## [1.2.0] - 2026-01

### 新增功能
- ✨ 完整的性能测试工具集
  - `performance_test.py` - 完整的性能测试工具（基本测试 + 并发压测）
  - `docker_load_test.py` - Docker环境专用压测工具（带资源监控）
  - `monitor_docker.py` - Docker容器资源监控工具
  - `analyze_test_results.py` - 测试结果分析工具
  - `quick_performance_test.py` - 快速性能测试脚本
  - `run_performance_test.bat/sh` - 交互式测试菜单脚本

### 文档完善
- 📚 性能测试完整指南（PERFORMANCE_TEST_GUIDE.md）
- 📚 性能测试总结报告（PERFORMANCE_TEST_SUMMARY.md）
- 📝 支持生成文本/JSON/HTML格式的测试报告

### 工具增强
- 🔧 自动检测运行环境（Docker容器内/本地）
- 🔧 自动调整数据库连接配置
- 🔧 支持持续压测（按时间）
- 🔧 支持高并发压测
- 🔧 实时监控容器资源使用

## [1.1.0] - 2026-01

### 新增功能
- ✨ 数据库连接池管理，提升并发性能
- ✨ 查询结果缓存机制（内存/Redis）
- ✨ 性能监控和慢查询日志
- ✨ SQL注入防护（表名验证）
- ✨ 查询超时机制

### 性能优化
- ⚡ 批量几何对象转换，查询速度提升50-90%
- ⚡ 连接池复用，连接创建开销减少80-95%
- ⚡ 元数据查询缓存，响应速度提升90%+

### 代码质量
- 🧪 完整的单元测试覆盖（22个测试用例）
- 📝 统一日志配置系统
- 🔒 增强的错误处理和安全性

## [1.0.0] - 2025-01

**作者**: ViVi141 (747384120@qq.com)

### 架构决策
- 🎯 **PostgreSQL专用方案**：专注于PostgreSQL/PostGIS高性能方案
- 🎯 移除直接读取GDB功能，所有数据必须导入PostgreSQL
- 🎯 优化为生产环境使用，提供最佳查询性能

### 新增
- ✨ 实现MCP服务器核心功能
- ✨ 支持通用化数据规格配置（JSON/YAML）
- ✨ 实现数据导入工具（import_geodata）- 导入到PostgreSQL
- ✨ 实现数据验证工具（verify_import）
- ✨ 实现数据查询工具（query_data）- 从PostgreSQL查询
- ✨ 实现SQL执行工具（execute_sql）- 支持复杂SQL查询
- ✨ 实现表列表工具（list_tables）- 列出已导入的表
- ✨ 实现规格管理工具（list_specs, get_spec, register_spec）
- ✨ 支持GDB格式数据导入到PostgreSQL
- ✨ 自动检测数据规格
- ✨ 自动验证和修复无效几何
- ✨ 批量插入优化
- ✨ 自动创建空间索引（GIST）

### 配置
- 📝 包含1:100万公众版基础地理信息数据规格配置
- 📝 提供数据库配置模板
- 📝 完整的项目文档

### 技术栈
- Python 3.8+
- MCP (Model Context Protocol)
- **PostgreSQL/PostGIS**（必需）
- Fiona/GDAL（用于读取GDB）
- Shapely

### 重要说明
- ⚠️ **PostgreSQL必需**：必须安装和配置PostgreSQL/PostGIS
- ⚠️ **数据导入**：数据必须先导入PostgreSQL才能查询
- ⚠️ **仅支持GDB**：目前仅支持GDB格式导入

