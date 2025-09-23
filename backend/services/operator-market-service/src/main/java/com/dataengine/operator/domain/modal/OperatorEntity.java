package com.dataengine.operator.domain.modal;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
public class OperatorEntity {
    private Long id;

    private String name;

    private String description;

    private String category;

    private String version;

    private String author;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}

