package com.datamate.cleaning.domain.model.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@TableName(value = "t_clean_result", autoResultMap = true)
public class CleaningResult {
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
