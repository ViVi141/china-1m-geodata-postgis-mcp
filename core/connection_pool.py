"""
数据库连接池管理模块
"""

import psycopg2
from psycopg2 import pool
from typing import Dict, Any, Optional
import logging
import threading

from .logging_config import get_logger

logger = get_logger(__name__)


class ConnectionPoolManager:
    """数据库连接池管理器"""

    _pools: Dict[str, pool.ThreadedConnectionPool] = {}
    _lock = threading.Lock()

    @classmethod
    def get_pool(
        cls,
        database_config: Dict[str, Any],
        minconn: int = 2,
        maxconn: int = 10,
        pool_key: Optional[str] = None,
    ) -> pool.ThreadedConnectionPool:
        """
        获取或创建连接池

        Args:
            database_config: 数据库配置字典
            minconn: 最小连接数，默认2
            maxconn: 最大连接数，默认10
            pool_key: 连接池键（可选），用于区分不同的数据库配置

        Returns:
            连接池实例
        """
        if pool_key is None:
            # 使用配置生成唯一键
            pool_key = (
                f"{database_config.get('host', 'localhost')}:"
                f"{database_config.get('port', 5432)}/"
                f"{database_config.get('database', '')}"
            )

        with cls._lock:
            if pool_key not in cls._pools:
                try:
                    logger.info(
                        f"创建新的连接池: {pool_key} (min={minconn}, max={maxconn})"
                    )
                    cls._pools[pool_key] = pool.ThreadedConnectionPool(
                        minconn=minconn,
                        maxconn=maxconn,
                        host=database_config.get("host", "localhost"),
                        port=database_config.get("port", 5432),
                        database=database_config.get("database"),
                        user=database_config.get("user"),
                        password=database_config.get("password"),
                        client_encoding="UTF8",
                    )
                except Exception as e:
                    logger.error(f"创建连接池失败: {e}")
                    raise

            return cls._pools[pool_key]

    @classmethod
    def get_connection(
        cls, database_config: Dict[str, Any], pool_key: Optional[str] = None
    ) -> psycopg2.extensions.connection:
        """
        从连接池获取连接

        Args:
            database_config: 数据库配置字典
            pool_key: 连接池键（可选）

        Returns:
            数据库连接
        """
        connection_pool = cls.get_pool(database_config, pool_key=pool_key)

        try:
            conn = connection_pool.getconn()
            if conn:
                # 设置连接编码
                with conn.cursor() as cur:
                    cur.execute("SET client_encoding TO 'UTF8';")
                conn.commit()
            return conn
        except pool.PoolError as e:
            logger.error(f"从连接池获取连接失败: {e}")
            raise ConnectionError(f"无法从连接池获取连接: {e}") from e

    @classmethod
    def put_connection(
        cls,
        conn: psycopg2.extensions.connection,
        database_config: Dict[str, Any],
        pool_key: Optional[str] = None,
    ) -> None:
        """
        归还连接到池

        Args:
            conn: 数据库连接
            database_config: 数据库配置字典
            pool_key: 连接池键（可选）
        """
        if pool_key is None:
            pool_key = (
                f"{database_config.get('host', 'localhost')}:"
                f"{database_config.get('port', 5432)}/"
                f"{database_config.get('database', '')}"
            )

        if pool_key in cls._pools:
            try:
                cls._pools[pool_key].putconn(conn)
            except Exception as e:
                logger.warning(f"归还连接到池失败: {e}")
                # 如果归还失败，尝试关闭连接
                try:
                    conn.close()
                except Exception:
                    pass

    @classmethod
    def close_all_pools(cls) -> None:
        """关闭所有连接池"""
        with cls._lock:
            for pool_key, connection_pool in cls._pools.items():
                try:
                    logger.info(f"关闭连接池: {pool_key}")
                    connection_pool.closeall()
                except Exception as e:
                    logger.error(f"关闭连接池 {pool_key} 失败: {e}")
            cls._pools.clear()
