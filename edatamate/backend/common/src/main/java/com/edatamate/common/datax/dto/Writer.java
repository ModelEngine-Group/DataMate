package com.edatamate.common.datax.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Builder
@Getter
@Setter
public class Writer {
    private String name;

    private Parameter parameter;
}
