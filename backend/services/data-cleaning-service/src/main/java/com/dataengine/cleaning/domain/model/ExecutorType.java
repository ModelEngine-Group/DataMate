package com.dataengine.cleaning.domain.model;

import lombok.Getter;

@Getter
public enum ExecutorType {
    DATA_PLATFORM("data_platform"),
    DATA_JUICER_RAY("ray"),
    DATA_JUICER_DEFAULT("default");

    private final String value;

    ExecutorType(String value) {
        this.value = value;
    }

    public static ExecutorType fromValue(String value) {
        for (ExecutorType type : ExecutorType.values()) {
            if (type.value.equals(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
}
