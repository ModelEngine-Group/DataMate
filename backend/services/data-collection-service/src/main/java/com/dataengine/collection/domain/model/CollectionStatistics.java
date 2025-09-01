package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class CollectionStatistics {
    private String id;
    private LocalDate statDate;
    private String periodType; // HOUR/DAY/WEEK/MONTH
    private Integer totalTasks;
    private Integer activeTasks;
    private Integer totalExecutions;
    private Integer successfulExecutions;
    private Integer failedExecutions;
    private Long totalRecordsProcessed;
    private Double avgExecutionTime;
    private Double avgThroughput;
    private LocalDateTime createdAt;
}
