package com.edatamate.common.datax.dto;


import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Builder
@Getter
@Setter
public class NfsParameter extends Parameter {
    private String ip;

    private String path;

    private List<String> fileType;
}
