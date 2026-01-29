# 印章添加算子

## 简介

本算子用于在文档或图片上添加银行印章，支持自动检测印章位置和多种银行配置。

## 功能特性

- 支持多种银行印章模板
- 自动检测印章位置
- 可调节印章大小
- 支持批量处理图片
- 自动从JSON文件中提取银行名称

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| sealSizeParam | slider | 200 | 印章直径（像素），范围100-300 |
| bankNameParam | input | 北京兴业银行 | 银行名称，用于生成印章文字 |
| autoDetectParam | switch | True | 是否自动检测印章位置 |

## 支持的银行

算子内置了以下银行的印章配置：
- 北京兴业银行
- 上海浦发银行
- 工商银行
- 农业银行
- 中国银行
- 建设银行
- 交通银行
- 招商银行
- 浦发银行
- 中信银行
- 光大银行
- 民生银行
- 平安银行
- 华夏银行
- 兴业银行
- 广发银行
- 洛汀城市银行

## 输入输出

**输入**:
- 图片文件路径列表（支持PNG、JPG、JPEG格式）
- JSON文件（用于提取银行名称）

**输出**:
- 添加印章后的图片文件
- 处理数量统计
- 使用的银行名称

## 使用示例

```python
# 在流水线中使用
operator = SealAddOperator(
    sealSizeParam=200,
    bankNameParam='工商银行',
    autoDetectParam=True
)

result = operator.execute({
    'export_path': '/path/to/images',
    'instance_id': 'flow_001'
})
```

## 依赖项

- Pillow >= 10.0.0
- opencv-python >= 4.8.0
- numpy >= 1.24.0
- loguru >= 0.7.0

## 版本信息

- 版本：v1.0
- 日期：2026-01-28
- 供应商：datamate
