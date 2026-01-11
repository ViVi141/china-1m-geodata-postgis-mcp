"""
统一日志配置模块
"""

import logging
import sys
from pathlib import Path
from typing import Optional

_logging_configured = False


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """
    统一配置日志系统

    Args:
        level: 日志级别，默认INFO
        log_file: 日志文件路径（可选），如果提供则同时输出到文件
        format_string: 日志格式字符串（可选）
        date_format: 日期格式字符串（可选）
    """
    global _logging_configured

    if _logging_configured:
        # 如果已经配置过，只更新级别
        logging.root.setLevel(level)
        return

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler(sys.stderr)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt=date_format,
        handlers=handlers,
        force=True,  # 强制重新配置，覆盖之前的配置
    )

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，通常使用 __name__

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)
