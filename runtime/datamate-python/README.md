# DataMate Python Service (DataMate)

这是 DataMate 的 Python 服务，负责DataMate的数据合成、数据标注、数据评估等功能。

## 简要说明

- 框架：FastAPI
- 异步数据库/ORM：SQLAlchemy (async)
- 数据库迁移：Alembic
- 运行器：uvicorn

## 快速开始（开发）

### 前置条件

- Python 3.11+
- poetry 包管理器

1. 克隆仓库
```bash
git clone git@github.com:ModelEngine-Group/DataMate.git
```
2. 进入项目目录
```bash
cd runtime/datamate-python
```

3. 安装依赖
由于项目使用poetry管理依赖，你可以使用以下命令安装：：
```bash
poetry install
```
或者直接使用pip安装（如果poetry不可用）：

```bash
pip install -e .
```

4. 配置环境变量
复制环境变量示例文件并配置：

```bash
cp .env.example .env
```
编辑.env文件，设置必要的环境变量，如数据库连接、Label Studio配置等。

5. 数据库迁移（开发环境）：

```bash
alembic upgrade head
```

6. 启动开发服务器（示例与常用参数）：

- 本地开发（默认 host/port，自动重载）：

```bash
set -a && source .env && set +a && poetry run uvicorn app.main:app --port 18000 --log-level debug --reload
```
或者
```bash
poetry run python -m app.main
```

- 指定主机与端口并打开调试日志：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

- 在生产环境使用多个 worker（不使用 --reload）：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info --proxy-headers
```

- 使用环境变量启动（示例）：

```bash
HOST=0.0.0.0 PORT=8000 uvicorn app.main:app --reload
```

注意：

- `--reload` 仅用于开发，会监视文件变化并重启进程；不要在生产中使用。
- `--workers` 提供并发处理能力，但会增加内存占用；生产时通常配合进程管理或容器编排（Kubernetes）使用。
- 若需要完整的生产部署建议使用 ASGI 服务器（如 gunicorn + uvicorn workers / 或直接使用 uvicorn 在容器中配合进程管理）。

访问 API 文档：

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc （推荐使用）

## 开发新功能
- 安装开发依赖：

```bash
poetry  add xxx
```


## 使用（简要）

- 所有 API 路径以 `/api` 前缀注册（见 `app/main.py` 中 `app.include_router(api_router, prefix="/api")`）。
- 根路径 `/` 返回服务信息和文档链接。

更多细节请查看 `doc/usage.md`（接口使用）和 `doc/development.md`（开发说明）。
