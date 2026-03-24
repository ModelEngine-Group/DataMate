# API Gateway

## 概述

API Gateway 是 DataMate 的统一入口，基于 Spring Cloud Gateway 实现，负责路由转发、JWT 认证和限流。

## 架构

```
backend/api-gateway/
├── src/main/java/com/datamate/gateway/
│   ├── config/         # Gateway 配置
│   ├── filter/         # JWT 认证过滤器
│   └── route/          # 路由定义
└── src/main/resources/
    └── application.yml   # Gateway 配置
```

## 配置

### 端口
- **默认**: 8080
- **Nacos 发现端口**: 30000

### 关键配置
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

## 功能

### 1. 路由转发
- 将前端请求转发到对应的后端服务
- 支持负载均衡
- 路径重写

### 2. JWT 认证
- 基于 JWT Token 的认证
- Token 验证和过期检查
- 用户上下文传递

### 3. 限流
- （如配置）请求频率限制
- 防止 API 滥用

## 快速开始

### 前置条件
- JDK 21+
- Maven 3.8+
- Nacos 服务（如果使用服务发现）

### 构建
```bash
cd backend/api-gateway
mvn clean install
```

### 运行
```bash
cd backend/api-gateway
mvn spring-boot:run
```

## 开发

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
        // 过滤逻辑
        return chain.filter(exchange);
    }
}
```

## 测试

### 测试路由转发
```bash
curl http://localhost:8080/api/data-management/datasets
```

### 测试 JWT 认证
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/protected-endpoint
```

## 文档

- **Spring Cloud Gateway 文档**: https://docs.spring.io/spring-cloud-gateway/
- **Nacos 发现**: https://nacos.io/

## 相关链接

- [后端 README](../README.md)
- [主应用 README](../services/main-application/README.md)
