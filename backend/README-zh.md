# DataMate 后端

## 概述

DataMate 后端是基于 Spring Boot 3.5 + Java 21 的微服务架构，提供数据管理、RAG 索引、API 网关等核心功能。

## 架构

```
backend/
├── api-gateway/          # API Gateway + 认证
├── services/
│   ├── data-management-service/  # 数据集管理
│   ├── rag-indexer-service/      # RAG 索引
│   └── main-application/         # 主应用入口
└── shared/
    ├── domain-common/    # DDD 构建块、异常处理
    └── security-common/  # JWT 工具
```

## 服务

| 服务 | 端口 | 描述 |
|---------|-------|-------------|
| **main-application** | 8080 | 主应用，包含数据管理、数据清洗、算子市场等模块 |
| **api-gateway** | 8080 | API Gateway，路由转发和认证 |

## 技术栈

- **框架**: Spring Boot 3.5.6, Spring Cloud 2025.0.0
- **语言**: Java 21
- **数据库**: PostgreSQL 8.0.33 + MyBatis-Plus 3.5.14
- **缓存**: Redis 3.2.0
- **向量数据库**: Milvus (via SDK 2.6.6)
- **文档**: SpringDoc OpenAPI 2.2.0
- **构建**: Maven

## 依赖

### 外部服务
- **PostgreSQL**: `datamate-database:5432`
- **Redis**: `datamate-redis:6379`
- **Milvus**: 向量数据库（RAG 索引）

### 共享库
- **domain-common**: 业务异常、系统参数、领域实体基类
- **security-common**: JWT 工具、认证辅助

## 快速开始

### 前置条件
- JDK 21+
- Maven 3.8+
- PostgreSQL 12+
- Redis 6+

### 构建
```bash
cd backend
mvn clean install
```

### 运行主应用
```bash
cd backend/services/main-application
mvn spring-boot:run
```

### 运行 API Gateway
```bash
cd backend/api-gateway
mvn spring-boot:run
```

## 开发

### 模块结构 (DDD)
```
com.datamate.{module}/
├── interfaces/
│   ├── rest/       # Controllers
│   ├── dto/        # Request/Response DTOs
│   ├── converter/   # MapStruct converters
│   └── validation/  # Custom validators
├── application/     # Application services
├── domain/
│   ├── model/       # Entities
│   └── repository/  # Repository interfaces
└── infrastructure/
    ├── persistence/  # Repository implementations
    ├── client/       # External API clients
    └── config/       # Service configuration
```

### 代码约定
- **实体**: Extend `BaseEntity<ID>`, use `@TableName("t_*")`
- **控制器**: `@RestController` + `@RequiredArgsConstructor`
- **服务**: `@Service` + `@Transactional`
- **错误处理**: `throw BusinessException.of(ErrorCode.XXX)`
- **MapStruct**: `@Mapper(componentModel = "spring")`

## 测试

```bash
# 运行所有测试
mvn test

# 运行特定测试
mvn test -Dtest=ClassName#methodName

# 运行特定模块测试
mvn -pl services/data-management-service -am test
```

## 配置

### 环境变量
- `DB_USERNAME`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `REDIS_PASSWORD`: Redis 密码
- `JWT_SECRET`: JWT 密钥

### 配置文件
- `application.yml`: 默认配置
- `application-dev.yml`: 开发环境覆盖

## 文档

- **API 文档**: http://localhost:8080/api/swagger-ui.html
- **AGENTS.md**: 见 `backend/shared/AGENTS.md` 获取共享库文档
- **服务文档**: 见各服务 README

## 相关链接

- [Spring Boot 文档](https://docs.spring.io/spring-boot/)
- [MyBatis-Plus 文档](https://baomidou.com/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
