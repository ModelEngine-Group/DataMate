# 自定义算子开发规范指南

本文档旨在为开发者提供一套标准的自定义数据处理算子开发规范。通过遵循本指南，您可以开发出能够无缝集成到数据处理系统中的高质量算子。

## 1. 目录结构规范

一个标准的算子开发包（Package）应包含以下核心文件。请确保文件命名准确，以便系统正确识别。

```text
operator_package/
├── __init__.py        # [必要] 算子注册入口，用于将算子注册到全局工厂
├── metadata.yml       # [必要] 算子元数据、UI 参数定义及资源配置
├── process.py         # [必要] 算子核心逻辑代码
├── requirements.txt   # [可选] 算子运行所需的第三方 Python 依赖
└── README.md          # [可选] 算子功能说明文档

```

---

## 2. 元数据与配置 (metadata.yml)

`metadata.yml` 定义了算子在系统中的“身份”、前端显示的配置组件以及运行时资源限制。

### 2.1 基础信息配置

| 字段 | 说明                                 | 示例 |
| --- |------------------------------------| --- |
| `name` | 算子显示名称                             | 测试算子 |
| `description` | 算子描述                               | 这是一个测试算子。 |
| `language` | 算子使用的语言，当前仅支持python                | python |
| `raw_id` | **关键字段**，必须与 `process.py` 中的类名完全一致 | TestMapper |
| `version` | 语义化版本号                             | 1.0.0 |
| `modal` / `inputs` / `outputs` | 支持的数据模态 (text/image/audio/video)   | text |

### 2.2 算子版本更新日志 (release)

定义算子当前版本较上版本更新内容。

```yaml
release:
  - '首次发布'
  - '支持基本处理操作'
```

### 2.2 运行时资源与指标 (runtime & metrics)

定义算子运行时的资源配额及性能指标参考。

```yaml
runtime:
  memory: 10MB  # 内存限制
  cpu: 1000m    # CPU 核心数 (m代表毫核)
  gpu: 0.1      # GPU 卡数
  npu: 0.1      # NPU 卡数
  storage: 10MB # 存储空间

metrics:        # 算子性能参考指标
  - name: '吞吐量'
    metric: '20 images/sec'
  - name: '准确率'
    metric: '99.5%'
```

### 2.3 参数设置 (settings) - UI 组件规范

通过 `settings` 字段，开发者可以自定义用户在前端界面配置算子时的交互组件。系统支持以下类型：

* **Slider (滑动条)** - 用于数值范围调整
```yaml
sliderParam:            # 参数的唯一标识符，process.py 中通过该参数获取值
  name: '参数展示名称'    # 界面上显示给用户的参数标题
  description: '参数展示描述'   # 用户鼠标悬停时显示的详细功能说明或帮助文本
  type: 'slider'      # 组件类型
  defaultVal: 0.5     # 算子加载时的初始值，必须位于 min 和 max 之间
  required: false     # 是否必填
  min: 0    # [下限] 滑动条允许调整的最小值
  max: 1    # [上限] 滑动条允许调整的最大值
  step: 0.1 # [步长] 每次拖动的增量 (例如 0.1 代表保留一位小数，1 代表整数)
```

* **Switch (开关)** - 用于布尔值控制
```yaml
switchParam:
  name: '参数展示名称'
  description: '参数展示描述'
  type: 'switch'
  defaultVal: 'true'        # 注意 yaml 中布尔值建议使用引号或标准写法
  required: false           # 是否必须参数
  checkedLabel: '选中'       # 选中时的展示
  unCheckedLabel: '未选中'   # 未选中时的展示
```

* **Select / Radio (下拉 / 单选)** - 用于枚举选项
```yaml
selectParam:
  name: '参数展示名称'
  description: '参数展示描述'
  type: 'select' # 或 'radio'
  defaultVal: 'option1'   # 默认后端传递值，为options其中一个选项
  required: false
  options:
    - label: '选项1'      # 前端显示标签
      value: 'option1'   # 后端传递值
    - label: '选项2'
      value: 'option2'
```

