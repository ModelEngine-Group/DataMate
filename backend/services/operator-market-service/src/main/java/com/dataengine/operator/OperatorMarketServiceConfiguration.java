package com.dataengine.operator;

import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

/**
 * Operator Market Service Configuration
 * 算子市场服务配置类 - 版本、安装、评分、仓库
 */
@Configuration
@EnableFeignClients
@ComponentScan(basePackages = {
    "com.dataengine.operator",
    "com.dataengine.shared"
})
public class OperatorMarketServiceConfiguration {
    // Service configuration class for JAR packaging
    // 作为jar包形式提供服务的配置类
}
