package com.dataengine.collection.domain.service;

/**
 * DataX作业状态
 */
public class DataXJobStatus {
    
    private final String jobId;
    private final JobState state;
    private final double progress;
    private final long recordsProcessed;
    private final long recordsTotal;
    private final String errorMessage;
    private final long startTime;
    private final long endTime;

    public DataXJobStatus(String jobId, JobState state, double progress, 
                         long recordsProcessed, long recordsTotal, 
                         String errorMessage, long startTime, long endTime) {
        this.jobId = jobId;
        this.state = state;
        this.progress = progress;
        this.recordsProcessed = recordsProcessed;
        this.recordsTotal = recordsTotal;
        this.errorMessage = errorMessage;
        this.startTime = startTime;
        this.endTime = endTime;
    }

    public enum JobState {
        RUNNING, COMPLETED, FAILED, STOPPED
    }

    // Getters
    public String getJobId() {
        return jobId;
    }

    public JobState getState() {
        return state;
    }

    public double getProgress() {
        return progress;
    }

    public long getRecordsProcessed() {
        return recordsProcessed;
    }

    public long getRecordsTotal() {
        return recordsTotal;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public long getStartTime() {
        return startTime;
    }

    public long getEndTime() {
        return endTime;
    }

    public boolean isCompleted() {
        return state == JobState.COMPLETED;
    }

    public boolean isFailed() {
        return state == JobState.FAILED;
    }

    public boolean isRunning() {
        return state == JobState.RUNNING;
    }
}
