"""
缓存管理模块
提供内存缓存和可选的Redis缓存支持
"""

import json
import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import logging

from .logging_config import get_logger

logger = get_logger(__name__)

# 尝试导入Redis（可选）
try:
    import redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None


class CacheManager:
    """缓存管理器"""

    def __init__(
        self, use_redis: bool = False, redis_client=None, default_ttl: int = 300
    ):
        """
        初始化缓存管理器

        Args:
            use_redis: 是否使用Redis缓存（需要安装redis库）
            redis_client: Redis客户端实例（可选）
            default_ttl: 默认缓存过期时间（秒），默认300秒（5分钟）
        """
        self.use_redis = use_redis and HAS_REDIS
        self.default_ttl = default_ttl

        # 内存缓存
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, datetime] = {}

        # Redis客户端
        if self.use_redis:
            if redis_client:
                self.redis = redis_client
            else:
                try:
                    self.redis = redis.Redis(
                        host="localhost",
                        port=6379,
                        db=0,
                        decode_responses=True,
                    )
                    # 测试连接
                    self.redis.ping()
                    logger.info("Redis缓存已启用")
                except Exception as e:
                    logger.warning(f"Redis连接失败，使用内存缓存: {e}")
                    self.use_redis = False
                    self.redis = None
        else:
            self.redis = None
            if use_redis:
                logger.warning("Redis库未安装，使用内存缓存。安装: pip install redis")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键字符串
        """
        # 将参数序列化为字符串
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if self.use_redis and self.redis:
            try:
                cached = self.redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"从Redis获取缓存失败: {e}")
                # 回退到内存缓存

        # 内存缓存
        if key in self._memory_cache:
            # 检查是否过期
            if key in self._cache_ttl:
                if datetime.now() < self._cache_ttl[key]:
                    return self._memory_cache[key]
                else:
                    # 缓存过期，删除
                    del self._memory_cache[key]
                    del self._cache_ttl[key]
            else:
                return self._memory_cache[key]

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认TTL
        """
        if ttl is None:
            ttl = self.default_ttl

        if self.use_redis and self.redis:
            try:
                self.redis.setex(key, ttl, json.dumps(value, default=str))
            except Exception as e:
                logger.warning(f"设置Redis缓存失败: {e}")
                # 回退到内存缓存

        # 内存缓存
        self._memory_cache[key] = value
        self._cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        if self.use_redis and self.redis:
            try:
                self.redis.delete(key)
            except Exception as e:
                logger.warning(f"删除Redis缓存失败: {e}")

        # 内存缓存
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._cache_ttl:
            del self._cache_ttl[key]

    def clear(self, prefix: Optional[str] = None) -> None:
        """
        清除缓存

        Args:
            prefix: 键前缀（可选），如果提供则只清除匹配前缀的缓存
        """
        if self.use_redis and self.redis:
            try:
                if prefix:
                    # 查找所有匹配的键
                    keys = self.redis.keys(f"{prefix}:*")
                    if keys:
                        self.redis.delete(*keys)
                else:
                    self.redis.flushdb()
            except Exception as e:
                logger.warning(f"清除Redis缓存失败: {e}")

        # 内存缓存
        if prefix:
            keys_to_delete = [
                k for k in self._memory_cache.keys() if k.startswith(prefix)
            ]
            for key in keys_to_delete:
                self.delete(key)
        else:
            self._memory_cache.clear()
            self._cache_ttl.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "type": "redis" if self.use_redis else "memory",
            "memory_cache_size": len(self._memory_cache),
            "default_ttl": self.default_ttl,
        }

        if self.use_redis and self.redis:
            try:
                stats["redis_info"] = {
                    "connected": True,
                    "db_size": self.redis.dbsize(),
                }
            except Exception:
                stats["redis_info"] = {"connected": False}

        return stats


# 全局缓存管理器实例
_global_cache: Optional[CacheManager] = None


def get_cache_manager(
    use_redis: bool = False, redis_client=None, default_ttl: int = 300
) -> CacheManager:
    """
    获取全局缓存管理器实例

    Args:
        use_redis: 是否使用Redis
        redis_client: Redis客户端
        default_ttl: 默认TTL

    Returns:
        缓存管理器实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager(use_redis, redis_client, default_ttl)
    return _global_cache


def cached(prefix: str = "cache", ttl: int = 300):
    """
    缓存装饰器

    Args:
        prefix: 缓存键前缀
        ttl: 缓存过期时间（秒）

    Example:
        @cached(prefix="tile_codes", ttl=600)
        async def list_tile_codes(self, ...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result

            # 执行函数
            result = await func(*args, **kwargs)

            # 保存到缓存
            cache_manager.set(cache_key, result, ttl=ttl)
            logger.debug(f"缓存已设置: {cache_key} (TTL: {ttl}秒)")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)

            # 保存到缓存
            cache_manager.set(cache_key, result, ttl=ttl)
            logger.debug(f"缓存已设置: {cache_key} (TTL: {ttl}秒)")

            return result

        # 根据函数类型返回相应的包装器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
