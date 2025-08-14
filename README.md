# Data-Engine 一站式数据工作平台

> 面向模型微调与RAG检索的企业级数据处理平台，支持数据管理、算子市场、数据清洗、数据合成、数据标注、数据评估等核心功能。

## 🌟 核心特性

- **六大核心模块**：数据管理、算子市场、数据清洗、数据合成、数据标注、数据评估
- **双版本支持**：社区版(CE)和企业版(EE)
- **DDD架构**：领域驱动设计，清晰的分层架构
- **微服务架构**：Spring Boot + 容器化部署
- **可视化编排**：拖拽式数据处理流程设计
- **算子生态**：丰富的内置算子和自定义算子支持

## 🚀 快速开始

### 社区版部署
```bash
cd deployment/docker
docker-compose -f docker-compose.ce.yml up -d
```

### 企业版部署
```bash
cd deployment/kubernetes
kubectl apply -f ../editions/enterprise/k8s/
```

## 📁 项目结构

详见 [代码架构设计](docs/architecture/代码架构设计.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

[Apache License 2.0](LICENSE)
