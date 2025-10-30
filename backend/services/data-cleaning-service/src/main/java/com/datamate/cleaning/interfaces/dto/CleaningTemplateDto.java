package com.datamate.cleaning.interfaces.dto;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import com.datamate.operator.interfaces.dto.OperatorDto;
import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

/**
 * CleaningTemplate
 */

@Getter
@Setter
public class CleaningTemplateDto {

    private String id;

    private String name;

    private String description;

    private List<OperatorDto> instance = new ArrayList<>();

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime updatedAt;
}

