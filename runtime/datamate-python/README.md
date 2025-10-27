# Label Studio Adapter (DataMate)

这是 DataMate 的 Label Studio Adapter 服务，负责将 DataMate 的项目与 Label Studio 同步并提供对外的 HTTP API（基于 FastAPI）。

## 简要说明

- 框架：FastAPI
- 异步数据库/ORM：SQLAlchemy (async)
- 数据库迁移：Alembic
- 运行器：uvicorn

## 快速开始（开发）

1. 克隆仓库并进入项目目录
2. 创建并激活虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 准备环境变量（示例）

创建 `.env` 并设置必要的变量，例如：

- DATABASE_URL（或根据项目配置使用具体变量）
- LABEL_STUDIO_BASE_URL
- LABEL_STUDIO_USER_TOKEN

（具体变量请参考 `.env.example`）

5. 数据库迁移（开发环境）：

```bash
alembic upgrade head
```

6. 启动开发服务器（示例与常用参数）：

- 本地开发（默认 host/port，自动重载）：

```bash
uvicorn app.main:app --reload
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

## 使用（简要）

- 所有 API 路径以 `/api` 前缀注册（见 `app/main.py` 中 `app.include_router(api_router, prefix="/api")`）。
- 根路径 `/` 返回服务信息和文档链接。

更多细节请查看 `doc/usage.md`（接口使用）和 `doc/development.md`（开发说明）。
