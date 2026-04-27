# DataMate 运行时

## 概述

DataMate 运行时提供数据处理、算子执行、数据收集等核心功能，基于 Python 3.12+ 和 FastAPI 框架。

## 架构

```
runtime/
├── datamate-python/      # FastAPI 后端服务（端口 18000）
├── python-executor/      # Ray 分布式执行器
├── ops/                 # 算子生态
├── datax/               # DataX 数据读写框架
└── deer-flow/            # DeerFlow 服务
```

## 组件

### 1. datamate-python (FastAPI 后端)
**端口**: 18000

核心 Python 服务，提供以下功能：
- **数据合成**: QA 生成、文档处理
- **数据标注**: Label Studio 集成、自动标注
- **数据评估**: 模型评估、质量检查
- **数据清洗**: 数据清洗管道
- **算子市场**: 算子管理、上传
- **RAG 索引**: 向量索引、知识库管理
- **数据收集**: 定时任务、数据源集成

**技术栈**:
- FastAPI 0.124+
- SQLAlchemy 2.0+ (async)
- Pydantic 2.12+
- PostgreSQL (via asyncpg)
- Milvus (via pymilvus)
- APScheduler (定时任务)

### 2. python-executor (Ray 执行器)
Ray 分布式执行框架，负责：
- **算子执行**: 执行数据处理算子
- **任务调度**: 异步任务管理
- **分布式计算**: 多节点并行处理

**技术栈**:
- Ray 2.7.0
- FastAPI (执行器 API)
- Data-Juicer (数据处理)

### 3. ops (算子生态)
算子生态，包含：
- **filter**: 数据过滤（去重、敏感内容、质量过滤）
- **mapper**: 数据转换（清洗、归一化）
- **slicer**: 数据切片（文本分割、幻灯片提取）
- **formatter**: 格式转换（PDF → text, slide → JSON）
- **llms**: LLM 算子（质量评估、条件检查）
- **annotation**: 标注算子（目标检测、分割）

**见**: `runtime/ops/README.md` 获取算子开发指南

### 4. datax (DataX 框架)
DataX 数据读写框架，支持多种数据源：
- **Readers**: MySQL, PostgreSQL, Oracle, MongoDB, Elasticsearch, HDFS, S3, NFS, GlusterFS, API, 等
- **Writers**: 同上，支持写入目标

**技术栈**: Java (Maven 构建)

### 5. deer-flow (DeerFlow 服务)
DeerFlow 服务（配置见 `conf.yaml`）。

## 快速开始

### 前置条件
- Python 3.12+
- Poetry (for datamate-python)
- Ray 2.7.0+ (for python-executor)

### 运行 datamate-python
```bash
cd runtime/datamate-python
poetry install
poetry run uvicorn app.main:app --reload --port 18000
```

### 运行 python-executor
```bash
cd runtime/python-executor
poetry install
ray start --head
```

## 开发

### datamate-python 模块结构
```
app/
├── core/              # 日志、异常、配置
├── db/
│   ├── models/        # SQLAlchemy 模型
│   └── session.py     # 异步会话
├── module/
│   ├── annotation/    # Label Studio 集成
│   ├── collection/    # 数据收集
│   ├── cleaning/      # 数据清洗
│   ├── dataset/       # 数据集管理
│   ├── evaluation/    # 模型评估
│   ├── generation/    # QA 合成
│   ├── operator/      # 算子市场
│   ├── rag/           # RAG 索引
│   └── shared/        # 共享 schemas
└── main.py            # FastAPI 入口
```

### 代码约定
- **路由**: `APIRouter` 在 `interface/*.py`
- **依赖注入**: `Depends(get_db)` 获取会话
- **错误**: `raise BusinessError(ErrorCode.XXX, context)`
- **事务**: `async with transaction(db):`
- **模型**: Extend `BaseEntity` (审计字段自动填充)

## 测试

```bash
cd runtime/datamate-python
poetry run pytest
```

## 配置

### 环境变量
- `DATABASE_URL`: PostgreSQL 连接字符串
- `LABEL_STUDIO_BASE_URL`: Label Studio URL
- `RAY_ENABLED`: 启用 Ray 执行器
- `RAY_ADDRESS`: Ray 集群地址

## 文档

- **API 文档**: http://localhost:18000/redoc
- **算子指南**: 见 `runtime/ops/README.md` 获取算子开发

## 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Ray 文档](https://docs.ray.io/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
