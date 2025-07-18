package com.edatamate.common.datax.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Builder
@Getter
@Setter
public class Reader {
    private String name;

    private Parameter parameter;
}
