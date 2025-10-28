package com.datamate.main;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * 数据引擎平台主应用
 * 聚合所有业务服务JAR包的微服务启动类
 *
 * @author Data Mate Team
 * @version 1.0.0
 */
@SpringBootApplication
@ComponentScan(basePackages = {
        "com.datamate.main",
        "com.datamate.datamanagement",
        "com.datamate.collection",
        "com.datamate.operator",
        "com.datamate.cleaning",
        "com.datamate.synthesis",
        "com.datamate.annotation",
        "com.datamate.evaluation",
        "com.datamate.pipeline",
        "com.datamate.execution",
        "com.datamate.common"
})
@MapperScan(basePackages = {
        "com.datamate.collection.infrastructure.persistence.mapper",
        "com.datamate.datamanagement.infrastructure.persistence.mapper",
        "com.datamate.operator.infrastructure.persistence.mapper",
        "com.datamate.cleaning.infrastructure.persistence.mapper",
        "com.datamate.**.mapper"
})
@EnableTransactionManagement
@EnableAsync
@EnableScheduling
public class DataMatePlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(DataMatePlatformApplication.class, args);
    }
}
