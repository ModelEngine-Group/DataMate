# 图像增强合成算子

## 简介

本算子用于将文档图像合成到真实背景中，支持多种场景模式，包括标准拍摄、斜拍、阴影、水印和不完整拍摄等。

## 功能特性

- 支持多种真实场景模拟
- 自动检测文档区域坐标
- 支持坐标缓存，提高处理效率
- 自动旋转和比例校正
- 支持水印添加
- 批量处理图片

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| scenesParam | select | 2 | 每张图随机选择几个场景 |
| sceneListParam | checkbox | normal,tilted,shadow,watermark,incomplete | 允许生成的场景类型 |
| skipDetectParam | switch | True | 是否跳过坐标检测 |

## 支持的场景

- **标准 (Normal)**: 正对或微倾斜，光照均匀
- **斜拍 (Tilted)**: 透视变形较大
- **阴影 (Shadow)**: 光照不均匀，有投影
- **水印 (Watermark)**: 桌面或背景有复杂纹理
- **不完整 (Incomplete)**: 凭证部分在画面外

## 输入输出

**输入**:
- 源图文件（PNG格式）
- 背景图文件（JPG/JPEG/PNG格式）

**输出**:
- 合成后的图片文件
- 增强数量统计
- 使用的场景列表

## 使用示例

```python
# 在流水线中使用
operator = FlowImgAugOperator(
    scenesParam=2,
    sceneListParam=['normal', 'tilted', 'shadow'],
    skipDetectParam=True
)

result = operator.execute({
    'export_path': '/path/to/images',
    'instance_id': 'flow_001'
})
```

## 依赖项

- opencv-python >= 4.8.0
- numpy >= 1.24.0
- loguru >= 0.7.0

## 版本信息

- 版本：v1.0
- 日期：2026-01-28
- 供应商：datamate
