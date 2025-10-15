package com.dataengine.cleaning.interfaces.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

import java.time.OffsetDateTime;
import java.util.List;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

/**
 * CleaningTask
 */

@Getter
@Setter
public class CleaningTask {

    private String id;

    private String name;

    private String description;

    private String srcDatasetId;

    private String srcDatasetName;

    private String destDatasetId;

    private String destDatasetName;

    /**
     * 任务当前状态
     */
    public enum StatusEnum {
        PENDING("pending"),

        RUNNING("running"),

        COMPLETED("completed"),

        STOPPED("stopped"),

        FAILED("failed");

        private final String value;

        StatusEnum(String value) {
            this.value = value;
        }

        @JsonValue
        public String getValue() {
            return value;
        }

        @JsonCreator
        public static StatusEnum fromValue(String value) {
            for (StatusEnum b : StatusEnum.values()) {
                if (b.value.equals(value)) {
                    return b;
                }
            }
            throw new IllegalArgumentException("Unexpected value '" + value + "'");
        }
    }

    private StatusEnum status;

    private String templateId;

    private List<OperatorResponse> instance;

    private CleaningProcess progress;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime startedAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime finishedAt;
}

