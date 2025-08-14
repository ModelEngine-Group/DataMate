package com.dataengine.collection.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * DataX配置属性
 */
@Component
@ConfigurationProperties(prefix = "datax")
public class DataXProperties {

    /**
     * DataX安装目录
     */
    private String home = "/opt/datax";

    /**
     * Python解释器路径
     */
    private String python = "/usr/bin/python";

    /**
     * 作业配置
     */
    private Job job = new Job();

    /**
     * 临时目录配置
     */
    private Temp temp = new Temp();

    public static class Job {
        /**
         * 最大并行作业数
         */
        private int maxParallel = 5;

        /**
         * 作业超时时间（秒）
         */
        private int timeout = 3600;

        /**
         * 默认内存大小（MB）
         */
        private int memory = 1024;

        // Getters and Setters
        public int getMaxParallel() {
            return maxParallel;
        }

        public void setMaxParallel(int maxParallel) {
            this.maxParallel = maxParallel;
        }

        public int getTimeout() {
            return timeout;
        }

        public void setTimeout(int timeout) {
            this.timeout = timeout;
        }

        public int getMemory() {
            return memory;
        }

        public void setMemory(int memory) {
            this.memory = memory;
        }
    }

    public static class Temp {
        /**
         * 临时目录
         */
        private String dir = "/tmp/datax-jobs";

        /**
         * 自动清理临时文件
         */
        private boolean autoClean = true;

        // Getters and Setters
        public String getDir() {
            return dir;
        }

        public void setDir(String dir) {
            this.dir = dir;
        }

        public boolean isAutoClean() {
            return autoClean;
        }

        public void setAutoClean(boolean autoClean) {
            this.autoClean = autoClean;
        }
    }

    // Getters and Setters
    public String getHome() {
        return home;
    }

    public void setHome(String home) {
        this.home = home;
    }

    public String getPython() {
        return python;
    }

    public void setPython(String python) {
        this.python = python;
    }

    public Job getJob() {
        return job;
    }

    public void setJob(Job job) {
        this.job = job;
    }

    public Temp getTemp() {
        return temp;
    }

    public void setTemp(Temp temp) {
        this.temp = temp;
    }
}
