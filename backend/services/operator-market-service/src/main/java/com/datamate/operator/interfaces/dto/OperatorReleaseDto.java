package com.datamate.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
public class OperatorReleaseDto {
    private String id;

    private String version;

    private LocalDateTime releaseDate;

    private List<String> changelog;
}
