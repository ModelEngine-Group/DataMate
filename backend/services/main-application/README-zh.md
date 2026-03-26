# 主应用

## 概述

主应用是 DataMate 的核心 Spring Boot 服务，包含数据管理、数据清洗、算子市场、数据收集等主要功能模块。

## 架构

```
backend/services/main-application/
├── src/main/java/com/datamate/main/
│   ├── interfaces/
│   │   ├── rest/       # Controllers
│   │   ├── dto/        # Request/Response DTOs
│   │   └── converter/   # MapStruct converters
│   ├── application/     # Application services
│   ├── domain/
│   │   ├── model/       # Entities
│   │   └── repository/  # Repository interfaces
│   └── infrastructure/
│       ├── persistence/  # Repository implementations
│       ├── client/       # External API clients
│       └── config/       # Service configuration
└── src/main/resources/
    ├── application.yml                # 主配置
    ├── config/application-datamanagement.yml  # 数据管理配置
    └── config/application-datacollection.yml   # 数据收集配置
```

## 模块

### 1. 数据管理
- 数据集 CRUD 操作
- 文件上传/下载
- 标签管理
- 数据集版本控制

### 2. 数据收集
- 数据源配置
- 定时数据收集任务
- 数据同步
- 数据导入/导出

## 配置

### 端口
- **默认**: 8080
- **上下文路径**: `/api`

### 关键配置
```yaml
server:
  port: 8080
  servlet:
    context-path: /api

datamate:
  data-management:
    base-path: /dataset
```

## 快速开始

### 前置条件
- JDK 21+
- Maven 3.8+
- PostgreSQL 12+
- Redis 6+

### 构建
```bash
cd backend/services/main-application
mvn clean install
```

### 运行
```bash
cd backend/services/main-application
mvn spring-boot:run
```

## 开发

### 添加新模块
1. 在 `domain/model/` 创建实体类
2. 在 `domain/repository/` 创建 repository 接口
3. 在 `infrastructure/persistence/` 实现 repository
4. 在 `application/` 创建 application service
5. 在 `interfaces/rest/` 创建 controller

## 测试

### 运行测试
```bash
cd backend/services/main-application
mvn test
```

### 运行特定测试
```bash
mvn test -Dtest=DatasetControllerTest
```

## 文档

- **Spring Boot 文档**: https://docs.spring.io/spring-boot/
- [AGENTS.md](../../shared/AGENTS.md)

## 相关链接

- [后端 README](../../README.md)
- [API Gateway README](../../api-gateway/README.md)
