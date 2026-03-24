# Ray 执行器

## 概述

Ray 执行器是基于 Ray 的分布式执行框架，负责执行数据处理算子、任务调度和分布式计算。

## 架构

```
runtime/python-executor/
└── datamate/
    ├── core/
    │   ├── base_op.py      # BaseOp, Mapper, Filter, Slicer, LLM
    │   ├── dataset.py      # Dataset 处理
    │   └── constant.py     # 常量定义
    ├── scheduler/
    │   ├── scheduler.py    # TaskScheduler, Task, TaskStatus
    │   ├── func_task_scheduler.py   # 函数任务调度
    │   └── cmd_task_scheduler.py    # 命令任务调度
    ├── wrappers/
    │   ├── executor.py     # Ray 执行器入口
    │   ├── datamate_wrapper.py      # DataMate 任务包装
    │   └── data_juicer_wrapper.py   # DataJuicer 集成
    └── common/utils/       # 工具函数
        ├── bytes_transform.py
        ├── file_scanner.py
        ├── lazy_loader.py
        └── text_splitter.py
```

## 组件

### 1. Base 类

#### BaseOp
所有算子的基类：

```python
class BaseOp:
    def __init__(self, *args, **kwargs):
        self.accelerator = kwargs.get('accelerator', "cpu")
        self.text_key = kwargs.get('text_key', "text")
        # ... 其他配置
    
    def execute(self, sample):
        raise NotImplementedError
```

#### Mapper
数据转换算子基类（1:1）：

```python
class Mapper(BaseOp):
    def execute(self, sample: Dict) -> Dict:
        # 转换逻辑
        return processed_sample
```

#### Filter
数据过滤算子基类（返回 bool）：

```python
class Filter(BaseOp):
    def execute(self, sample: Dict) -> bool:
        # 过滤逻辑
        return True  # 保留或过滤
```

#### Slicer
数据切片算子基类（1:N）：

```python
class Slicer(BaseOp):
    def execute(self, sample: Dict) -> List[Dict]:
        # 切片逻辑
        return [sample1, sample2, ...]
```

#### LLM
LLM 算子基类：

```python
class LLM(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = self.get_llm(*args, **kwargs)
    
    def build_llm_prompt(self, *args, **kwargs):
        raise NotImplementedError
```

### 2. Task Scheduler

异步任务调度器：

```python
class TaskScheduler:
    def __init__(self, max_concurrent: int = 10):
        self.tasks: Dict[str, Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def submit(self, task_id, task, *args, **kwargs):
        # 提交任务
        pass
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        # 获取任务状态
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        # 取消任务
        pass
```

### 3. 算子执行

#### 算子注册
```python
from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='YourOperatorName',
    module_path="ops.user.operator_package.process"
)
```

#### 执行算子
```python
from datamate.core.base_op import Mapper

class MyMapper(Mapper):
    def execute(self, sample):
        text = sample.get('text', '')
        processed = text.upper()
        sample['text'] = processed
        return sample
```

## 快速开始

### 前置条件
- Python 3.11+
- Ray 2.7.0+
- Poetry

### 安装
```bash
cd runtime/python-executor
poetry install
```

### 启动 Ray Head
```bash
ray start --head
```

### 启动 Ray Worker
```bash
ray start --head-address=<head-ip>:6379
```

## 使用

### 提交任务到 Ray
```python
from ray import remote

@remote
def execute_operator(sample, operator_config):
    # 执行算子逻辑
    return result

# 提交任务
result_ref = execute_operator.remote(sample, config)
result = ray.get(result_ref)
```

### 使用 Task Scheduler
```python
from datamate.scheduler.scheduler import TaskScheduler

scheduler = TaskScheduler(max_concurrent=10)
task_id = "task-001"
scheduler.submit(task_id, my_function, arg1, arg2)
status = scheduler.get_task_status(task_id)
```

## 开发

### 添加新算子
1. 在 `runtime/ops/` 创建算子目录
2. 实现 `process.py` 和 `__init__.py`
3. 在 `__init__.py` 注册算子
4. 测试算子

### 调试算子
```bash
# 本地测试
python -c "from ops.user.operator_package.process import YourOperatorName; op = YourOperatorName(); print(op.execute({'text': 'test'}))"
```

## 性能

### 并行执行
Ray 自动处理并行执行和资源分配。

### 容错
Ray 提供自动任务重试和故障转移。

### 资源管理
Ray 动态分配 CPU、GPU、内存资源。

## 文档

- [Ray 文档](https://docs.ray.io/)
- [AGENTS.md](./AGENTS.md)

## 相关链接

- [运行时 README](../README.md)
- [算子生态](../ops/README.md)
