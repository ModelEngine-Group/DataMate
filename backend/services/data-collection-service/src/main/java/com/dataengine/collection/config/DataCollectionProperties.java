package com.dataengine.collection.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 数据归集服务配置
 */
@Configuration
@ConfigurationProperties(prefix = "data-collection")
public class DataCollectionProperties {

    /**
     * DataX配置
     */
    private DataX dataX = new DataX();

    /**
     * 执行配置
     */
    private Execution execution = new Execution();

    /**
     * 监控配置
     */
    private Monitoring monitoring = new Monitoring();

    public DataX getDataX() {
        return dataX;
    }

    public void setDataX(DataX dataX) {
        this.dataX = dataX;
    }

    public Execution getExecution() {
        return execution;
    }

    public void setExecution(Execution execution) {
        this.execution = execution;
    }

    public Monitoring getMonitoring() {
        return monitoring;
    }

    public void setMonitoring(Monitoring monitoring) {
        this.monitoring = monitoring;
    }

    /**
     * DataX相关配置
     */
    public static class DataX {
        private String homePath = "/opt/datax";
        private String pythonPath = "/usr/bin/python";
        private String jobConfigPath = "/tmp/datax/jobs";
        private String logPath = "/tmp/datax/logs";
        private Integer maxMemory = 2048;
        private Integer channelCount = 5;

        public String getHomePath() {
            return homePath;
        }

        public void setHomePath(String homePath) {
            this.homePath = homePath;
        }

        public String getPythonPath() {
            return pythonPath;
        }

        public void setPythonPath(String pythonPath) {
            this.pythonPath = pythonPath;
        }

        public String getJobConfigPath() {
            return jobConfigPath;
        }

        public void setJobConfigPath(String jobConfigPath) {
            this.jobConfigPath = jobConfigPath;
        }

        public String getLogPath() {
            return logPath;
        }

        public void setLogPath(String logPath) {
            this.logPath = logPath;
        }

        public Integer getMaxMemory() {
            return maxMemory;
        }

        public void setMaxMemory(Integer maxMemory) {
            this.maxMemory = maxMemory;
        }

        public Integer getChannelCount() {
            return channelCount;
        }

        public void setChannelCount(Integer channelCount) {
            this.channelCount = channelCount;
        }
    }

    /**
     * 执行相关配置
     */
    public static class Execution {
        private Integer maxConcurrentTasks = 10;
        private Integer taskTimeoutMinutes = 120;
        private Integer retryCount = 3;
        private Integer retryIntervalSeconds = 30;

        public Integer getMaxConcurrentTasks() {
            return maxConcurrentTasks;
        }

        public void setMaxConcurrentTasks(Integer maxConcurrentTasks) {
            this.maxConcurrentTasks = maxConcurrentTasks;
        }

        public Integer getTaskTimeoutMinutes() {
            return taskTimeoutMinutes;
        }

        public void setTaskTimeoutMinutes(Integer taskTimeoutMinutes) {
            this.taskTimeoutMinutes = taskTimeoutMinutes;
        }

        public Integer getRetryCount() {
            return retryCount;
        }

        public void setRetryCount(Integer retryCount) {
            this.retryCount = retryCount;
        }

        public Integer getRetryIntervalSeconds() {
            return retryIntervalSeconds;
        }

        public void setRetryIntervalSeconds(Integer retryIntervalSeconds) {
            this.retryIntervalSeconds = retryIntervalSeconds;
        }
    }

    /**
     * 监控相关配置
     */
    public static class Monitoring {
        private Integer statusCheckIntervalSeconds = 30;
        private Integer logRetentionDays = 30;
        private Boolean enableMetrics = true;

        public Integer getStatusCheckIntervalSeconds() {
            return statusCheckIntervalSeconds;
        }

        public void setStatusCheckIntervalSeconds(Integer statusCheckIntervalSeconds) {
            this.statusCheckIntervalSeconds = statusCheckIntervalSeconds;
        }

        public Integer getLogRetentionDays() {
            return logRetentionDays;
        }

        public void setLogRetentionDays(Integer logRetentionDays) {
            this.logRetentionDays = logRetentionDays;
        }

        public Boolean getEnableMetrics() {
            return enableMetrics;
        }

        public void setEnableMetrics(Boolean enableMetrics) {
            this.enableMetrics = enableMetrics;
        }
    }
}
