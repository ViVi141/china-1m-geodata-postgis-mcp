# 测试说明

本文档说明如何运行项目的单元测试和集成测试。

## 安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-cov
```

或使用requirements.txt（需要取消注释测试依赖）：

```bash
pip install -r requirements.txt
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_table_validator.py
pytest tests/test_cache_manager.py
pytest tests/test_performance_monitor.py
```

### 运行特定测试类或函数

```bash
pytest tests/test_table_validator.py::TestTableValidator
pytest tests/test_table_validator.py::TestTableValidator::test_validate_valid_table_name
```

### 运行并显示覆盖率

```bash
pytest --cov=core --cov-report=html
```

### 运行并显示详细输出

```bash
pytest -v
```

### 只运行单元测试（排除集成测试）

```bash
pytest -m "not integration"
```

## 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest配置和共享fixtures
├── test_table_validator.py  # 表名验证器测试
├── test_cache_manager.py    # 缓存管理器测试
└── test_performance_monitor.py  # 性能监控器测试
```

## 编写新测试

### 单元测试示例

```python
import pytest
from core.your_module import YourClass

class TestYourClass:
    def test_your_method(self):
        obj = YourClass()
        result = obj.your_method()
        assert result == expected_value
```

### 异步测试示例

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected_value
```

### 使用Fixtures

```python
def test_with_fixture(mock_database_config):
    # mock_database_config 来自 conftest.py
    assert mock_database_config["host"] == "localhost"
```

## 测试标记

- `@pytest.mark.slow` - 标记为慢测试
- `@pytest.mark.integration` - 标记为集成测试
- `@pytest.mark.unit` - 标记为单元测试

运行特定标记的测试：

```bash
pytest -m unit          # 只运行单元测试
pytest -m "not slow"    # 排除慢测试
```

## 注意事项

1. **数据库测试**：单元测试使用Mock对象，不需要真实的数据库连接
2. **异步测试**：使用 `@pytest.mark.asyncio` 装饰器标记异步测试
3. **测试隔离**：每个测试应该独立，不依赖其他测试的状态
4. **清理资源**：使用 `pytest.fixture` 的 `yield` 或 `teardown` 清理资源

## 持续集成

测试可以在CI/CD流程中运行：

```yaml
# GitHub Actions 示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=core --cov-report=xml
```

## 测试覆盖率目标

- 核心模块（core/）：目标覆盖率 > 80%
- 工具脚本（scripts/）：目标覆盖率 > 60%
- 总体覆盖率：目标 > 70%

查看覆盖率报告：

```bash
pytest --cov=core --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```
