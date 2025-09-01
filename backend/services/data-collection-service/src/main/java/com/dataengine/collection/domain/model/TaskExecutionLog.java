package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class TaskExecutionLog {
    private String id;
    private String executionId;
    private String logLevel;
    private String message;
    private String thread;
    private String logger;
    private String exceptionStack;
    private LocalDateTime timestamp;
}
