package com.dataengine.main;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.data.elasticsearch.repository.config.EnableElasticsearchRepositories;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * 数据引擎平台主应用
 * 聚合所有业务服务JAR包的微服务启动类
 *
 * @author Data Engine Team
 * @version 1.0.0
 */
@SpringBootApplication
@ComponentScan(basePackages = {
    "com.dataengine.main",
    "com.dataengine.datamanagement",
    "com.dataengine.collection",
    "com.dataengine.operator",
    "com.dataengine.cleaning",
    "com.dataengine.synthesis",
    "com.dataengine.annotation",
    "com.dataengine.evaluation",
    "com.dataengine.pipeline",
    "com.dataengine.execution",
    "com.dataengine.rag",
    "com.dataengine.shared",
    "com.dataengine.common"
})
@EntityScan(basePackages = {
    "com.dataengine.datamanagement.domain.model",
    "com.dataengine.collection.domain.model",
    "com.dataengine.operator.domain.model",
    "com.dataengine.cleaning.domain.model",
    "com.dataengine.synthesis.domain.model",
    "com.dataengine.annotation.domain.model",
    "com.dataengine.evaluation.domain.model",
    "com.dataengine.pipeline.domain.model",
    "com.dataengine.execution.domain.model",
    "com.dataengine.rag.domain.model",
    "com.dataengine.shared.domain"
})
@EnableJpaRepositories(basePackages = {
    "com.dataengine.collection.infrastructure.persistence",
    "com.dataengine.operator.infrastructure.persistence",
    "com.dataengine.cleaning.infrastructure.persistence",
    "com.dataengine.synthesis.infrastructure.persistence",
    "com.dataengine.annotation.infrastructure.persistence",
    "com.dataengine.evaluation.infrastructure.persistence",
    "com.dataengine.pipeline.infrastructure.persistence",
    "com.dataengine.execution.infrastructure.persistence",
    "com.dataengine.rag.infrastructure.persistence"
})
@EnableTransactionManagement
@EnableAsync
@EnableScheduling
public class DataEnginePlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(DataEnginePlatformApplication.class, args);
    }
}
