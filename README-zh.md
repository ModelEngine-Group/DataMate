# DataMate 一站式数据工作平台

<div align="center">

[![Backend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml)
[![Frontend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml)
![GitHub Stars](https://img.shields.io/github/stars/ModelEngine-Group/DataMate)
![GitHub Forks](https://img.shields.io/github/forks/ModelEngine-Group/DataMate)
![GitHub Issues](https://img.shields.io/github/issues/ModelEngine-Group/DataMate)
![GitHub License](https://img.shields.io/github/license/ModelEngine-Group/datamate-docs)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ModelEngine-Group/DataMate)

**DataMate是面向模型微调与RAG检索的企业级数据处理平台，支持数据归集、数据管理、算子市场、数据清洗、数据合成、数据标注、数据评估、知识生成等核心功能。**

[简体中文](./README-zh.md) | [English](./README.md)

如果您喜欢这个项目，希望您能给我们一个Star⭐️!

</div>

## 🌟 核心特性

- **核心模块**：数据归集、数据管理、算子市场、数据清洗、数据合成、数据标注、数据评估、知识生成
- **可视化编排**：拖拽式数据处理流程设计
- **算子生态**：丰富的内置算子和自定义算子支持

## 🚀 快速开始

### 前置条件

- Git (用于拉取源码)
- Make (用于构建和安装)
- Docker (用于构建镜像和部署服务)
- Docker-Compose (用于部署服务-docker方式)
- Kubernetes (用于部署服务-k8s方式)
- Helm (用于部署服务-k8s方式)
- **K8s 部署额外需要**: [Sealed Secrets Controller](https://github.com/bitnami-labs/sealed-secrets)（用于加密管理敏感配置）

### 密钥管理（仅 K8s 部署需要）

DataMate K8s 部署使用 **Bitnami Sealed Secrets** 管理数据库密码、JWT 密钥等敏感信息。所有密钥以加密形式存储在 Git 中（`deployment/kubernetes/sealed-secrets/`），部署时由集群内的 Sealed Secrets Controller 自动解密。

**在线环境安装 Sealed Secrets Controller：**

```bash
# 通过 Helm 安装（推荐）
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system

# 验证安装
kubectl get pods -n kube-system | grep sealed-secrets
```

**离线环境：**

1. 在有网络的机器上下载 Sealed Secrets 镜像：
   ```bash
   # 下载 controller 镜像（约 60MB）
   docker pull bitnami/sealed-secrets-controller:latest
   docker save bitnami/sealed-secrets-controller:latest -o sealed-secrets-controller.tar
   
   # 下载 kubeseal 工具（用于更新密钥）
   # macOS:
   brew install kubeseal
   # Linux:
   wget https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/kubeseal-linux-amd64
   ```

2. 将镜像导入离线环境的镜像仓库，通过 Helm 安装时指定镜像地址。

**更新密钥：**

```bash
# 如果数据库密码等敏感信息发生变更，使用 kubeseal 重新加密
echo -n "new-password" | kubeseal --raw --name datamate-conf --namespace datamate --scope namespace-wide
```

> 注意：Docker 部署方式不需要 Sealed Secrets，密钥统一通过 `.env` 文件管理（已在 `.gitignore` 中排除）。

### Docker一键部署
```shell
wget -qO docker-compose.yml https://raw.githubusercontent.com/ModelEngine-Group/DataMate/refs/heads/main/deployment/docker/datamate/docker-compose.yml \
 && REGISTRY=ghcr.io/modelengine-group/ docker compose up -d
```

### 拉取代码

```bash
git clone git@github.com:ModelEngine-Group/DataMate.git
cd DataMate
```

### 部署基础服务

```bash
make install
```

本项目支持docker-compose和helm两种方式部署，请在执行命令后输入部署方式的对应编号，命令回显如下所示：
```shell
Choose a deployment method:
1. Docker/Docker-Compose
2. Kubernetes/Helm
Enter choice:
```

若您使用的机器没有make，您也可以执行如下命令部署:
```bash
REGISTRY=ghcr.io/modelengine-group/ docker compose -f deployment/docker/datamate/docker-compose.yml --profile milvus up -d
```

当容器运行后，请在浏览器打开 http://localhost:30000 查看前端界面。

要查看所有可用的 Make 目标、选项和帮助信息，请运行：

```bash
make help
```

如果您是离线环境，您可以执行如下命令下载所有依赖的镜像:
```bash
make download
```

### 部署Label Studio作为标注工具
```bash
make install-label-studio
```

### 构建并部署Mineru增强pdf处理
```bash
make build-mineru
make install-mineru
```

### 部署DeerFlow服务
```bash
make install-deer-flow
```

### 本地开发部署
本地代码修改后，请执行以下命令构建镜像并使用本地镜像部署
```bash
make build
make install dev=true
```

### 卸载服务
```bash
make uninstall
```

在运行 `make uninstall` 时，卸载流程会只询问一次是否删除卷（数据），该选择会应用到所有组件。卸载顺序为：milvus -> label-studio -> datamate，确保在移除 datamate 网络前，所有使用该网络的服务已先停止。

## 📚 文档

### 核心文档
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - 本地开发环境搭建和工作流程
- **[AGENTS.md](./AGENTS.md)** - AI 助手指南和代码规范

### 后端文档
- **[backend/README-zh.md](./backend/README-zh.md)** - 后端架构、服务和技术栈
- **[backend/api-gateway/README-zh.md](./backend/api-gateway/README-zh.md)** - API Gateway 配置和路由
- **[backend/services/main-application/README-zh.md](./backend/services/main-application/README-zh.md)** - 主应用模块
- **[backend/shared/README-zh.md](./backend/shared/README-zh.md)** - 共享库（domain-common, security-common）

### 运行时文档
- **[runtime/README-zh.md](./runtime/README-zh.md)** - 运行时架构和组件
- **[runtime/datamate-python/README-zh.md](./runtime/datamate-python/README-zh.md)** - FastAPI 后端服务
- **[runtime/python-executor/README-zh.md](./runtime/python-executor/README-zh.md)** - Ray 执行器框架
- **[runtime/ops/README.md](./runtime/ops/README.md)** - 算子生态
- **[runtime/datax/README-zh.md](./runtime/datax/README-zh.md)** - DataX 数据框架
- **[runtime/deer-flow/README-zh.md](./runtime/deer-flow/README-zh.md)** - DeerFlow LLM 服务

### 前端文档
- **[frontend/README-zh.md](./frontend/README-zh.md)** - React 前端应用

## 🤝 贡献指南

感谢您对本项目的关注！我们非常欢迎社区的贡献，无论是提交 Bug 报告、提出功能建议，还是直接参与代码开发，都能帮助项目变得更好。

• 📮 [GitHub Issues](../../issues)：提交 Bug 或功能建议。

• 🔧 [GitHub Pull Requests](../../pulls)：贡献代码改进。

## 📄 许可证

DataMate 基于 [MIT](LICENSE) 开源，您可以在遵守许可证条款的前提下自由使用、修改和分发本项目的代码。
