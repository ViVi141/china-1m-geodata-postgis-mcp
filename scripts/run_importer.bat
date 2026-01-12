@echo off
REM Windows 批处理包装脚本 - 跨平台数据导入工具
REM 自动调用 Python 脚本处理平台差异

python scripts/run_importer.py %*
