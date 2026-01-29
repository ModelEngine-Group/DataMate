# 步骤一：数据生成 - 不动产权证

## 简介

本模块用于生成不动产权证的模拟数据，每条记录包含13个字段的信息，并对应固定的边界框坐标。

## 文件说明

```
generate_data/
├── process.py                    # 主处理脚本
├── metadata.yml                 # 算子配置文件
├── requirements.txt            # 依赖包列表
├── src/
│   ├── data_generator.py        # 数据生成模块
│   └── __init__.py            # 包初始化
└── README.md                  # 本说明文件
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

### 基本用法（生成 5 条数据）

```bash
python process.py
```

### 自定义数量

```bash
# 生成 100 条数据
python process.py -n 100

# 生成 1000 条数据，指定随机种子
python process.py -n 1000 -s 123
```

## 输出说明

输出JSON文件（默认：`generated_records.json`），包含以下结构：

```json
[
  [
    {
      "type": "沧",
      "bbox": [530, 128, 565, 157]
    },
    {
      "type": "2024",
      "bbox": [575, 125, 630, 154]
    },
    ...
  ]
]
```

每条记录包含13个字段：
1. 地区标识（固定为"沧"）
2. 年份（2020-2030随机）
3. 县名（模拟县名）
4. 文档编号（7位数字）
5. 权利人姓名
6. 所有权形式（共同拥有/单独所有/家庭共有）
7. 登记地址
8. 不动产权证书号（15位数字）
9. 权利类型
10. 权利性质
11. 用途（住宅/商业/办公/工业/仓储）
12. 面积信息（土地使用权面积和房屋建筑面积）
13. 土地使用期限

## 常见问题

### Q: 提示 "找不到模块 'faker'"

**A**: 请先安装依赖：`pip install -r requirements.txt`

### Q: 中文在控制台显示乱码

**A**: 这是 Windows 控制台编码问题，不影响生成的数据文件。

### Q: 如何修改生成数据的字段？

**A**: 修改 `src/data_generator.py` 中的字段生成方法。

## 技术支持

如有问题，请联系项目组。

---

**版本**: v1.0
**日期**: 2026-01-25
