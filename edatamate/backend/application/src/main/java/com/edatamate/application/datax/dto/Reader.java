package com.edatamate.application.datax.dto;

import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
public class Reader {
    private String name;

    private Parameter parameter;
}
