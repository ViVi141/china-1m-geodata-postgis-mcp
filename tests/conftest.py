"""
pytest配置和共享fixtures
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_database_config():
    """模拟数据库配置"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_password",
    }


@pytest.fixture
def mock_connection():
    """模拟数据库连接"""
    conn = Mock()
    cur = Mock()
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None
    return conn, cur


@pytest.fixture
def sample_table_info():
    """示例表信息"""
    return {
        "table_name": "boua",
        "description": "行政境界面",
        "category": "境界与政区",
        "layer_code": "BOUA",
        "record_count": 1000,
        "srid": 4326,
    }


@pytest.fixture
def sample_tile_codes():
    """示例图幅代码列表"""
    return {
        "tile_codes": [
            {
                "tile_code": "F49",
                "total_records": 5000,
                "tables": {"boua": 1000, "hyda": 2000, "lrdl": 2000},
            },
            {
                "tile_code": "F50",
                "total_records": 4500,
                "tables": {"boua": 900, "hyda": 1800, "lrdl": 1800},
            },
        ],
        "total": 2,
    }
