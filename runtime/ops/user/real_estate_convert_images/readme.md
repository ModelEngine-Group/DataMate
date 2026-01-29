# 步骤二：图像转换 - 不动产权证

## 简介

本模块用于将JSON数据渲染到模板图像上，生成填充后的不动产权证图像。

## 文件说明

```
convert_images/
├── process.py                    # 主处理脚本
├── metadata.yml                 # 算子配置文件
├── requirements.txt            # 依赖包列表
├── src/
│   ├── image_converter.py      # 图像转换模块
│   └── __init__.py          # 包初始化
└── README.md                # 本说明文件
```

## 安装步骤

### 1. 确保已安装 Python 3.8+

```bash
python --version
```

### 2. 安装依赖包

```bash
pip install -r requirements.txt
```

如果下载慢，使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 使用方法

### 基本用法

```bash
python process.py
```

### 指定DPI

```bash
# 使用更高的 DPI（更清晰的图片）
python process.py --dpi 300
```

## 输入要求

1. **JSON文件**：包含文本内容和bbox坐标的JSON文件（步骤1输出）
2. **模板图像**：
   - 优先使用：`template.jpg`、`template.jpeg`、`template.png`、`blank.jpg`、`bg.jpg`
   - 或当前目录下任意不含`_filled_`的图像文件

## 输出说明

生成填充后的图像文件，命名规则：`{json文件名}_filled_{序号}.{扩展名}`

例如：
- `generated_records_filled_01.jpg`
- `generated_records_filled_02.jpg`

## 注意事项

- 程序会自动跳过包含`_filled_`的图像文件，避免将输出结果作为模板
- 前4个字段使用仿宋字体并居中显示
- 其他字段使用宋体字体左对齐显示
- 字体大小会根据bbox大小自动调整

## 常见问题

### Q: 提示 "找不到模板图"

**A**: 确保当前目录下有以下任一文件：
   - `template.jpg`
   - `template.jpeg`
   - `template.png`
   - `blank.jpg`
   - `bg.jpg`
   或任意不含 `_filled_` 的图像文件

### Q: 生成的图像不清晰

**A**: 使用更高的 DPI 值，如 `--dpi 300` 或 `--dpi 400`。

### Q: 如何修改字体？

**A**: 修改 `src/image_converter.py` 中的字体路径。

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-25
