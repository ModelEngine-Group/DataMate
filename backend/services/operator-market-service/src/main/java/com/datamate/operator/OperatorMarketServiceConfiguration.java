package com.datamate.operator;

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Operator Market Service Configuration
 * 算子市场服务配置类 - 版本、安装、评分、仓库
 */
@Configuration
@EnableAsync
@EnableScheduling
@EntityScan(basePackages = "com.datamate.operator.domain.model")
@ComponentScan(basePackages = {
        "com.datamate.operator"
})
public class OperatorMarketServiceConfiguration {
    // Service configuration class for JAR packaging
    // 作为jar包形式提供服务的配置类
}
