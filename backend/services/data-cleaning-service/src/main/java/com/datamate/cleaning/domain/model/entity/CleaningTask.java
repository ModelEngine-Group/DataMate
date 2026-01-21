package com.datamate.cleaning.domain.model.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.cleaning.common.enums.CleaningTaskStatusEnum;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * CleaningTask
 */

@Getter
@Setter
@TableName(value = "t_clean_task", autoResultMap = true)
public class CleaningTask extends BaseEntity<String> {
    private String name;

    private String description;

    private CleaningTaskStatusEnum status;

    private String srcDatasetId;

    private String srcDatasetName;

    private String destDatasetId;

    private String destDatasetName;

    private Long beforeSize;

    private Long afterSize;

    private Integer fileCount;

    private LocalDateTime startedAt;

    private LocalDateTime finishedAt;
}

