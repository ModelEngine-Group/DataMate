# 自定义算子开发指南

## 算子规范

### 算子元数据格式

每个自定义算子都需要包含一个 `metadata.json` 文件：

```json
{
  "name": "custom_text_processor",
  "displayName": "自定义文本处理器",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "自定义文本处理算子示例",
  "category": "数据处理",
  "type": "CUSTOM",
  "inputs": [
    {
      "name": "input_text",
      "type": "string",
      "description": "输入文本",
      "required": true
    }
  ],
  "outputs": [
    {
      "name": "processed_text",
      "type": "string",
      "description": "处理后的文本"
    }
  ],
  "parameters": [
    {
      "name": "max_length",
      "type": "integer",
      "description": "最大长度",
      "default": 1000,
      "min": 1,
      "max": 10000
    },
    {
      "name": "case_conversion",
      "type": "string",
      "description": "大小写转换",
      "default": "none",
      "enum": ["none", "upper", "lower", "title"]
    }
  ]
}
```

### 算子实现

创建 `operator.py` 文件：

```python
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class OperatorConfig:
    name: str
    parameters: Dict[str, Any]

@dataclass
class ExecutionContext:
    task_id: str
    input_path: str
    output_path: str
    temp_path: str

class CustomTextProcessor:
    """自定义文本处理器算子"""
    
    def __init__(self):
        self.name = "custom_text_processor"
        self.version = "1.0.0"
    
    def execute(self, config: OperatorConfig, context: ExecutionContext) -> Dict[str, Any]:
        """执行算子逻辑"""
        
        # 获取参数
        max_length = config.parameters.get('max_length', 1000)
        case_conversion = config.parameters.get('case_conversion', 'none')
        
        # 读取输入数据
        with open(context.input_path, 'r', encoding='utf-8') as f:
            input_text = f.read()
        
        # 处理逻辑
        processed_text = self._process_text(input_text, max_length, case_conversion)
        
        # 写入输出数据
        with open(context.output_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        
        return {
            'input_length': len(input_text),
            'output_length': len(processed_text),
            'truncated': len(input_text) > max_length
        }
    
    def _process_text(self, text: str, max_length: int, case_conversion: str) -> str:
        """文本处理逻辑"""
        
        # 长度截断
        if len(text) > max_length:
            text = text[:max_length]
        
        # 大小写转换
        if case_conversion == 'upper':
            text = text.upper()
        elif case_conversion == 'lower':
            text = text.lower()
        elif case_conversion == 'title':
            text = text.title()
        
        return text

# 算子工厂函数
def create_operator():
    return CustomTextProcessor()
```

## 算子安装与注册

### 1. 本地开发

将算子文件放置在 `runtime/operators/custom/` 目录下：

```
runtime/operators/custom/
├── custom_text_processor/
│   ├── metadata.json
│   ├── operator.py
│   ├── requirements.txt (可选)
│   └── README.md (可选)
```

### 2. 通过算子市场注册

使用API接口注册算子：

```bash
curl -X POST http://localhost:8080/api/operators \
  -H "Content-Type: multipart/form-data" \
  -F "metadata=@metadata.json" \
  -F "code=@operator.py" \
  -F "requirements=@requirements.txt"
```

### 3. 测试算子

```python
# test_operator.py
import json
from operator import create_operator
from operator_runtime import OperatorConfig, ExecutionContext

# 创建测试配置
config = OperatorConfig(
    name="custom_text_processor",
    parameters={
        "max_length": 500,
        "case_conversion": "lower"
    }
)

context = ExecutionContext(
    task_id="test-001",
    input_path="/tmp/input.txt",
    output_path="/tmp/output.txt",
    temp_path="/tmp"
)

# 创建算子实例并执行
operator = create_operator()
result = operator.execute(config, context)

print(json.dumps(result, indent=2))
```

## 最佳实践

### 1. 错误处理

```python
def execute(self, config: OperatorConfig, context: ExecutionContext) -> Dict[str, Any]:
    try:
        # 算子逻辑
        pass
    except FileNotFoundError as e:
        raise ValueError(f"输入文件不存在: {e}")
    except Exception as e:
        raise RuntimeError(f"算子执行失败: {e}")
```

### 2. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

def execute(self, config: OperatorConfig, context: ExecutionContext) -> Dict[str, Any]:
    logger.info(f"开始执行算子: {self.name}")
    logger.debug(f"参数: {config.parameters}")
    
    # 算子逻辑
    
    logger.info("算子执行完成")
```

### 3. 进度报告

```python
def execute(self, config: OperatorConfig, context: ExecutionContext) -> Dict[str, Any]:
    total_items = 1000
    
    for i, item in enumerate(items):
        # 处理单个项目
        
        # 报告进度
        if i % 100 == 0:
            progress = (i + 1) / total_items * 100
            logger.info(f"处理进度: {progress:.1f}%")
```

### 4. 资源管理

```python
import tempfile
import os

def execute(self, config: OperatorConfig, context: ExecutionContext) -> Dict[str, Any]:
    # 使用临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        tmp_path = tmp_file.name
        # 使用临时文件
    
    try:
        # 算子逻辑
        pass
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
```
