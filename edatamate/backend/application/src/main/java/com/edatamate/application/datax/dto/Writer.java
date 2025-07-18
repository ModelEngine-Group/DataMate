package com.edatamate.application.datax.dto;

import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
public abstract class Writer extends Parameter {
    private String name;

    private Parameter parameter;
}
