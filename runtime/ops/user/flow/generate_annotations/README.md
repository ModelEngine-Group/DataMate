# QA生成算子

## 简介

本算子用于为流水资产分析表生成多模态训练用的问答对，支持多种QA类型。

## 功能特性

- 支持多种QA类型生成
- 自动关联JSON数据和图片文件
- 支持批量生成QA对
- 灵活的QA模板系统

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| qaCountParam | slider | 10 | 每个样本生成的QA对数量 |
| qaTypeParam | checkbox | basic,detailed,complex | 生成的QA类型 |

## 支持的QA类型

- **基础信息 (basic)**: 文档类型、户名、账号等基本信息
- **详细信息 (detailed)**: 统计期间、资金流入等详细信息
- **复杂推理 (complex)**: 需要多步推理的复杂问题

## 输入输出

**输入**:
- JSON数据文件
- 图片文件（PNG/JPG/JPEG格式）

**输出**:
- QA对JSON文件
- 生成数量统计
- 使用的QA类型

## QA对格式

```json
{
  "id": "flow_qa_1",
  "image": "path/to/image.png",
  "conversations": [
    {
      "from": "human",
      "value": "<image>
这是什么类型的文档？"
    },
    {
      "from": "gpt",
      "value": "这是一份银行账户流水证明"
    }
  ]
}
```

## 使用示例

```python
# 在流水线中使用
operator = FlowQAGenOperator(
    qaCountParam=10,
    qaTypeParam=['basic', 'detailed']
)

result = operator.execute({
    'export_path': '/path/to/data',
    'instance_id': 'flow_001'
})
```

## 依赖项

- loguru >= 0.7.0

## 版本信息

- 版本：v1.0
- 日期：2026-01-28
- 供应商：datamate
