# 自定义算子开发指南

## 算子规范

### 算子元数据格式

每个自定义算子都需要包含一个 `metadata.yml` 文件：

```yaml
name: '测试算子'
description: '这是一个测试算子。'
language: 'python'
vendor: 'huawei'
raw_id: 'TestMapper'
version: '1.0.0'
modal: 'text'   # text/image/audio/video/multimodal
inputs: 'text'
outputs: 'text'
```

### 算子实现

#### process.py

```python
# -*- coding: utf-8 -*-

# 导入所需数据结构，可以通过以下方式直接导入使用
# 提供两种算子类：
# Mapper用于映射和转换数据，使用时直接修改数据内容
from datamate.core.base_op import Mapper

class TestMapper(Mapper):
    def execute(self, sample):
        sample[self.text_key] += "\n新增的数据"
        return sample


# Filter用于过滤和选择性保留数据，使用时将需要过滤的数据的text或data置为空值
from datamate.core.base_op import Filter

class TestFilter(Filter):
    def execute(self, sample):
        if len(sample[self.text_key]) > 100:
            sample[self.text_key] += ""
        return sample

```

其中，sample的数据结构如下所示:
```json lines
// 数据结构
{
  "text": "数据文件的文本内容",
  "data": "多模态文件的内容",
  "fileName": "文件名称",
  "fileType": "文件类型",
  "filePath": "文件路径",
  "fileSize": "文件大小",
  "export_path": "保存的文件路径",
  "extraFileType": "导出的文件类型"
}

// 数据示例
{
  "text": "text",
  "data": "data",
  "fileName": "test",
  "fileType": "pdf",
  "filePath": "/dataset/test.pdf",
  "fileSize": "100B",
  "export_path": "/dataset/test.txt",
  "extraFileType": "txt"
}
```

####  \_\_init__.py

```python
# -*- coding: utf-8 -*-

# 导入OPERATORS用于进行模块注册，可以通过以下方式直接导入使用
from datamate.core.base_op import OPERATORS

# module_name必须填写算子类名称；module_path中须替换模块的算子压缩包名称：python_operator.user.压缩包名.process
OPERATORS.register_module(module_name='TestMapper',
                          module_path="ops.user.test_operator.process")

```
