package com.dataengine.collection.application.dto;

import java.time.LocalDateTime;

/**
 * 连接测试结果DTO
 */
public class ConnectionTestResultDTO {

    private boolean success;
    private String message;
    private Integer latency;
    private LocalDateTime testedAt;

    public ConnectionTestResultDTO() {}

    public ConnectionTestResultDTO(boolean success, String message, Integer latency, LocalDateTime testedAt) {
        this.success = success;
        this.message = message;
        this.latency = latency;
        this.testedAt = testedAt;
    }

    // Getters and Setters
    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Integer getLatency() {
        return latency;
    }

    public void setLatency(Integer latency) {
        this.latency = latency;
    }

    public LocalDateTime getTestedAt() {
        return testedAt;
    }

    public void setTestedAt(LocalDateTime testedAt) {
        this.testedAt = testedAt;
    }
}
