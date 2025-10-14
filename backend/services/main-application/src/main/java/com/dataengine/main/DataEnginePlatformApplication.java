package com.dataengine.main;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.data.elasticsearch.repository.config.EnableElasticsearchRepositories;
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
@MapperScan(basePackages = {
    "com.dataengine.collection.infrastructure.persistence.mapper",
    "com.dataengine.datamanagement.infrastructure.persistence.mapper",
    "com.dataengine.operator.infrastructure.persistence.mapper",
    "com.dataengine.cleaning.infrastructure.persistence.mapper",
    "com.dataengine.common.infrastructure.mapper"
})
@EnableTransactionManagement
@EnableAsync
@EnableScheduling
public class DataEnginePlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(DataEnginePlatformApplication.class, args);
    }
}
