package com.edatamate.common.datax.dto;


import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Builder
@Getter
@Setter
public class NasParameter extends Parameter {
    private String ip;

    private String path;
}
