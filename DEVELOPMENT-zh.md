# 开发指南

本文档为 DataMate 提供全面的本地开发环境搭建和工作流程指南，涵盖 Java、Python、React 三种语言。

## 概述

DataMate 是由多语言（Java 后端、Python 运行时、React 前端）组成的微服务项目，通过 Docker Compose 进行本地开发协调。

## 前置条件

- Git (用于拉取源码)
- Make (用于构建和安装)
- Docker (用于构建镜像和部署服务)
- Docker Compose (用于部署服务 - docker 方式)
- Kubernetes (用于部署服务 - k8s 方式)
- Helm (用于部署服务 - k8s 方式)

注意：
- 确保 Java 和 Python 环境在系统 PATH 中（如适用）
- Docker Compose 将编排本地开发栈

## 快速开始

### 1. 克隆仓库并安装依赖
```bash
git clone git@github.com:ModelEngine-Group/DataMate.git
cd DataMate
```

### 2. 启动基础服务
```bash
make install
```

本项目支持 docker-compose 和 helm 两种方式部署，请在执行命令后输入部署部署方式的对应编号，命令回显如下所示：
```shell
Choose a deployment method:
1. Docker/Docker-Compose
2. Kubernetes/Helm
Enter choice:
```

若您使用的机器没有 make，您也可以执行如下命令部署：
```bash
REGISTRY=ghcr.io/modelengine-group/ docker compose -f deployment/docker/datamate/docker-compose.yml --profile milvus up -d
```

当容器运行后，请在浏览器打开 http://localhost:30000 查看前端界面。

### 3. 本地开发部署
本地代码修改后，请执行以下命令构建镜像并使用本地镜像部署：
```bash
make build
make install dev=true
```

### 4. 卸载服务
```bash
make uninstall
```

在运行 `make uninstall` 时，卸载流程会只询问一次是否删除卷（数据），该选择会应用到所有组件。卸载顺序为：milvus -> label-studio -> datamate，确保在移除 datamate 网络前，所有使用该网络的服务已先停止。

## 项目结构

```
DataMate/
├── backend/              # Java 后端
│   ├── api-gateway/     # API Gateway
│   ├── services/          # 核心服务
│   └── shared/            # 共享库
├── runtime/              # Python 运行时
│   ├── datamate-python/   # FastAPI 后端
│   ├── python-executor/   # Ray 执行器
│   ├── ops/               # 算子生态
│   ├── datax/             # DataX 框架
│   └── deer-flow          # DeerFlow 服务
├── frontend/             # React 前端
├── deployment/           # 部署配置
└── docs/                # 文档
```

## 开发工作流程

### Java 后端开发
```bash
# 构建
cd backend
mvn clean install

# 运行测试
mvn test

# 运行特定服务
cd backend/services/main-application
mvn spring-boot:run
```

### Python 运行时开发
```bash
# 安装依赖
cd runtime/datamate-python
poetry install

# 运行服务
poetry run uvicorn app.main:app --reload --port 18000

# 运行测试
poetry run pytest
```

### React 前端开发
```bash
# 安装依赖
cd frontend
npm ci

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build
```

### Docker Compose 开发
```bash
# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f [service-name]

# 停止所有服务
docker compose down
```

## 环境配置

每个组件可以有自己的环境变量文件。不要提交包含密钥的 .env 文件。

### 后端（Java）
- **路径**: `backend/.env`
- **典型密钥**:
  - `DB_URL`: 数据库连接字符串
  - `DB_USER`: 数据库用户名
  - `DB_PASSWORD`: 数据库密码
  - `REDIS_URL`: Redis 连接字符串
  - `REDIS_PASSWORD`: Redis 密码
  - `JWT_SECRET`: JWT 密钥

### 运行时（Python）
- **路径**: `runtime/datamate-python/.env`
- **典型密钥**:
  - `DATABASE_URL`: PostgreSQL 连接字符串
  - `RAY_ENABLED`: 是否启用 Ray 执行器
  - `RAY_ADDRESS`: Ray 集群地址
  - `LABEL_STUDIO_BASE_URL`: Label Studio 基础 URL

### 前端（React）
- **路径**: `frontend/.env`
- **典型密钥**:
  - `VITE_API_BASE_URL`: API 基础 URL
  - `VITE_RUNTIME_API_URL`: 运行时 API 基础 URL

## 测试

### Java（JUnit 5）
```bash
cd backend
mvn test
```

### Python（pytest）
```bash
cd runtime/datamate-python
poetry run pytest
```

### 前端
当前未配置测试框架。

## 调试

### Java 后端
```bash
# 启用 JDWP 调试端口 5005
export JAVA_TOOL_OPTIONS='-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005'
java -jar backend/main-application/target/*.jar
```

### Python 运行时
```bash
# 启用 debugpy 监听端口 5678
cd runtime/datamate-python
python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app --reload --port 18000 --host 0.0.0.0
```

### React 前端
使用浏览器开发者工具或 VS Code 调试器。

## 常见问题

### 端口冲突
检查哪个进程正在使用端口：
```bash
lsof -i TCP:8080
lsof -i TCP:18000
lsof -i TCP:5173
```
停止或重新配置冲突的服务。

### 数据库连接失败
确保 `.env` 包含正确的 `DATABASE_URL` 和凭据；确保数据库服务在 Docker Compose 中已启动。

### Ray 集群问题
确保 Ray 已正确启动；检查 Ray 工作进程日志；确保 `RAY_ADDRESS` 配置正确。

## 文档

- **核心文档**:
  - [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构、微服务通信、数据流
  - [DEVELOPMENT.md](./DEVELOPMENT.md) - 本地开发环境搭建和工作流程
  - [AGENTS.md](./AGENTS.md) - AI 助手指南和代码规范

- **后端文档**:
  - [backend/README.md](./backend/README.md) - 后端架构、服务和技术栈
  - [backend/api-gateway/README.md](./backend/api-gateway/README.md) - API Gateway 配置和路由
  - [backend/services/main-application/README.md](./backend/services/main-application/README.md) - 主应用模块
  - [backend/shared/README.md](./backend/shared/README.md) - 共享库（domain-common, security-common）

- **运行时文档**:
  - [runtime/README.md](./runtime/README.md) - 运行时架构和组件
  - [runtime/datamate-python/README.md](./runtime/datamate-python/README.md) - FastAPI 后端服务
  - [runtime/python-executor/README.md](./runtime/python-executor/README.md) - Ray 执行器框架
  - [runtime/ops/README.md](./runtime/ops/README.md) - 算子生态
  - [runtime/datax/README.md](./runtime/datax/README.md) - DataX 数据框架
  - [runtime/deer-flow/README.md](./runtime/deer-flow/README.md) - DeerFlow LLM 服务

- **前端文档**:
  - [frontend/README.md](./frontend/README.md) - React 前端应用

## 贡献指南

感谢您对本项目的关注！我们非常欢迎社区的贡献，无论是提交 Bug 报告、提出功能建议，还是直接参与代码开发，都能帮助项目变得更好。

• 📮 [GitHub Issues](../../issues)：提交 Bug 或功能建议。
• 🔧 [GitHub Pull Requests](../../pulls)：贡献代码改进。

## 许可证

DataMate 基于 [MIT](LICENSE) 开源，您可以在遵守许可证条款的前提下自由使用、修改和分发本项目的代码。
