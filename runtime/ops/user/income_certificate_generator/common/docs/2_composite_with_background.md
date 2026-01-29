# 图片合成工具

## 功能描述

将原始图片嵌入到随机选择的背景图片中，实现真实场景合成效果。

## 依赖环境

- **cv2 (OpenCV)**: 透视变换、色彩空间转换、泊松融合
- **numpy**: 数组运算和坐标计算
- **json**: 读取背景坐标数据
- **pathlib**: 文件路径处理

## 调用方式

```bash
# 单张图片合成（随机选择背景）
python 2_composite_with_background.py source.jpg coordinates.json background_folder output_folder

# 指定背景图片
python 2_composite_with_background.py source.jpg coordinates.json background_folder output_folder --bg "桌面.jpg"

# 批量合成模式
python 2_composite_with_background.py source_folder coordinates.json background_folder output_folder --batch --count 3
```

## 参数说明

- `source`: 原始图片路径或文件夹
- `json_path`: JSON文件路径（包含背景坐标）
- `background_folder`: 背景图片文件夹路径
- `output_folder`: 输出文件夹路径
- `--bg`: 指定背景图片文件名（可选）
- `--batch`: 批量处理模式
- `--count`: 每张原始图片生成的合成图数量（默认1）

## 流程图

```
开始
  ↓
读取原始图片和JSON坐标
  ↓
随机选择背景图片（或指定背景）
  ↓
判断场景类型（normal/tilted/shadow/watermark/incomplete）
  ↓
自动旋转校正（横版/竖版匹配）
  ↓
比例校正（补白边防止变形）
  ↓
透视变换（映射到目标区域）
  ↓
色彩匹配（LAB空间光照适配）
  ↓
泊松融合（自然边界）
  ↓
保存合成结果
  ↓
结束
```
