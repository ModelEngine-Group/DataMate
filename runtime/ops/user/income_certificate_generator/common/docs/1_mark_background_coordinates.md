# 背景图片坐标标记工具

## 功能描述

批量标记背景图片中文档位置，并将坐标保存到JSON文件。

## 依赖环境

- **cv2 (OpenCV)**: 图像读取、边缘检测、轮廓提取
- **numpy**: 数组运算和坐标处理
- **tkinter**: 获取屏幕分辨率用于显示适配
- **json**: 存储和读取缓存坐标
- **pathlib**: 文件路径处理

## 调用方式

```bash
# 基本用法
python 1_mark_background_coordinates.py background_folder coordinates.json

# 生成调试图
python 1_mark_background_coordinates.py background_folder coordinates.json --debug

# 强制重新标记所有图片
python 1_mark_background_coordinates.py background_folder coordinates.json --force
```

## 参数说明

- `background_folder`: 背景图片文件夹路径
- `json_path`: JSON文件路径（存储标记结果）
- `--debug`: 生成调试图，显示自动识别结果
- `--force`: 强制重新标记所有图片（包括已标记的）

## 流程图

```
开始
  ↓
读取背景图片
  ↓
检查JSON缓存 → 有缓存 → 直接使用
  ↓ 无缓存
图像预处理（双边滤波 + CLAHE增强）
  ↓
Canny边缘检测
  ↓
轮廓筛选（提取4-6边形最大轮廓）
  ↓
自动识别成功 → 保存到JSON
  ↓ 失败
手动标记（点击4个角点）→ 保存到JSON
  ↓
结束
```
