# 印章添加工具

## 功能描述

给凭证类图片添加逼真的印章效果（财务专用章/人名章/银行章），支持磨损、渐变等真实效果。

## 依赖环境

- **PIL (Pillow)**: 印章绘制、图片合成、滤镜效果
- **numpy**: 噪点生成、透明度处理
- **math**: 印章文字弧形排列计算
- **random**: 随机旋转和效果变化

## 调用方式

```bash
# 添加财务专用章
python add_seal.py input.jpg output.jpg --type finance --company "某某科技有限公司"

# 添加人名章
python add_seal.py input.jpg output.jpg --type name --person-name "张三"

# 添加银行章
python add_seal.py input.jpg output.jpg --type bank --bank-text "银行承兑"

# 添加多个印章组合
python add_seal.py input.jpg output.jpg --type multiple --company "公司名" --person-name "张三" --bank-text "银行承兑"

# 自定义透明度
python add_seal.py input.jpg output.jpg --type finance --company "公司名" --opacity 0.9
```

## 参数说明

- `input`: 输入图片路径
- `output`: 输出图片路径
- `--type`: 印章类型（finance/name/bank/multiple）
- `--company`: 公司名称（财务章）
- `--seal-text`: 财务章底部文字（默认"财务专用章"）
- `--person-name`: 人名（人名章）
- `--bank-text`: 银行文字（银行章）
- `--bank-sub-text`: 银行副文字
- `--position`: 盖章位置坐标（x y），自动计算如果不指定
- `--opacity`: 透明度0-1（默认0.85）

## 流程图

```
开始
  ↓
选择印章类型
  ↓
┌─────────┬─────────┬──────────┬──────────┐
│ finance │  name   │   bank   │ multiple │
│ 财务章  │  人名章 │  银行章  │  多章组合│
└────┬────┴────┬────┴────┬─────┴────┬─────┘
     ↓         ↓         ↓          ↓
  圆形印章   方形印章   椭圆印章   创建多印章
  (双线+星)  (边框+竖排)(椭圆+图案)
     ↓         ↓         ↓          ↓
  └─────────→ 添加印章效果 ←─────────┘
            (旋转/透明度/渐变/磨损/模糊)
                    ↓
              智能定位盖章位置
                    ↓
              泊松融合到凭证
                    ↓
              添加纸张纹理
                    ↓
                保存结果
                    ↓
                 结束
```

## 印章类型说明

- **财务专用章**: 圆形，双线边框+中心五角星+环绕公司名称
- **人名章**: 方形，边框+竖排姓名（从右到左）
- **银行章**: 椭圆形，双线边框+中心圆形图案+主副文字
- **多章组合**: 同时添加财务章、人名章、银行章
