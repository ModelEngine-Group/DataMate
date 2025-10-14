package com.dataengine.gateway;

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
@ComponentScan(basePackages = {
    "com.dataengine.gateway",
    "com.dataengine.shared"
})
public class ApiGatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(ApiGatewayApplication.class, args);
    }

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            // 数据归集服务路由
            .route("data-collection", r -> r.path("/api/data-collection/**")
                .uri("lb://data-collection-service"))

            // 数据管理服务路由
            .route("data-management", r -> r.path("/api/data-management/**")
                .uri("lb://data-management-service"))

            // 算子市场服务路由
            .route("operator-market", r -> r.path("/api/operators/**")
                .uri("lb://operator-market-service"))

            // 数据清洗服务路由
            .route("data-cleaning", r -> r.path("/api/cleaning/**")
                .uri("lb://data-cleaning-service"))

            // 数据合成服务路由
            .route("data-synthesis", r -> r.path("/api/synthesis/**")
                .uri("lb://data-synthesis-service"))

            // 数据标注服务路由
            .route("data-annotation", r -> r.path("/api/annotation/**")
                .uri("lb://data-annotation-service"))

            // 数据评估服务路由
            .route("data-evaluation", r -> r.path("/api/evaluation/**")
                .uri("lb://data-evaluation-service"))

            // 流程编排服务路由
            .route("pipeline-orchestration", r -> r.path("/api/pipelines/**")
                .uri("lb://pipeline-orchestration-service"))

            // 执行引擎服务路由
            .route("execution-engine", r -> r.path("/api/execution/**")
                .uri("lb://execution-engine-service"))

            // 认证服务路由
            .route("auth-service", r -> r.path("/api/auth/**")
                .uri("lb://auth-service"))

            // RAG服务路由
            .route("rag-indexer", r -> r.path("/api/rag/indexer/**")
                .uri("lb://rag-indexer-service"))
            .route("rag-query", r -> r.path("/api/rag/query/**")
                .uri("lb://rag-query-service"))

            .build();
    }
}
