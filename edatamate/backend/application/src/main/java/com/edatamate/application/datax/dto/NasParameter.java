package com.edatamate.application.datax.dto;


import lombok.Builder;

@Builder
public class NasParameter extends Parameter {
    private String ip;

    private String path;

    private String prefix;
}
