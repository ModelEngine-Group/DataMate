package com.datamate.collection;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * 数据归集服务配置类
 *
 * 基于DataX的数据归集和同步服务，支持多种数据源的数据采集和归集
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
@EnableTransactionManagement
@ComponentScan(basePackages = {
        "com.datamate.collection",
        "com.datamate.datamanagement",
        "com.datamate.shared"
})
public class DataCollectionServiceConfiguration {
    // Configuration class for JAR packaging - no main method needed
}
