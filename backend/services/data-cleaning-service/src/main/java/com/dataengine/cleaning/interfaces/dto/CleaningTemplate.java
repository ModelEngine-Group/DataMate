package com.dataengine.cleaning.interfaces.dto;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;
import jakarta.validation.Valid;

/**
 * CleaningTemplate
 */

@Getter
@Setter
public class CleaningTemplate {

    private String id;

    private String name;

    private String description;

    @Valid
    private List<@Valid OperatorResponse> instance = new ArrayList<>();

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private OffsetDateTime updatedAt;
}

