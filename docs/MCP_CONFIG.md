# MCP配置文件说明

本文档说明如何在MCP客户端中配置1:100万基础地理信息PostGIS MCP服务。

## MCP.json配置文件位置

MCP配置文件的位置取决于你使用的MCP客户端：

### Claude Desktop (Anthropic)
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Cursor IDE
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\mcp.json`
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/mcp.json`

## 配置示例

### 方式1：使用绝对路径（推荐）

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "python",
      "args": [
        "C:/Users/YourUsername/Desktop/gdb_mcp/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/Users/YourUsername/Desktop/gdb_mcp"
      }
    }
  }
}
```

### 方式2：使用虚拟环境（推荐）

如果你使用虚拟环境，需要指定虚拟环境中的Python解释器：

**Windows:**
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

**Linux/macOS:**
```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "/home/username/gdb_mcp/.venv/bin/python",
      "args": [
        "/home/username/gdb_mcp/mcp_server.py"
      ],
      "cwd": "/home/username/gdb_mcp"
    }
  }
}
```

### 方式3：使用系统Python（如果已安装依赖）

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "python",
      "args": [
        "/absolute/path/to/gdb_mcp/mcp_server.py"
      ],
      "cwd": "/absolute/path/to/gdb_mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/gdb_mcp"
      }
    }
  }
}
```

## 完整配置示例（Claude Desktop）

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "C:/Users/YourUsername/Desktop/gdb_mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/Users/YourUsername/Desktop/gdb_mcp/mcp_server.py"
      ],
      "cwd": "C:/Users/YourUsername/Desktop/gdb_mcp",
      "env": {
        "PYTHONPATH": "C:/Users/YourUsername/Desktop/gdb_mcp"
      }
    }
  }
}
```

## 配置说明

### 必需字段

- **command**: Python解释器路径
  - Windows虚拟环境: `.venv\Scripts\python.exe`
  - Linux/macOS虚拟环境: `.venv/bin/python`
  - 系统Python: `python` 或 `python3`

- **args**: 参数数组，包含MCP服务器脚本的绝对路径
  - 必须使用绝对路径: `["/absolute/path/to/mcp_server.py"]`

### 可选字段

- **cwd**: 工作目录（推荐设置）
  - 设置为项目根目录，确保相对路径（如`config/`、`specs/`）能正确解析

- **env**: 环境变量
  - `PYTHONPATH`: 设置Python模块搜索路径（如果需要）

## 验证配置

配置完成后，重启MCP客户端，然后：

1. 检查MCP服务器是否启动
2. 查看可用工具列表
3. 测试连接：使用 `list_tables` 工具查看数据库中的表

## 常见问题

### 问题1：找不到模块

**错误**: `ModuleNotFoundError: No module named 'core'`

**解决方案**: 
- 确保 `cwd` 设置为项目根目录
- 或设置 `PYTHONPATH` 环境变量指向项目根目录

### 问题2：找不到配置文件

**错误**: `FileNotFoundError: config/database.ini`

**解决方案**: 
- 确保 `cwd` 设置为项目根目录
- 或使用绝对路径配置数据库连接

### 问题3：Python版本不兼容

**错误**: Python版本过低

**解决方案**: 
- 确保使用Python 3.8或更高版本
- 在虚拟环境中安装正确的Python版本

### 问题4：数据库连接失败

**错误**: 无法连接到PostgreSQL

**解决方案**: 
- 确保PostgreSQL服务正在运行
- 检查 `config/database.ini` 配置是否正确
- 确保数据库已启用PostGIS扩展

## 多服务器配置

如果你同时使用多个MCP服务器，可以在同一个配置文件中配置：

```json
{
  "mcpServers": {
    "china-1m-geodata-postgis-mcp": {
      "command": "python",
      "args": ["/path/to/gdb_mcp/mcp_server.py"],
      "cwd": "/path/to/gdb_mcp"
    },
    "other-mcp-server": {
      "command": "node",
      "args": ["/path/to/other/server.js"]
    }
  }
}
```

## 注意事项

1. **路径格式**:
   - Windows: 使用正斜杠 `/` 或双反斜杠 `\\`
   - Linux/macOS: 使用正斜杠 `/`

2. **虚拟环境**:
   - 推荐使用虚拟环境，避免依赖冲突
   - 确保虚拟环境中已安装所有依赖

3. **权限**:
   - 确保MCP客户端有权限执行Python脚本
   - 确保有权限访问项目目录和数据库

4. **日志**:
   - MCP服务器日志输出到stderr
   - 可以在MCP客户端中查看日志输出

