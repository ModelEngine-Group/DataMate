# Operator Market Service - Python Implementation

## 概述

这是 `operator-market-service` 的 Python 实现，已集成到 `runtime/datamate-python` 项目中。

## 功能

- **算子管理**：创建、查询、更新、删除算子
- **分类管理**：树状分类结构查询
- **文件上传**：支持算子文件上传和解析（支持 tar/zip 格式）
- **MCP 工具集成**：通过 fastapi-mcp 提供 MCP 工具接口

## 目录结构

```
app/module/operator_market/
├── __init__.py              # 模块入口
├── constants.py              # 常量定义
├── exceptions.py             # 异常定义
├── schema/                  # Pydantic Schema 定义
│   ├── __init__.py
│   ├── operator.py          # 算子相关 Schema
│   ├── category.py          # 分类相关 Schema
│   └── release.py          # 发布版本 Schema
├── parsers/                 # 文件解析器
│   ├── __init__.py
│   ├── abstract_parser.py   # 抽象解析器基类
│   ├── tar_parser.py       # TAR 文件解析器
│   ├── zip_parser.py       # ZIP 文件解析器
│   └── parser_holder.py    # 解析器持有者
├── repository/              # 数据访问层
│   ├── __init__.py
│   ├── operator_repository.py
│   ├── category_repository.py
│   ├── category_relation_repository.py
│   └── operator_release_repository.py
├── service/                 # 服务层
│   ├── __init__.py
│   ├── operator_service.py
│   └── category_service.py
└── interface/               # API 接口层
    ├── __init__.py
    ├── operator_routes.py
    └── category_routes.py
```

## API 端点

### 算子相关 (`/api/operator-market/operators`)

| 方法 | 路径 | 描述 |
|------|--------|------|
| POST | `/list` | 查询算子列表（支持分页、分类过滤、关键词搜索） |
| GET | `/{operator_id}` | 获取算子详情 |
| PUT | `/{operator_id}` | 更新算子信息 |
| POST | `/create` | 创建新算子 |
| POST | `/upload` | 上传算子文件 |
| POST | `/upload/pre-upload` | 预上传（获取请求 ID） |
| POST | `/upload/chunk` | 分块上传 |
| DELETE | `/{operator_id}` | 删除算子 |
| GET | `/examples/download` | 下载示例算子 |

### 分类相关 (`/api/operator-market/categories`)

| 方法 | 路径 | 描述 |
|------|--------|------|
| GET | `/tree` | 获取分类树状结构 |

## 数据库表

- `t_operator` - 算子表
- `t_operator_category` - 分类表
- `t_operator_category_relation` - 分类关系表
- `t_operator_release` - 算子发布版本表
- `v_operator` - 算子视图（包含分类信息）

## 文件格式支持

算子文件需包含 `metadata.yml` 文件，格式如下：

```yaml
raw_id: "operator-id"
name: "算子名称"
description: "算子描述"
version: "1.0.0"
language: "python"  # python, java
modal: "text"       # text, image, audio, video
vendor: "datamate"   # datamate, data-juicer, or other
inputs: {...}
outputs: {...}
runtime: {...}
settings: {...}
metrics: {...}
release:
  - "更新日志1"
  - "更新日志2"
```

## 待实现功能

- [ ] 算子收藏功能完善
- [ ] 标签过滤功能

## 使用示例

### 查询算子列表

```bash
curl -X POST "http://localhost:18000/api/operator-market/operators/list" \
  -H "Content-Type: application/json" \
  -d '{
    "page": 1,
    "size": 10,
    "keyword": "test",
    "isStar": false
  }'
```

### 获取分类树

```bash
curl -X GET "http://localhost:18000/api/operator-market/categories/tree"
```

### 创建算子

```bash
curl -X POST "http://localhost:18000/api/operator-market/operators/create" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new-operator-id",
    "name": "新算子",
    "description": "这是一个新算子",
    "version": "1.0.0",
    "fileName": "operator.tar"
  }'
```
