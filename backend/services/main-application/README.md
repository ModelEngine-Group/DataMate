# Main Application

## Overview

The Main Application is DataMate's core Spring Boot service, containing major functional modules including data management, data cleaning, operator marketplace, and data collection.

## Architecture

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
    ├── application.yml                # Main configuration
    ├── config/application-datamanagement.yml  # Data management config
    └── config/application-datacollection.yml   # Data collection config
```

## Modules

### 1. Data Management
- Dataset CRUD operations
- File upload/download
- Tag management
- Dataset versioning

### 2. Data Collection
- Data source configuration
- Scheduled data collection tasks
- Data synchronization
- Data import/export

## Configuration

### Port
- **Default**: 8080
- **Context Path**: `/api`

### Key Configuration
```yaml
server:
  port: 8080
  servlet:
    context-path: /api

datamate:
  data-management:
    base-path: /dataset
```

## Quick Start

### Prerequisites
- JDK 21+
- Maven 3.8+
- PostgreSQL 12+
- Redis 6+

### Build
```bash
cd backend/services/main-application
mvn clean install
```

### Run
```bash
cd backend/services/main-application
mvn spring-boot:run
```

## Development

### Adding a New Module
1. Create entity class in `domain/model/`
2. Create repository interface in `domain/repository/`
3. Implement repository in `infrastructure/persistence/`
4. Create application service in `application/`
5. Create controller in `interfaces/rest/`

## Testing

### Run Tests
```bash
cd backend/services/main-application
mvn test
```

### Run Specific Test
```bash
mvn test -Dtest=DatasetControllerTest
```

## Documentation

- **Spring Boot Docs**: https://docs.spring.io/spring-boot/
- [AGENTS.md](../../shared/AGENTS.md)

## Related Links

- [Backend README](../../README.md)
- [API Gateway README](../../api-gateway/README.md)
