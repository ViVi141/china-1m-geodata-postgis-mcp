# Docker数据库连接问题修复说明

## 问题描述

在Docker环境中，数据导入服务（`data-importer`）无法连接到PostgreSQL数据库，但MCP服务可以正常连接。

## 问题根源

### 1. 配置读取优先级问题

**问题**：
- 导入脚本（`setup_unified_database.py`, `import_all_tiles.py`, `create_unified_schema.py`）只从配置文件读取数据库连接信息
- 不读取Docker环境变量（`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`）
- 如果宿主机上的`config/database.ini`指向了其他数据库（如本地PostgreSQL），这个配置会被挂载到容器中，导致连接错误

**MCP服务为什么可以连接**：
- MCP服务在启动时，`docker-entrypoint.sh`会先运行，根据环境变量生成/更新配置文件
- 但导入脚本可能在配置文件更新之前就读取了配置，或者配置文件更新失败

### 2. 配置文件挂载问题

**问题**：
- `docker-compose.yml`中，`data-importer`服务挂载了`./config:/app/config`
- 如果宿主机上的`config/database.ini`存在且指向了其他数据库，这个文件会被挂载到容器中
- 虽然`docker-entrypoint.sh`会尝试更新配置文件，但可能存在时序问题或权限问题

### 3. docker-entrypoint.sh更新逻辑不够强制

**问题**：
- `docker-entrypoint.sh`只在特定条件下更新配置文件（如host=localhost或密码不匹配）
- 如果配置文件中的host不是localhost，且密码匹配，可能不会更新配置文件
- 这导致容器可能使用挂载的配置文件（指向其他数据库）而不是环境变量

## 修复方案

### 1. 修改导入脚本，优先使用环境变量

**修改的文件**：
- `scripts/setup_unified_database.py`
- `scripts/import_all_tiles.py`
- `scripts/create_unified_schema.py`

**修改内容**：
- 在读取配置文件之前，先检查环境变量
- 如果环境变量已设置，优先使用环境变量
- 只有在环境变量未设置时，才从配置文件读取
- 添加详细的配置信息输出，便于调试

**示例代码**：
```python
import os

# 优先使用环境变量
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database = os.getenv('DB_NAME')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD', '').strip()

# 如果环境变量未设置，从配置文件读取
if not all([host, database, user, password]):
    # 读取配置文件...
```

### 2. 增强docker-entrypoint.sh

**修改内容**：
- 在Docker环境中，如果环境变量已设置，强制更新配置文件
- 检查配置文件中的host是否为`postgres`（Docker服务名），如果不是则更新
- 添加更详细的日志输出，显示配置更新原因

**关键改进**：
```bash
# 如果环境变量已设置，强制使用环境变量（避免挂载的配置文件覆盖）
if [ -n "${DB_HOST}" ] || [ -n "${DB_PASSWORD}" ] || [ -n "${DB_NAME}" ] || [ -n "${DB_USER}" ]; then
    NEED_UPDATE=true
    echo "检测到环境变量已设置，将使用环境变量更新配置文件..."
fi
```

### 3. 添加诊断工具

**新增文件**：
- `scripts/diagnose_db_connection.py`

**功能**：
- 检查环境变量配置
- 检查配置文件内容
- 显示最终使用的配置（优先级：环境变量 > 配置文件）
- 检查配置问题（如Docker环境中使用localhost）
- 尝试连接数据库并显示结果

**使用方法**：
```bash
# 在Docker容器中运行
docker exec -it geodata-importer python /app/scripts/diagnose_db_connection.py
```

## 验证修复

### 1. 检查环境变量

在Docker容器中检查环境变量：
```bash
docker exec -it geodata-importer env | grep -E "DB_|POSTGRES_"
```

应该看到：
```
DB_HOST=postgres
DB_PORT=5432
DB_NAME=gis_data
DB_USER=postgres
DB_PASSWORD=...
```

### 2. 检查配置文件

在Docker容器中检查配置文件：
```bash
docker exec -it geodata-importer cat /app/config/database.ini
```

应该看到：
```
[postgresql]
host = postgres
port = 5432
database = gis_data
user = postgres
password = ...
```

**注意**：如果看到`host = localhost`或其他值，说明配置文件更新失败。

### 3. 运行诊断工具

```bash
docker exec -it geodata-importer python /app/scripts/diagnose_db_connection.py
```

诊断工具会显示：
- 环境变量配置
- 配置文件内容
- 最终使用的配置
- 配置问题检查
- 连接测试结果

### 4. 测试导入脚本

```bash
# 测试连接
docker exec -it geodata-importer python /app/scripts/setup_unified_database.py --help

# 运行诊断
docker exec -it geodata-importer python /app/scripts/diagnose_db_connection.py
```

## 常见问题排查

### 问题1：仍然无法连接

**检查项**：
1. 确认PostgreSQL服务正在运行：
   ```bash
   docker ps | grep postgres
   ```

2. 确认容器在同一网络中：
   ```bash
   docker network inspect geodata-network
   ```

3. 确认`depends_on`配置正确：
   ```yaml
   depends_on:
     postgres:
       condition: service_healthy
   ```

4. 检查PostgreSQL健康检查：
   ```bash
   docker logs geodata-postgres
   ```

### 问题2：配置文件未更新

**可能原因**：
1. 配置文件挂载为只读（应该可写）
2. 文件权限问题
3. `docker-entrypoint.sh`未执行

**解决方法**：
1. 检查`docker-compose.yml`中的挂载配置：
   ```yaml
   volumes:
     - ./config:/app/config  # 应该是可写的，不是:ro
   ```

2. 手动删除容器内的配置文件，让`docker-entrypoint.sh`重新生成：
   ```bash
   docker exec -it geodata-importer rm /app/config/database.ini
   docker restart geodata-importer
   ```

### 问题3：连接到错误的数据库

**检查项**：
1. 运行诊断工具，查看最终使用的配置
2. 检查环境变量是否正确设置
3. 检查配置文件内容

**解决方法**：
1. 确保环境变量正确设置
2. 删除宿主机上的`config/database.ini`（如果指向错误数据库）
3. 重新启动容器，让`docker-entrypoint.sh`生成正确的配置

## 最佳实践

1. **在Docker环境中，始终使用环境变量**：
   - 不要依赖挂载的配置文件
   - 在`docker-compose.yml`中设置环境变量
   - 让`docker-entrypoint.sh`根据环境变量生成配置文件

2. **避免在宿主机上创建指向其他数据库的配置文件**：
   - 如果需要在本地开发，使用`.gitignore`忽略`config/database.ini`
   - 在Docker环境中，让容器自动生成配置文件

3. **使用诊断工具排查问题**：
   - 在遇到连接问题时，首先运行`diagnose_db_connection.py`
   - 根据诊断结果定位问题

4. **检查配置一致性**：
   - 确保`docker-compose.yml`中所有服务的环境变量一致
   - 确保`POSTGRES_PASSWORD`和`DB_PASSWORD`一致

## 相关文件

- `scripts/setup_unified_database.py` - 统一数据库设置脚本（已修复）
- `scripts/import_all_tiles.py` - 导入所有图幅脚本（已修复）
- `scripts/create_unified_schema.py` - 创建表结构脚本（已修复）
- `scripts/docker-entrypoint.sh` - Docker入口脚本（已增强）
- `scripts/diagnose_db_connection.py` - 诊断工具（新增）
- `docker-compose.yml` - Docker编排配置

## 更新日期

2026-01-07

