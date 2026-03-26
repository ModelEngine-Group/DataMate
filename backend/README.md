# DataMate Backend

## Overview

DataMate Backend is a microservices architecture based on Spring Boot 3.5 + Java 21, providing core functions such as data management, RAG indexing, and API gateway.

## Architecture

```
backend/
├── api-gateway/          # API Gateway + Authentication
├── services/
│   ├── data-management-service/  # Dataset management
│   ├── rag-indexer-service/      # RAG indexing
│   └── main-application/         # Main application entry
└── shared/
    ├── domain-common/    # DDD building blocks, exception handling
    └── security-common/  # JWT utilities
```

## Services

| Service | Port | Description |
|---------|-------|-------------|
| **main-application** | 8080 | Main application, includes data management, data cleaning, operator marketplace modules |
| **api-gateway** | 8080 | API Gateway, route forwarding and authentication |

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
- **Milvus**: Vector database (RAG indexing)

### Shared Libraries
- **domain-common**: Business exceptions, system parameters, domain entity base classes
- **security-common**: JWT utilities, auth helpers

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
- **AGENTS.md**: See `backend/shared/AGENTS.md` for shared libraries documentation
- **Service Docs**: See individual service READMEs

## Related Links

- [Spring Boot Documentation](https://docs.spring.io/spring-boot/)
- [MyBatis-Plus Documentation](https://baomidou.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
