"""
表名验证模块 - 防止SQL注入
"""

import re
import psycopg2
from typing import Set, Optional
import logging

from .logging_config import get_logger

logger = get_logger(__name__)


class TableValidator:
    """表名验证器"""

    # 允许的表名模式：字母、数字、下划线，必须以字母或下划线开头
    TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    # 缓存已验证的表名
    _validated_tables: Set[str] = set()

    @classmethod
    def validate_table_name(
        cls, table_name: str, conn: Optional[psycopg2.extensions.connection] = None
    ) -> str:
        """
        验证表名，防止SQL注入

        Args:
            table_name: 要验证的表名
            conn: 数据库连接（可选），如果提供则验证表是否存在

        Returns:
            验证后的表名

        Raises:
            ValueError: 表名无效或不存在
        """
        if not table_name:
            raise ValueError("表名不能为空")

        # 检查格式
        if not cls.TABLE_NAME_PATTERN.match(table_name):
            raise ValueError(
                f"无效的表名格式: {table_name}。"
                "表名只能包含字母、数字和下划线，且必须以字母或下划线开头"
            )

        # 如果表名已在缓存中，直接返回
        if table_name in cls._validated_tables:
            return table_name

        # 如果提供了连接，验证表是否存在
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                          AND table_name = %s
                        """,
                        (table_name,),
                    )
                    if not cur.fetchone():
                        raise ValueError(f"表不存在: {table_name}")
            except psycopg2.Error as e:
                logger.warning(f"验证表存在性时出错: {e}")
                # 如果验证失败，不抛出异常，只记录警告
                # 让后续的SQL执行来发现错误

        # 添加到缓存
        cls._validated_tables.add(table_name)
        return table_name

    @classmethod
    def clear_cache(cls) -> None:
        """清除验证缓存"""
        cls._validated_tables.clear()
