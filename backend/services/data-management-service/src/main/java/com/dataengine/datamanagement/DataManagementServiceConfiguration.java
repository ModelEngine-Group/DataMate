package com.dataengine.datamanagement;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

/**
 * Data Management Service Configuration
 * 数据管理服务配置类 - 多源接入、元数据、血缘治理
 */
@Configuration
@ComponentScan(basePackages = {
    "com.dataengine.datamanagement",
    "com.dataengine.shared"
})
public class DataManagementServiceConfiguration {
    // Service configuration class for JAR packaging
    // 作为jar包形式提供服务的配置类
}
