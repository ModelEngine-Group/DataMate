# API Gateway

## Overview

API Gateway is DataMate's unified entry point, built on Spring Cloud Gateway, responsible for route forwarding, JWT authentication, and rate limiting.

## Architecture

```
backend/api-gateway/
├── src/main/java/com/datamate/gateway/
│   ├── config/         # Gateway configuration
│   ├── filter/         # JWT authentication filter
│   └── route/          # Route definitions
└── src/main/resources/
    └── application.yml   # Gateway configuration
```

## Configuration

### Port
- **Default**: 8080
- **Nacos Discovery Port**: 30000

### Key Configuration
```yaml
spring:
  application:
    name: datamate-gateway
  cloud:
    nacos:
      discovery:
        port: 30000
        server-addr: ${NACOS_ADDR}
        username: consul
        password:
datamate:
  jwt:
    secret: ${JWT_SECRET}
    expiration-seconds: 3600
```

## Features

### 1. Route Forwarding
- Forward frontend requests to corresponding backend services
- Support for load balancing
- Path rewriting

### 2. JWT Authentication
- JWT Token-based authentication
- Token validation and expiration checking
- User context propagation

### 3. Rate Limiting
- Request rate limiting (if configured)
- Prevent API abuse

## Quick Start

### Prerequisites
- JDK 21+
- Maven 3.8+
- Nacos service (if using service discovery)

### Build
```bash
cd backend/api-gateway
mvn clean install
```

### Run
```bash
cd backend/api-gateway
mvn spring-boot:run
```

## Development

### Adding New Routes
Configure route rules in `application.yml` or via Nacos:

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: data-management
          uri: lb://data-management-service
          predicates:
            - Path=/api/data-management/**
          filters:
            - StripPrefix=3
```

### Adding Custom Filters
Create a `GlobalFilter` or `GatewayFilter`:

```java
@Component
public class AuthFilter implements GlobalFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // Filter logic
        return chain.filter(exchange);
    }
}
```

## Testing

### Test Route Forwarding
```bash
curl http://localhost:8080/api/data-management/datasets
```

### Test JWT Authentication
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/protected-endpoint
```

## Documentation

- **Spring Cloud Gateway Docs**: https://docs.spring.io/spring-cloud-gateway/
- **Nacos Discovery**: https://nacos.io/

## Related Links

- [Backend README](../README.md)
- [Main Application README](../services/main-application/README.md)
