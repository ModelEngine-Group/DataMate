# Word文档转图片工具

## 功能描述

将Word文档(.docx)转换为图片，支持多种转换方式并自动选择最佳方案。

## 依赖环境

- **win32com/pywin32**: 调用Word COM组件转PDF（最佳质量）
- **pdf2image**: PDF转图片（依赖poppler）
- **docx2pdf**: 无需Word的PDF转换方案
- **python-docx**: 纯Python解析Word文档（备用）
- **PIL (Pillow)**: 图片处理和渲染

## 调用方式

```bash
# 基本用法
python convert_to_image.py input.docx output_dir

# 指定输出目录
python convert_to_image.py D:\\docs\\test.docx D:\\images
```

## 参数说明

- `input_path`: 输入Word文档路径
- `output_dir`: 输出图片存放目录

## 转换方法优先级

1. **win32com_poppler**: Word → PDF → Poppler（最佳质量，需要安装Word）
2. **docx2pdf_poppler**: docx2pdf → Poppler（无需Word）
3. **win32com_direct**: Word直接渲染
4. **python_docx**: 纯Python渲染（备用方案）

## 流程图

```
开始
  ↓
检测可用转换方法
  ↓
选择最佳转换方案
  ↓
┌─────────────────┬─────────────────┬──────────────────┐
│ win32com+poppler│ docx2pdf+poppler│  python-docx     │
│ (推荐)          │                 │  (备用)          │
└────────┬────────┴────────┬────────┴────────┬─────────┘
         ↓                 ↓                 ↓
    Word→PDF→Image    docx2PDF→Image   纯Python渲染
         ↓                 ↓                 ↓
    保存PNG图片 ← ← ← ← ← ← ← ← ← ← ← ←
         ↓
       结束
```

## 注意事项

- **Poppler推荐版本**: poppler-24.08.0（稳定）
- **避免版本**: poppler-25.12.0（已知兼容性问题）
- **默认DPI**: 200（推荐范围150-300）
