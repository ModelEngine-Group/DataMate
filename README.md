# DataMate All-in-One Data Work Platform

<div align="center">

[![Backend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml)
[![Frontend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml)
![GitHub Stars](https://img.shields.io/github/stars/ModelEngine-Group/DataMate)
![GitHub Forks](https://img.shields.io/github/forks/ModelEngine-Group/DataMate)
![GitHub Issues](https://img.shields.io/github/issues/ModelEngine-Group/DataMate)
![GitHub License](https://img.shields.io/github/license/ModelEngine-Group/datamate-docs)

**DataMate is an enterprise-level data processing platform for model fine-tuning and RAG retrieval, supporting core
functions such as data collection, data management, operator marketplace, data cleaning, data synthesis, data
annotation, data evaluation, and knowledge generation.**

[简体中文](./README-zh.md) | [English](./README.md)

If you like this project, please give it a Star⭐️!

</div>

## 🌟 Core Features

- **Core Modules**: Data Collection, Data Management, Operator Marketplace, Data Cleaning, Data Synthesis, Data
  Annotation, Data Evaluation, Knowledge Generation.
- **Visual Orchestration**: Drag-and-drop data processing workflow design.
- **Operator Ecosystem**: Rich built-in operators and support for custom operators.

## 🚀 Quick Start

### Prerequisites

- Git (for pulling source code)
- Make (for building and installing)
- Docker (for building images and deploying services)
- Docker-Compose (for service deployment - Docker method)
- Kubernetes (for service deployment - k8s method)
- Helm (for service deployment - k8s method)

This project supports deployment via two methods: docker-compose and helm. After executing the command, please enter the corresponding number for the deployment method. The command echo is as follows:
```shell
Choose a deployment method:
1. Docker/Docker-Compose
2. Kubernetes/Helm
Enter choice:
```

### Clone the Code

```bash
git clone git@github.com:ModelEngine-Group/DataMate.git
cd DataMate
```

### Deploy the basic services

```bash
make install
```

If the machine you are using does not have make installed, please run the following command to deploy it:
```bash
# Windows
set REGISTRY=ghcr.io/modelengine-group/
docker compose -f ./deployment/docker/datamate/docker-compose.yml up -d
docker compose -f ./deployment/docker/milvus/docker-compose.yml up -d

# Linux/Mac
export REGISTRY=ghcr.io/modelengine-group/
docker compose -f ./deployment/docker/datamate/docker-compose.yml up -d
docker compose -f ./deployment/docker/milvus/docker-compose.yml up -d
```

Once the container is running, access http://localhost:30000 in a browser to view the front-end interface.

To list all available Make targets, flags and help text, run:

```bash
make help
```

### Build and deploy Mineru Enhanced PDF Processing
```bash
make build-mineru
make install-mineru
```

### Deploy the DeerFlow service
```bash
make install-deer-flow
```

### Local Development and Deployment
After modifying the local code, please execute the following commands to build the image and deploy using the local image.
```bash
make build
make install dev=true
```

### Uninstall
```bash
make uninstall
```

When running make uninstall, the installer will prompt once whether to delete volumes; that single choice is applied to all components. The uninstall order is: milvus -> label-studio -> datamate, which ensures the datamate network is removed cleanly after services that use it have stopped.

## 🤝 Contribution Guidelines

Thank you for your interest in this project! We warmly welcome contributions from the community. Whether it's submitting
bug reports, suggesting new features, or directly participating in code development, all forms of help make the project
better.

• 📮 [GitHub Issues](../../issues): Submit bugs or feature suggestions.

• 🔧 [GitHub Pull Requests](../../pulls): Contribute code improvements.

## 📄 License

DataMate is open source under the [MIT](LICENSE) license. You are free to use, modify, and distribute the code of this
project in compliance with the license terms.
