# DataMate 数据模型结构

本文档列出了根据 `scripts/db` 中的 SQL 文件创建的所有 Python 数据模型。

## 模型组织结构

```
app/models/
├── __init__.py                 # 主模块导出文件
├── dm/                         # 数据管理 (Data Management) 模块
│   ├── __init__.py
│   ├── annotation_template.py  # 标注模板
│   ├── labeling_project.py     # 标注项目
│   ├── dataset.py              # 数据集
│   ├── dataset_files.py        # 数据集文件
│   ├── dataset_statistics.py   # 数据集统计
│   ├── dataset_tag.py          # 数据集标签关联
│   ├── tag.py                  # 标签
│   └── user.py                 # 用户
├── cleaning/                   # 数据清洗 (Data Cleaning) 模块
│   ├── __init__.py
│   ├── clean_template.py       # 清洗模板
│   ├── clean_task.py           # 清洗任务
│   ├── operator_instance.py    # 算子实例
│   └── clean_result.py         # 清洗结果
├── collection/                 # 数据归集 (Data Collection) 模块
│   ├── __init__.py
│   ├── task_execution.py       # 任务执行明细
│   ├── collection_task.py      # 数据归集任务
│   ├── task_log.py             # 任务执行记录
│   └── datax_template.py       # DataX模板配置
├── common/                     # 通用 (Common) 模块
│   ├── __init__.py
│   └── chunk_upload_request.py # 文件切片上传请求
└── operator/                   # 算子 (Operator) 模块
    ├── __init__.py
    ├── operator.py             # 算子
    ├── operator_category.py    # 算子分类
    └── operator_category_relation.py  # 算子分类关联
```

## 模块详情

### 1. Data Management (DM) 模块
对应 SQL: `data-management-init.sql` 和 `data-annotation-init.sql`

#### 模型列表：
- **AnnotationTemplate** (`t_dm_annotation_templates`) - 标注模板
- **LabelingProject** (`t_dm_labeling_projects`) - 标注项目
- **Dataset** (`t_dm_datasets`) - 数据集（支持医学影像、文本、问答等多种类型）
- **DatasetFiles** (`t_dm_dataset_files`) - 数据集文件
- **DatasetStatistics** (`t_dm_dataset_statistics`) - 数据集统计信息
- **Tag** (`t_dm_tags`) - 标签
- **DatasetTag** (`t_dm_dataset_tags`) - 数据集标签关联
- **User** (`users`) - 用户

### 2. Data Cleaning 模块
对应 SQL: `data-cleaning-init.sql`

#### 模型列表：
- **CleanTemplate** (`t_clean_template`) - 清洗模板
- **CleanTask** (`t_clean_task`) - 清洗任务
- **OperatorInstance** (`t_operator_instance`) - 算子实例
- **CleanResult** (`t_clean_result`) - 清洗结果

### 3. Data Collection (DC) 模块
对应 SQL: `data-collection-init.sql`

#### 模型列表：
- **TaskExecution** (`t_dc_task_executions`) - 任务执行明细
- **CollectionTask** (`t_dc_collection_tasks`) - 数据归集任务
- **TaskLog** (`t_dc_task_log`) - 任务执行记录
- **DataxTemplate** (`t_dc_datax_templates`) - DataX模板配置

### 4. Common 模块
对应 SQL: `data-common-init.sql`

#### 模型列表：
- **ChunkUploadRequest** (`t_chunk_upload_request`) - 文件切片上传请求

### 5. Operator 模块
对应 SQL: `data-operator-init.sql`

#### 模型列表：
- **Operator** (`t_operator`) - 算子
- **OperatorCategory** (`t_operator_category`) - 算子分类
- **OperatorCategoryRelation** (`t_operator_category_relation`) - 算子分类关联

## 使用方式

```python
# 导入所有模型
from app.models import (
    # DM 模块
    AnnotationTemplate,
    LabelingProject,
    Dataset,
    DatasetFiles,
    DatasetStatistics,
    DatasetTag,
    Tag,
    User,
    # Cleaning 模块
    CleanTemplate,
    CleanTask,
    OperatorInstance,
    CleanResult,
    # Collection 模块
    TaskExecution,
    CollectionTask,
    TaskLog,
    DataxTemplate,
    # Common 模块
    ChunkUploadRequest,
    # Operator 模块
    Operator,
    OperatorCategory,
    OperatorCategoryRelation
)

# 或者按模块导入
from app.models.dm import Dataset, DatasetFiles
from app.models.collection import CollectionTask
from app.models.operator import Operator
```

## 注意事项

1. **UUID 主键**: 大部分表使用 UUID (String(36)) 作为主键
2. **时间戳**: 使用 `TIMESTAMP` 类型，并配置自动更新
3. **软删除**: 部分模型（如 AnnotationTemplate, LabelingProject）支持软删除，包含 `deleted_at` 字段和 `is_deleted` 属性
4. **JSON 字段**: 配置信息、元数据等使用 JSON 类型存储
5. **字段一致性**: 所有模型字段都严格按照 SQL 定义创建，确保与数据库表结构完全一致

## 更新记录

- 2025-10-25: 根据 `scripts/db` 中的 SQL 文件创建所有数据模型
- 已更新现有的 `annotation_template.py`、`labeling_project.py`、`dataset_files.py` 以匹配 SQL 定义
