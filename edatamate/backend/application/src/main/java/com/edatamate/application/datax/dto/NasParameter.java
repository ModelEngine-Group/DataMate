package com.edatamate.application.datax.dto;


import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
public class NasParameter extends Parameter {
    private String ip;

    private String path;

    private String prefix;

    private String destPath;
}
