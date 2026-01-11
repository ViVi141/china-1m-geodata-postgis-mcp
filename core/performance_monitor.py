"""
性能监控模块
提供性能监控装饰器和查询统计功能
"""

import time
import functools
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime
import logging

from .logging_config import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, slow_query_threshold: float = 5.0):
        """
        初始化性能监控器

        Args:
            slow_query_threshold: 慢查询阈值（秒），默认5秒
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "slow_queries": 0,
            }
        )
        self.recent_queries: deque = deque(maxlen=100)  # 保留最近100条查询

    def record_query(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        记录查询统计

        Args:
            operation: 操作名称（如 'query_data', 'list_tables'）
            duration: 执行时间（秒）
            success: 是否成功
            error: 错误信息（如果失败）
        """
        stats = self.query_stats[operation]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)

        if duration > self.slow_query_threshold:
            stats["slow_queries"] += 1
            logger.warning(
                f"慢查询警告: {operation} 耗时 {duration:.2f}秒 "
                f"(阈值: {self.slow_query_threshold}秒)"
            )

        # 记录最近查询
        self.recent_queries.append(
            {
                "operation": operation,
                "duration": duration,
                "success": success,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            operation: 操作名称（可选），如果提供则只返回该操作的统计

        Returns:
            统计信息字典
        """
        if operation:
            if operation not in self.query_stats:
                return {}
            stats = self.query_stats[operation].copy()
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
            else:
                stats["avg_time"] = 0.0
            return {operation: stats}

        # 返回所有统计
        result = {}
        for op, stats in self.query_stats.items():
            stats_copy = stats.copy()
            if stats_copy["count"] > 0:
                stats_copy["avg_time"] = stats_copy["total_time"] / stats_copy["count"]
            else:
                stats_copy["avg_time"] = 0.0
            result[op] = stats_copy

        return result

    def get_recent_queries(self, limit: int = 10) -> list:
        """
        获取最近的查询记录

        Args:
            limit: 返回的记录数

        Returns:
            最近的查询记录列表
        """
        return list(self.recent_queries)[-limit:]

    def reset_stats(self, operation: Optional[str] = None) -> None:
        """
        重置统计信息

        Args:
            operation: 操作名称（可选），如果提供则只重置该操作的统计
        """
        if operation:
            if operation in self.query_stats:
                del self.query_stats[operation]
        else:
            self.query_stats.clear()
            self.recent_queries.clear()


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(slow_query_threshold: float = 5.0) -> PerformanceMonitor:
    """
    获取全局性能监控器实例

    Args:
        slow_query_threshold: 慢查询阈值

    Returns:
        性能监控器实例
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(slow_query_threshold)
    return _global_monitor


def monitor_performance(operation_name: Optional[str] = None):
    """
    性能监控装饰器

    Args:
        operation_name: 操作名称（可选），如果不提供则使用函数名

    Example:
        @monitor_performance("query_data")
        async def query_data(self, ...):
            ...
    """

    def decorator(func):
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            success = True
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_query(op_name, duration, success, error)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            success = True
            error = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_query(op_name, duration, success, error)

        # 根据函数类型返回相应的包装器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
