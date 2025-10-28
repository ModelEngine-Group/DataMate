package com.datamate.cleaning.domain.model.entity;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;


@Getter
@Setter
public class TemplateWithInstance {
    private String id;

    private String name;

    private String description;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    private String operatorId;

    private Integer opIndex;

    private String settingsOverride;
}
