package com.datamate.cleaning.common.enums;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum CleaningTaskStatusEnum {
    PENDING("PENDING"),

    RUNNING("RUNNING"),

    COMPLETED("COMPLETED"),

    STOPPED("STOPPED"),

    FAILED("FAILED");

    private final String value;

    CleaningTaskStatusEnum(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static CleaningTaskStatusEnum fromValue(String value) {
        for (CleaningTaskStatusEnum b : CleaningTaskStatusEnum.values()) {
            if (b.value.equals(value)) {
                return b;
            }
        }
        throw BusinessException.of(SystemErrorCode.INVALID_PARAMETER);
    }
}
