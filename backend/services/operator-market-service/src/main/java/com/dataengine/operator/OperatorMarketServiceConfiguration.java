package com.dataengine.operator;

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Operator Market Service Configuration
 * 算子市场服务配置类 - 版本、安装、评分、仓库
 */
@Configuration
@EnableAsync
@EnableScheduling
@EnableJpaRepositories(basePackages = "com.dataengine.operator.domain.repository")
@EntityScan(basePackages = "com.dataengine.operator.domain.modal")
@ComponentScan(basePackages = {
    "com.dataengine.operator",
    "com.dataengine.shared"
})
public class OperatorMarketServiceConfiguration {
    // Service configuration class for JAR packaging
    // 作为jar包形式提供服务的配置类
}
