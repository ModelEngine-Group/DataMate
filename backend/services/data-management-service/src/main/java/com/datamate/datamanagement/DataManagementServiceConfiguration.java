package com.datamate.datamanagement;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Data Management Service Configuration
 * 数据管理服务配置类 - 多源接入、元数据、血缘治理
 */
@Configuration
@EnableAsync
@ComponentScan(basePackages = {
        "com.datamate.datamanagement",
        "com.datamate.shared"
})
public class DataManagementServiceConfiguration {
    // Service configuration class for JAR packaging
    // 作为jar包形式提供服务的配置类
}
