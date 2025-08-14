package com.dataengine.collection.application.dto;

import java.util.List;

/**
 * 任务执行日志DTO
 */
public class TaskExecutionLogsDTO {

    private String taskId;
    private List<LogEntry> logs;
    private Integer totalLines;
    private Integer currentPage;
    private Integer pageSize;

    public TaskExecutionLogsDTO() {}

    public TaskExecutionLogsDTO(String taskId, List<LogEntry> logs, Integer totalLines,
                              Integer currentPage, Integer pageSize) {
        this.taskId = taskId;
        this.logs = logs;
        this.totalLines = totalLines;
        this.currentPage = currentPage;
        this.pageSize = pageSize;
    }

    // Getters and Setters
    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public List<LogEntry> getLogs() {
        return logs;
    }

    public void setLogs(List<LogEntry> logs) {
        this.logs = logs;
    }

    public Integer getTotalLines() {
        return totalLines;
    }

    public void setTotalLines(Integer totalLines) {
        this.totalLines = totalLines;
    }

    public Integer getCurrentPage() {
        return currentPage;
    }

    public void setCurrentPage(Integer currentPage) {
        this.currentPage = currentPage;
    }

    public Integer getPageSize() {
        return pageSize;
    }

    public void setPageSize(Integer pageSize) {
        this.pageSize = pageSize;
    }

    /**
     * 日志条目内部类
     */
    public static class LogEntry {
        private String timestamp;
        private String level;
        private String message;

        public LogEntry() {}

        public LogEntry(String timestamp, String level, String message) {
            this.timestamp = timestamp;
            this.level = level;
            this.message = message;
        }

        public String getTimestamp() {
            return timestamp;
        }

        public void setTimestamp(String timestamp) {
            this.timestamp = timestamp;
        }

        public String getLevel() {
            return level;
        }

        public void setLevel(String level) {
            this.level = level;
        }

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }
    }
}
