# DataMate Runtime

## Overview

DataMate Runtime 提供数据处理、算子执行、数据收集等核心功能，基于 Python 3.12+ 和 FastAPI 框架。

## Architecture

```
runtime/
├── datamate-python/      # FastAPI 后端服务（port 18000）
├── python-executor/      # Ray 分布式执行器
├── ops/                 # 算子生态
├── datax/               # DataX 数据读写框架
└── deer-flow/            # DeerFlow 服务
```

## Components

### 1. datamate-python (FastAPI Backend)
**Port**: 18000

核心 Python 服务，提供以下功能：
- **数据合成**: QA 生成、文档处理
- **数据标注**: Label Studio 集成、自动标注
- **数据评估**: 模型评估、质量检查
- **数据清洗**: 数据清洗管道
- **算子市场**: 算子管理、上传
- **RAG 索引**: 向量索引、知识库管理
- **数据收集**: 定时任务、数据源集成

**Technology Stack**:
- FastAPI 0.124+
- SQLAlchemy 2.0+ (async)
- Pydantic 2.12+
- PostgreSQL (via asyncpg)
- Milvus (via pymilvus)
- APScheduler (定时任务)

### 2. python-executor (Ray Executor)
Ray 分布式执行框架，负责：
- **算子执行**: 执行数据处理算子
- **任务调度**: 异步任务管理
- **分布式计算**: 多节点并行处理

**Technology Stack**:
- Ray 2.7.0
- FastAPI (执行器 API)
- Data-Juicer (数据处理)

### 3. ops (Operator Ecosystem)
算子生态，包含：
- **filter**: 数据过滤（去重、敏感内容、质量过滤）
- **mapper**: 数据转换（清洗、归一化）
- **slicer**: 数据切片（文本分割、幻灯片提取）
- **formatter**: 格式转换（PDF → text, slide → JSON）
- **llms**: LLM 算子（质量评估、条件检查）
- **annotation**: 标注算子（目标检测、分割）

**See**: `runtime/ops/README.md` for operator development guide.

### 4. datax (DataX Framework)
DataX 数据读写框架，支持多种数据源：
- **Readers**: MySQL, PostgreSQL, Oracle, MongoDB, Elasticsearch, HDFS, S3, NFS, GlusterFS, API, 等
- **Writers**: 同上，支持写入目标

**Technology Stack**: Java (Maven 构建)

### 5. deer-flow (DeerFlow Service)
DeerFlowService（配置见 `conf.yaml`）。

## Quick Start

### Prerequisites
- Python 3.12+
- Poetry (for datamate-python)
- Ray 2.7.0+ (for python-executor)

### Run datamate-python
```bash
cd runtime/datamate-python
poetry install
poetry run uvicorn app.main:app --reload --port 18000
```

### Run python-executor
```bash
cd runtime/python-executor
poetry install
ray start --head
```

## Development

### datamate-python Module Structure
```
app/
├── core/              # Logging, exception, config
├── db/
│   ├── models/        # SQLAlchemy models
│   └── session.py     # Async session
├── module/
│   ├── annotation/    # Label Studio integration
│   ├── collection/    # Data collection
│   ├── cleaning/      # Data cleaning
│   ├── dataset/       # Dataset management
│   ├── evaluation/    # Model evaluation
│   ├── generation/    # QA synthesis
│   ├── operator/      # Operator marketplace
│   ├── rag/           # RAG indexing
│   └── shared/        # Shared schemas
└── main.py            # FastAPI entry
```

### Code Conventions
- **Routes**: `APIRouter` in `interface/*.py`
- **DI**: `Depends(get_db)` for session
- **Error**: `raise BusinessError(ErrorCodes.XXX, context)`
- **Transaction**: `async with transaction(db):`
- **Models**: Extend `BaseEntity` (audit fields auto-filled)

## Testing

```bash
cd runtime/datamate-python
poetry run pytest
```

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `LABEL_STUDIO_BASE_URL`: Label Studio URL
- `RAY_ENABLED`: Enable Ray executor
- `RAY_ADDRESS`: Ray cluster address

## Documentation

- **API Docs**: http://localhost:18000/redoc
- **AGENTS.md**: See `runtime/datamate-python/app/AGENTS.md` for detailed module docs
- **Operator Guide**: See `runtime/ops/README.md` for operator development

## Related Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ray Documentation](https://docs.ray.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
