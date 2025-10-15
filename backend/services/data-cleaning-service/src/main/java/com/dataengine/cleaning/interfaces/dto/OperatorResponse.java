package com.dataengine.cleaning.interfaces.dto;

import java.time.OffsetDateTime;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

/**
 * OperatorResponse
 */

@Getter
@Setter
public class OperatorResponse {

    private String id;

    private String name;

    private String description;

    private String version;

    private String inputs;

    private String outputs;

    private String runtime;

    private String settings;

    private Boolean isStar;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime updatedAt;
}

