# DataMate All-in-One Data Work Platform

<div align="center">

[![Backend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-backend.yml)
[![Frontend CI](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml/badge.svg)](https://github.com/ModelEngine-Group/DataMate/actions/workflows/docker-image-frontend.yml)
![GitHub Stars](https://img.shields.io/github/stars/ModelEngine-Group/DataMate)
![GitHub Forks](https://img.shields.io/github/forks/ModelEngine-Group/DataMate)
![GitHub Issues](https://img.shields.io/github/issues/ModelEngine-Group/DataMate)
![GitHub License](https://img.shields.io/github/license/ModelEngine-Group/DataMate)

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

### Clone the Code

```bash
git clone git@github.com:ModelEngine-Group/DataMate.git
cd DataMate
```

### Build Images

```bash
make build
```

### Docker Installation

```bash
make install INSTALLER=docker
```

### Kubernetes Installation

```bash
make install INSTALLER=k8s
```

## 🤝 Contribution Guidelines

Thank you for your interest in this project! We warmly welcome contributions from the community. Whether it's submitting
bug reports, suggesting new features, or directly participating in code development, all forms of help make the project
better.

• 📮 [GitHub Issues](../../issues): Submit bugs or feature suggestions.

• 🔧 [GitHub Pull Requests](../../pulls): Contribute code improvements.

## 📄 License

DataMate is open source under the [MIT](LICENSE) license. You are free to use, modify, and distribute the code of this
project in compliance with the license terms.
