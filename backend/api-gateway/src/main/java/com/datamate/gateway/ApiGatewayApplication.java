package com.datamate.gateway;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;

/**
 * API Gateway & Auth Service Application
 * 统一的API网关和认证授权微服务
 * 提供路由、鉴权、限流等功能
 */
@SpringBootApplication
@ComponentScan(basePackages = {"com.datamate"})
@MapperScan(basePackages = {"com.datamate.**.mapper"})
public class ApiGatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(ApiGatewayApplication.class, args);
    }

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            // 数据合成服务路由
            .route("data-synthesis", r -> r.path("/api/synthesis/**")
                .uri("http://datamate-backend-python:18000"))

            // 数据标注服务路由
            .route("data-annotation", r -> r.path("/api/annotation/**")
                .uri("http://datamate-backend-python:18000"))

            // 数据评估服务路由
            .route("data-evaluation", r -> r.path("/api/evaluation/**")
                .uri("http://datamate-backend-python:18000"))

            // 数据归集服务路由
            .route("data-collection", r -> r.path("/api/data-collection/**")
                 .uri("http://datamate-backend-python:18000"))

            // 知识图谱RAG服务路由
            .route("python-service", r -> r.path("/api/rag/**", "api/models/**")
                 .uri("http://datamate-backend-python:18000"))

            .route("deer-flow-frontend", r -> r.path("/chat/**")
                .uri("http://deer-flow-frontend:3000"))

            .route("deer-flow-static", r -> r.path("/_next/**")
                .uri("http://deer-flow-frontend:3000"))

            .route("deer-flow-backend", r -> r.path("/deer-flow-backend/**")
                .filters(f -> f.stripPrefix(1).prefixPath("/api"))
                .uri("http://deer-flow-backend:8000"))

            // 网关服务（用户）
            .route("gateway", r -> r.path("/api/user/**")
                    .uri("http://localhost:8080"))

            // 其他后端服务
            .route("default", r -> r.path("/api/**")
                        .uri("http://datamate-backend:8080"))

            .build();
    }
}
