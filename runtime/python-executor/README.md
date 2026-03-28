# Ray Executor

## Overview

Ray Executor is a Ray-based distributed execution framework responsible for executing data processing operators, task scheduling, and distributed computing.

## Architecture

```
runtime/python-executor/
└── datamate/
    ├── core/
    │   ├── base_op.py      # BaseOp, Mapper, Filter, Slicer, LLM
    │   ├── dataset.py      # Dataset processing
    │   └── constant.py     # Constant definitions
    ├── scheduler/
    │   ├── scheduler.py    # TaskScheduler, Task, TaskStatus
    │   ├── func_task_scheduler.py   # Function task scheduling
    │   └── cmd_task_scheduler.py    # Command task scheduling
    ├── wrappers/
    │   ├── executor.py     # Ray executor entry point
    │   ├── datamate_wrapper.py      # DataMate task wrapper
    │   └── data_juicer_wrapper.py   # DataJuicer integration
    └── common/utils/       # Utility functions
        ├── bytes_transform.py
        ├── file_scanner.py
        ├── lazy_loader.py
        └── text_splitter.py
```

## Components

### 1. Base Classes

#### BaseOp
Base class for all operators:

```python
class BaseOp:
    def __init__(self, *args, **kwargs):
        self.accelerator = kwargs.get('accelerator', "cpu")
        self.text_key = kwargs.get('text_key', "text")
        # ... other configuration
    
    def execute(self, sample):
        raise NotImplementedError
```

#### Mapper
Base class for data transformation operators (1:1):

```python
class Mapper(BaseOp):
    def execute(self, sample: Dict) -> Dict:
        # Transformation logic
        return processed_sample
```

#### Filter
Base class for data filtering operators (returns bool):

```python
class Filter(BaseOp):
    def execute(self, sample: Dict) -> bool:
        # Filtering logic
        return True  # Keep or filter out
```

#### Slicer
Base class for data slicing operators (1:N):

```python
class Slicer(BaseOp):
    def execute(self, sample: Dict) -> List[Dict]:
        # Slicing logic
        return [sample1, sample2, ...]
```

#### LLM
Base class for LLM operators:

```python
class LLM(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = self.get_llm(*args, **kwargs)
    
    def build_llm_prompt(self, *args, **kwargs):
        raise NotImplementedError
```

### 2. Task Scheduler

Async task scheduler:

```python
class TaskScheduler:
    def __init__(self, max_concurrent: int = 10):
        self.tasks: Dict[str, Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def submit(self, task_id, task, *args, **kwargs):
        # Submit task
        pass
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        # Get task status
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        # Cancel task
        pass
```

### 3. Operator Execution

#### Operator Registration
```python
from datamate.core.base_op import OPERATORS

OPERATORS.register_module(
    module_name='YourOperatorName',
    module_path="ops.user.operator_package.process"
)
```

#### Execute Operator
```python
from datamate.core.base_op import Mapper

class MyMapper(Mapper):
    def execute(self, sample):
        text = sample.get('text', '')
        processed = text.upper()
        sample['text'] = processed
        return sample
```

## Quick Start

### Prerequisites
- Python 3.11+
- Ray 2.7.0+
- Poetry

### Installation
```bash
cd runtime/python-executor
poetry install
```

### Start Ray Head
```bash
ray start --head
```

### Start Ray Worker
```bash
ray start --head-address=<head-ip>:6379
```

## Usage

### Submit Task to Ray
```python
from ray import remote

@remote
def execute_operator(sample, operator_config):
    # Execute operator logic
    return result

# Submit task
result_ref = execute_operator.remote(sample, config)
result = ray.get(result_ref)
```

### Use Task Scheduler
```python
from datamate.scheduler.scheduler import TaskScheduler

scheduler = TaskScheduler(max_concurrent=10)
task_id = "task-001"
scheduler.submit(task_id, my_function, arg1, arg2)
status = scheduler.get_task_status(task_id)
```

## Development

### Adding a New Operator
1. Create operator directory in `runtime/ops/`
2. Implement `process.py` and `__init__.py`
3. Register operator in `__init__.py`
4. Test the operator

### Debugging Operators
```bash
# Local test
python -c "from ops.user.operator_package.process import YourOperatorName; op = YourOperatorName(); print(op.execute({'text': 'test'}))"
```

## Performance

### Parallel Execution
Ray automatically handles parallel execution and resource allocation.

### Fault Tolerance
Ray provides automatic task retry and failover.

### Resource Management
Ray dynamically allocates CPU, GPU, and memory resources.

## Documentation

- [Ray Documentation](https://docs.ray.io/)
- [AGENTS.md](./AGENTS.md)

## Related Links

- [Runtime README](../README.md)
- [Operator Ecosystem](../ops/README.md)
