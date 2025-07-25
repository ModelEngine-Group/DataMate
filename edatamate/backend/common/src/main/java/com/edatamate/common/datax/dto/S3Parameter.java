package com.edatamate.common.datax.dto;


import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Builder
@Getter
@Setter
public class S3Parameter extends Parameter {
    private String endpoint;

    private String bucket;

    private String ak;

    private String sk;
}
