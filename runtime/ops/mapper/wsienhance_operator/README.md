# WSIEnhance WSI 智能增强分析算子

## 概述

WSIEnhance 是一个面向全玻片扫描图像（Whole Slide Image, WSI）的智能分析与增强处理算子，提供组织检测、伪影识别、质量评估和 Patch 提取等核心功能。

## 功能特性

### 1. WSI 读取
- 支持多种 WSI 格式：`.svs`, `.tif`, `.ndpi`, `.vms`, `.bif`
- 基于 OpenSlide 后端
- 多分辨率金字塔支持

### 2. 组织检测
- 基于 HSV 颜色空间的智能分割
- 形态学处理：闭运算/开运算、填充孔洞
- 细脖子切断、细桥断开、轮廓平滑

### 3. 笔迹检测
- 暗色区域检测
- 蓝墨水 HSV+RGB 联合判定
- 墨迹样细长痕迹识别

### 4. 伪影检测
- 近纯白空洞/裂隙识别
- 组织折叠检测（LAB 颜色空间）
- 深紫组织保护机制

### 5. 气泡检测（可选）
- 低饱和度高亮区域识别

### 6. Patch 提取
- 256×256 固定尺寸（可配置）
- 排除笔迹和伪影区域
- 白背景比例过滤

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| 提取 Patch | switch | false | 是否从组织区域提取 256x256 的 Patch |
| 导出 Patch 位置 | switch | true | 是否导出 Patch 在原图中的位置 JSON |
| 气泡检测 | switch | false | 是否启用气泡检测 |
| 伪影检测 | switch | true | 是否启用伪影检测 |
| 折叠处理策略 | radio | 算作组织 | 折叠区域分类策略 |
| Patch 尺寸 | slider | 256 | 提取的 Patch 大小（像素） |
| 背景灰度阈值 | slider | 210 | Patch 过滤灰度阈值 |
| 最大背景比例 | slider | 0.85 | Patch 中允许的背景最大占比 |
| 缩略图尺寸 | slider | 3072 | 生成缩略图的最大边长 |
| 组织饱和度下限 | slider | 8 | HSV 饱和度阈值 |
| 组织亮度上限 | slider | 225 | HSV 亮度上限 |
| 最小组织面积 | slider | 1000 | 最小组织连通域面积 |

## 输入输出

**输入**: 图像数据（`image_path` 字段，WSI 文件路径）

**输出**: 包含以下字段：
- `wsienhance_result`: 完整检测结果
- `wsienhance_output_dir`: 输出目录路径
- `tissue_ratio`: 组织区域占比
- `patch_count`: 提取的 Patch 数量

## 输出文件结构

```
wsienhance_results/
└── slide_name/
    ├── thumbnail.png              # 原始缩略图
    ├── thumbnail_overlay.png      # 叠加标注图
    ├── results.json               # 检测结果元数据
    ├── patch_positions.json       # Patch 位置信息（可选）
    └── patches/                   # Patch 目录（可选）
        ├── patch_0_0.png
        ├── patch_0_256.png
        └── ...
```

## 检测结果格式

```json
{
  "wsi_size": {"w": 100000, "h": 80000},
  "thumbnail": {"path": "...", "w": 3072, "h": 2458},
  "coords_thumbnail": {
    "tissue_contours": [[[x1,y1], [x2,y2], ...], ...],
    "note_contours": [...],
    "artifact_contours": [...],
    "bubble_contours": [...]
  },
  "statistics": {
    "tissue_contour_count": 5,
    "tissue_area_pixels": 1234567,
    "tissue_ratio": 0.65
  },
  "patches": {
    "count": 150,
    "dir": "..."
  }
}
```

## 依赖说明

- openslide-python >= 1.3.1
- opencv-python-headless >= 4.8.0
- numpy >= 1.21.0
- Pillow >= 9.0.0

## 注意事项

1. **OpenSlide 安装**: 需要先安装 OpenSlide 二进制包（https://openslide.org/download/），然后安装 Python 绑定

2. **内存优化**: 处理大尺寸 WSI 时，建议减小缩略图尺寸以降低内存占用

3. **参数调优**:
   - 组织检测不完整：减小 `sat_thresh` 或增大 `val_max`
   - 包含过多背景：增大 `sat_thresh` 或减小 `val_max`
   - 深紫细胞核被误标为笔迹：减小 `note_val_max`

## 版本历史

- **v1.0.0**: 首次发布，支持 WSI 组织检测、伪影识别、Patch 提取功能
