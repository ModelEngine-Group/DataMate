package com.edatamate.common.k8s;

/**
 * Job 执行结果
 *
 * @param success Getters
 */
public record JobResult(boolean success, String jobId, String logs, long executionTimeMs, String errorMessage) {

    @Override
    public String toString() {
        return String.format("JobResult{success=%s, jobId='%s', executionTime=%dms, errorMessage='%s'}",
                success, jobId, executionTimeMs, errorMessage);
    }
}
