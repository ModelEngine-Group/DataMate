package com.datamate.cleaning.interfaces.dto;

import com.datamate.cleaning.common.enums.CleaningTaskStatusEnum;

import java.time.LocalDateTime;
import java.util.List;

import com.datamate.operator.interfaces.dto.OperatorDto;
import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

/**
 * CleaningTask
 */

@Getter
@Setter
public class CleaningTaskDto {

    private String id;

    private String name;

    private String description;

    private String srcDatasetId;

    private String srcDatasetName;

    private String destDatasetId;

    private String destDatasetName;

    private Long beforeSize;

    private Long afterSize;

    private Integer fileCount;

    private CleaningTaskStatusEnum status;

    private String templateId;

    private List<OperatorDto> instance;

    private CleaningProcess progress;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime createdAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime startedAt;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    private LocalDateTime finishedAt;
}

