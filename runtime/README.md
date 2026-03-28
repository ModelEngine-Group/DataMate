# DataMate Runtime

## Overview

DataMate Runtime provides core functionality for data processing, operator execution, and data collection, built on Python 3.12+ and the FastAPI framework.

## Architecture

```
runtime/
├── datamate-python/      # FastAPI backend service (port 18000)
├── python-executor/      # Ray distributed executor
├── ops/                 # Operator ecosystem
├── datax/               # DataX data read/write framework
└── deer-flow/            # DeerFlow service
```

## Components

### 1. datamate-python (FastAPI Backend)
**Port**: 18000

Core Python service providing:
- **Data Synthesis**: QA generation, document processing
- **Data Annotation**: Label Studio integration, auto-annotation
- **Data Evaluation**: Model evaluation, quality checks
- **Data Cleaning**: Data cleaning pipelines
- **Operator Marketplace**: Operator management, upload
- **RAG Indexing**: Vector indexing, knowledge base management
- **Data Collection**: Scheduled tasks, data source integration

**Technology Stack**:
- FastAPI 0.124+
- SQLAlchemy 2.0+ (async)
- Pydantic 2.12+
- PostgreSQL (via asyncpg)
- Milvus (via pymilvus)
- APScheduler (scheduled tasks)

### 2. python-executor (Ray Executor)
Ray distributed execution framework responsible for:
- **Operator Execution**: Execute data processing operators
- **Task Scheduling**: Async task management
- **Distributed Computing**: Multi-node parallel processing

**Technology Stack**:
- Ray 2.7.0
- FastAPI (executor API)
- Data-Juicer (data processing)

### 3. ops (Operator Ecosystem)
Operator ecosystem including:
- **filter**: Data filtering (deduplication, sensitive content, quality filtering)
- **mapper**: Data transformation (cleaning, normalization)
- **slicer**: Data slicing (text splitting, slide extraction)
- **formatter**: Format conversion (PDF → text, slide → JSON)
- **llms**: LLM operators (quality evaluation, condition checking)
- **annotation**: Annotation operators (object detection, segmentation)

**See**: `runtime/ops/README.md` for operator development guide

### 4. datax (DataX Framework)
DataX data read/write framework supporting multiple data sources:
- **Readers**: MySQL, PostgreSQL, Oracle, MongoDB, Elasticsearch, HDFS, S3, NFS, GlusterFS, API, etc.
- **Writers**: Same as above, supports writing to targets

**Technology Stack**: Java (Maven build)

### 5. deer-flow (DeerFlow Service)
DeerFlow service (see `conf.yaml` for configuration).

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
- **Dependency Injection**: `Depends(get_db)` for session
- **Error Handling**: `raise BusinessError(ErrorCodes.XXX, context)`
- **Transactions**: `async with transaction(db):`
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
- **Operator Guide**: See `runtime/ops/README.md` for operator development

## Related Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ray Documentation](https://docs.ray.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
