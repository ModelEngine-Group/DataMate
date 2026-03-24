# API Gateway

## Overview

API Gateway 是 DataMate 的统一入口，基于 Spring Cloud Gateway 实现，负责路由转发、JWT 认证和限流。

## Architecture

```
backend/api-gateway/
├── src/main/java/com/datamate/gateway/
│   ├── config/         # Gateway configuration
│   ├── filter/         # JWT authentication filter
│   └── route/          # Route definitions
└免 src/main/resources/
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
- 将前端请求转发到对应的后端服务
- 支持负载均衡
- 路径重写

### 2. JWT Authentication
- 基于 JWT Token 的认证
- Token 验证和过期检查
- 用户上下文传递

### 3. Rate Limiting
- (如果配置）请求频率限制
- 防止 API 滥用

## Quick Start

### Prerequisites
- JDK 21+
- Maven 3.8+
- Nacos 服务（如果使用服务发现）

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

### 添加新路由
在 `application.yml` 或通过 Nacos 配置路由规则：

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

### 添加自定义过滤器
创建 `GlobalFilter` 或 `GatewayFilter`：

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

### 测试路由转发
```bash
curl http://localhost:8080/api/data-management/datasets
```

### 测试 JWT 认证
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/protected-endpoint
```

## Documentation

- **Spring Cloud Gateway Docs**: https://docs.spring.io/spring-cloud-gateway/
- **Nacos Discovery**: https://nacos.io/

## Related Links

- [Backend README](../README.md)
- [Main Application README](../services/main-application/README.md)
