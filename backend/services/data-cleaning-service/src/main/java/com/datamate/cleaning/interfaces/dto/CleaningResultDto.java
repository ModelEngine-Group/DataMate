package com.datamate.cleaning.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class CleaningResultDto {
    private String instanceId;

    private String srcFileId;

    private String destFileId;

    private String srcName;

    private String destName;

    private String srcType;

    private String destType;

    private long srcSize;

    private long destSize;

    private String status;

    private String result;
}
