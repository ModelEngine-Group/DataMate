package com.dataengine.operator.domain.modal;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
public class Operator {
    private String id;

    private String name;

    private String description;

    private String version;

    private String inputs;

    private String outputs;

    private String categories;

    private String runtime;

    private String settings;

    private Boolean isStar;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}

