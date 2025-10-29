package com.datamate.cleaning.interfaces.dto;

import java.time.LocalDateTime;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

/**
 * OperatorDto
 */

@Getter
@Setter
public class OperatorDto {

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
    private LocalDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime updatedAt;
}

