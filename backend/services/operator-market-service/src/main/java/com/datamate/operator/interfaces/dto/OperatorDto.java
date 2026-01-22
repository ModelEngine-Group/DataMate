package com.datamate.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

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

    private List<String> categories;

    private String runtime;

    private String settings;

    private Map<String, Object> overrides;

    private String fileName;

    private Long fileSize;

    private String metrics;

    private Integer usageCount;

    private Boolean isStar;

    private List<String> requirements;

    private String readme;

    private List<OperatorReleaseDto> releases;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime updatedAt;
}

