package com.dataengine.collection.infrastructure.runtime.datax;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "dataengine.data-collection.datax")
public class DataxProperties {
    private String homePath;        // DATAX_HOME
    private String pythonPath;      // python 可执行文件
    private String jobConfigPath;   // 生成的作业文件目录
    private String logPath;         // 运行日志目录
    private Integer maxMemory = 2048;
    private Integer channelCount = 5;
}
