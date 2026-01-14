# DataMate 一站式数据工作平台

<div align="center">

[![Backend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml)
[![Frontend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml)
![GitHub Stars](https://img.shields.io/github/stars/ModelEngine-Group/DataMate)
![GitHub Forks](https://img.shields.io/github/forks/ModelEngine-Group/DataMate)
![GitHub Issues](https://img.shields.io/github/issues/ModelEngine-Group/DataMate)
![GitHub License](https://img.shields.io/github/license/ModelEngine-Group/datamate-docs)

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
- kubernetes (用于部署服务-k8s方式)
- Helm (用于部署服务-k8s方式)

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

## 🤝 贡献指南

感谢您对本项目的关注！我们非常欢迎社区的贡献，无论是提交 Bug 报告、提出功能建议，还是直接参与代码开发，都能帮助项目变得更好。

• 📮 [GitHub Issues](../../issues)：提交 Bug 或功能建议。

• 🔧 [GitHub Pull Requests](../../pulls)：贡献代码改进。

## 📄 许可证

DataMate 基于 [MIT](LICENSE) 开源，您可以在遵守许可证条款的前提下自由使用、修改和分发本项目的代码。
