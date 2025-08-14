package com.dataengine.collection.domain.model;

/**
 * 任务状态枚举
 */
public enum TaskStatus {
    DRAFT("草稿"),
    READY("就绪"),
    RUNNING("运行中"),
    COMPLETED("已完成"),
    FAILED("失败"),
    STOPPED("已停止");

    private final String description;

    TaskStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

    public boolean isTerminal() {
        return this == COMPLETED || this == FAILED || this == STOPPED;
    }

    public boolean isActive() {
        return this == RUNNING;
    }
}
