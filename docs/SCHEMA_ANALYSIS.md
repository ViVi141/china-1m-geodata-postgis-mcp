# GDB图层结构分析指南

本文档说明如何分析GDB图层的实际结构，并基于分析结果生成准确的字段说明文档。

## 为什么需要分析GDB图层结构？

1. **确保准确性**：不同图幅的GDB文件可能包含不同的字段，需要基于实际数据生成字段说明
2. **了解字段含义**：通过分析示例值，可以更好地理解字段的实际用途
3. **发现数据质量**：通过空值率统计，了解哪些字段经常为空，避免盲目查询

## 分析工具

### 1. analyze_gdb_schema.py

详细分析GDB文件的所有图层，包括：
- 字段名称和类型
- 字段空值率统计
- 字段示例值（最多10个）
- 几何类型
- 记录数统计

**使用方法**：

```bash
# 分析单个GDB文件
python scripts/analyze_gdb_schema.py F49.gdb --output analysis/F49_schema.json

# 批量分析目录中的所有GDB文件
python scripts/analyze_gdb_schema.py --dir . --output analysis/all_schema.json
```

**输出**：
- JSON格式的分析结果文件
- 控制台输出的字段说明摘要

### 2. generate_field_spec.py

基于分析结果生成Markdown格式的字段说明文档。

**使用方法**：

```bash
python scripts/generate_field_spec.py analysis/F49_schema.json docs/FIELD_SPEC.md
```

**功能**：
- 根据图层映射关系（`specs/china_1m_2021.json`）组织字段说明
- 自动生成字段描述（基于预定义规则和示例值）
- 标注空值率高的字段
- 添加使用提示

## 分析流程

### 步骤1：分析GDB图层

```bash
# 分析所有可用的GDB文件
python scripts/analyze_gdb_schema.py F49.gdb --output analysis/F49_schema.json
python scripts/analyze_gdb_schema.py G49.gdb --output analysis/G49_schema.json
python scripts/analyze_gdb_schema.py F50.gdb --output analysis/F50_schema.json
python scripts/analyze_gdb_schema.py G50.gdb --output analysis/G50_schema.json
```

### 步骤2：合并分析结果（可选）

如果需要合并多个图幅的分析结果，可以编写脚本合并JSON文件，确保字段说明覆盖所有可能的字段。

### 步骤3：生成字段说明文档

```bash
# 使用分析结果生成字段说明
python scripts/generate_field_spec.py analysis/F49_schema.json docs/FIELD_SPEC.md
```

### 步骤4：验证和优化

1. 检查生成的文档是否完整
2. 根据实际业务需求补充字段描述
3. 更新`generate_field_spec.py`中的字段描述字典

## 字段描述规则

`generate_field_spec.py`使用以下规则生成字段描述：

1. **预定义描述**：优先使用预定义的字段描述（如GB、PAC、NAME等）
2. **类型推断**：根据字段类型（str、int32、float）生成基础描述
3. **示例值**：如果示例值数量≤5，添加到描述中
4. **空值率警告**：如果空值率>50%，添加警告提示

## 更新字段说明

当发现新的字段或需要更新字段描述时：

1. 在`scripts/generate_field_spec.py`的`get_field_description`函数中添加或更新字段描述字典
2. 重新运行分析脚本生成新的字段说明文档
3. 验证生成的文档准确性

## 注意事项

1. **图幅差异**：不同图幅可能包含不同的字段，建议分析多个图幅以确保完整性
2. **字段命名**：GDB中的字段名可能包含大小写，导入PostgreSQL后统一转为小写
3. **空值处理**：空值率高的字段（>50%）应谨慎使用，建议结合其他字段查询
4. **示例值限制**：分析脚本只收集前10个不同的示例值，可能无法覆盖所有情况

## 相关文件

- `scripts/analyze_gdb_schema.py` - GDB图层分析脚本
- `scripts/generate_field_spec.py` - 字段说明生成脚本
- `specs/china_1m_2021.json` - 图层映射配置
- `docs/FIELD_SPEC.md` - 生成的字段说明文档
- `analysis/` - 分析结果JSON文件目录

