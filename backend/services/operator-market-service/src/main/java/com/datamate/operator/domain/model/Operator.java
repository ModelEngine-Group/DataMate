package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@TableName(value = "t_operator")
public class Operator extends BaseEntity<String> {
    private String name;

    private String description;

    private String version;

    private String inputs;

    private String outputs;

    private String runtime;

    private String settings;

    private String fileName;

    private Long fileSize;

    private String metrics;

    private Integer usageCount;

    private Boolean isStar;
}

