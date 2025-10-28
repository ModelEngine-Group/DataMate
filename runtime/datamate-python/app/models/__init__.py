# app/models/__init__.py

# Data Management (DM) 模块
from .dm import (
    AnnotationTemplate,
    LabelingProject,
    Dataset,
    DatasetFiles,
    DatasetStatistics,
    DatasetTag,
    Tag,
    User
)

# Data Cleaning 模块
from .cleaning import (
    CleanTemplate,
    CleanTask,
    OperatorInstance,
    CleanResult
)

# Data Collection (DC) 模块
from .collection import (
    TaskExecution,
    CollectionTask,
    TaskLog,
    DataxTemplate
)

# Common 模块
from .common import (
    ChunkUploadRequest
)

# Operator 模块
from .operator import (
    Operator,
    OperatorCategory,
    OperatorCategoryRelation
)

__all__ = [
    # DM 模块
    "AnnotationTemplate",
    "LabelingProject",
    "Dataset",
    "DatasetFiles",
    "DatasetStatistics",
    "DatasetTag",
    "Tag",
    "User",
    # Cleaning 模块
    "CleanTemplate",
    "CleanTask",
    "OperatorInstance",
    "CleanResult",
    # Collection 模块
    "TaskExecution",
    "CollectionTask",
    "TaskLog",
    "DataxTemplate",
    # Common 模块
    "ChunkUploadRequest",
    # Operator 模块
    "Operator",
    "OperatorCategory",
    "OperatorCategoryRelation"
]