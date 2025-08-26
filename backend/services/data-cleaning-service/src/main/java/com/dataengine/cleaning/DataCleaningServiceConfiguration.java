package com.dataengine.cleaning;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 数据归集服务配置类
 *
 * 基于DataX的数据归集和同步服务，支持多种数据源的数据采集和归集
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
@EnableJpaRepositories(basePackages = "com.dataengine.cleaning.infrastructure.repository")
@ComponentScan(basePackages = {
    "com.dataengine.cleaning",
    "com.dataengine.shared"
})
public class DataCleaningServiceConfiguration {
    // Configuration class for JAR packaging - no main method needed
}