* **Range (范围区间)**
```yaml
rangeParam:
  name: '参数展示名称'
  description: '参数展示描述'
  type: 'range'
  properties:
    - name: 'rangeLeft'   # 范围下限
      type: 'inputNumber'
      defaultVal: 100
      min: 0
      max: 10000
      step: 1
    - name: 'rangeRight'  # 范围上限
      type: 'inputNumber'
      defaultVal: 8000
      min: 0
      max: 10000
      step: 1
```

* **Checkbox (多选)**
```yaml
checkboxParam:
  name: '参数展示名称'
  description: '参数展示描述'
  type: 'checkbox'
  defaultVal: 'option1,option2'   # 多个值用逗号分隔
  required: false
  options:
    - label: '选项1'
      value: 'option1'
    - label: '选项2'
      value: 'option2'

```

* **Input (文本输入)**
```yaml
inputParam:
  name: '参数展示名称'
  description: '参数展示描述'
  type: 'input'
  defaultVal: '默认值'
  required: false
```

---

## 3. 核心逻辑实现 (`process.py`)

`process.py` 是算子的执行主体。开发者需继承基础类并实现数据处理逻辑。

### 开发规范

1. **继承基类**：必须从 `datamate.core.base_op` 继承 `Mapper`或 `Filter`。
2. **类名一致性**：Python 类名建议与后续 `metadata.yml` 中的 `raw_id` 保持一致。
3. **Execute 方法**：必须实现 `execute` 方法，接收 `sample` (字典) 并返回处理后的字典。

### 代码模板

```python
from typing import Dict, Any
from datamate.core.base_op import Mapper

class YourOperatorName(Mapper):
    """
    算子类名建议使用驼峰命名法定义，例如 TestMapper
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slider_param = float(kwargs.get("sliderParam", 0.5))
        self.switch_param = kwargs.get('switchParam', False)
        self.select_param = kwargs.get('selectParam', '')
        self.radio_param = kwargs.get('radioParam', '')
        self.range_param = kwargs.get('rangeParam', [0, 0])
        self.checkbox_param = kwargs.get('checkboxParam', [])
        self.input_param = kwargs.get('inputParam', '').strip()
    
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        :param sample: 输入的数据样本，通常包含 text_key 等字段
        :return: 处理后的数据样本
        """
        # 示例：获取文本并进行修改
        # input_text = sample['text']
        # processed_text = do_something(input_text)
        # sample['text'] = processed_text
        
        return sample

```

---

## 4. 算子注册 (`__init__.py`)

`__init__.py` 用于将开发好的算子注册到系统中。

### 注册规范

使用 `OPERATORS.register_module` 方法进行注册。

* **module_name**: 对应 `metadata.yml` 中的 `raw_id` 及 Python 类名。
* **module_path**: 指向 `process.py` 的引用路径（注意路径层级）。

### 代码模板

```python
# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 假设 process.py 位于 operator_package 目录下
OPERATORS.register_module(
    module_name='YourOperatorName',
    module_path="ops.user.operator_package.process"
)

```

---

## 5. 开发注意事项

1. **依赖管理**：如果算子依赖非标准库（如 pandas, numpy），请在 `requirements.txt` 中列出。
2. **异常处理**：在 `process.py` 中建议添加适当的 try-catch 逻辑，避免单条数据异常导致整个任务崩溃。
3. **数据类型**：在 `metadata.yml` 中定义的参数类型（如 slider 返回 float，input 返回 string），在 Python 代码中使用时需注意类型转换。

---

## 6. 算子打包与上传

开发完成后，需将所有文件打包为一个压缩包进行上传。**包名必须严格遵循注册路径规范**。

### 打包规范

1. **文件完整性**：压缩包内必须包含 `__init__.py`, `metadata.yml`, `process.py` 及相关依赖。
2. **命名一致性（重要）**：压缩包的文件名（不含后缀）必须与 `__init__.py` 中 `module_path` 所指定的**包目录名**保持一致。

### 示例说明

假设您在 `__init__.py` 中的注册代码如下：

```python
OPERATORS.register_module(
    module_name='TestMapper',
    # 这里 ops.user.my_custom_op.process 中的 'my_custom_op' 为包目录名
    module_path="ops.user.my_custom_op.process"
)

```

则您的压缩包名称必须命名为：

> **`my_custom_op.zip`** (或 .tar)

系统解压后将基于此名称构建导入路径，名称不一致将导致 `ModuleNotFoundError`。
