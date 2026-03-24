# DataMate Backend

## Overview

DataMate Backend 是基于 Spring Boot 3.5 + Java 21 的微服务架构，提供数据管理、RAG 索引、API 网关等核心功能。

## Architecture

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

## Services

| Service | Port | Description |
|---------|-------|-------------|
| **main-application** | 8080 | 主应用，包含数据管理、数据清洗、算子市场等模块 |
| **api-gateway** | 8080 | API Gateway，路由转发和认证 |

## Technology Stack

- **Framework**: Spring Boot 3.5.6, Spring Cloud 2025.0.0
- **Language**: Java 21
- **Database**: PostgreSQL 8.0.33 + MyBatis-Plus 3.5.14
- **Cache**: Redis 3.2.0
- **Vector DB**: Milvus (via SDK 2.6.6)
- **Documentation**: SpringDoc OpenAPI 2.2.0
- **Build**: Maven

## Dependencies

### External Services
- **PostgreSQL**: `datamate-database:5432`
- **Redis**: `datamate-redis:6379`
- **Milvus**: 向量数据库（RAG 索引）

### Shared Libraries
- **domain-common**: 业务异常、系统参数、领域实体基类
- **security-common**: JWT 工具、认证辅助

## Quick Start

### Prerequisites
- JDK 21+
- Maven 3.8+
- PostgreSQL 12+
- Redis 6+

### Build
```bash
cd backend
mvn clean install
```

### Run Main Application
```bash
cd backend/services/main-application
mvn spring-boot:run
```

### Run API Gateway
```bash
cd backend/api-gateway
mvn spring-boot:run
```

## Development

### Module Structure (DDD)
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

### Code Conventions
- **Entities**: Extend `BaseEntity<ID>`, use `@TableName("t_*")`
- **Controllers**: `@RestController` + `@RequiredArgsConstructor`
- **Services**: `@Service` + `@Transactional`
- **Error Handling**: `throw BusinessException.of(ErrorCode.XXX)`
- **MapStruct**: `@Mapper(componentModel = "spring")`

## Testing

```bash
# Run all tests
mvn test

# Run specific test
mvn test -Dtest=ClassName#methodName

# Run specific module tests
mvn -pl services/data-management-service -am test
```

## Configuration

### Environment Variables
- `DB_USERNAME`: Database username
- `DB_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `JWT_SECRET`: JWT secret key

### Profiles
- `application.yml`: Default configuration
- `application-dev.yml`: Development overrides

## Documentation

- **API Docs**: http://localhost:8080/api/swagger-ui.html
- **AGENTS.md**: See `backend/shared/AGENTS.md` for shared libraries
- **Service Docs**: See individual service READMEs

## Related Links

- [Spring Boot Documentation](https://docs.spring.io/spring-boot/)
- [MyBatis-Plus Documentation](https://baomidou.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
