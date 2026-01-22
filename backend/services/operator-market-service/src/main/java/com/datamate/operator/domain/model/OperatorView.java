package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@TableName(value = "v_operator")
public class OperatorView {
    @TableField(value = "operator_id")
    private String id;

    @TableField(value = "operator_name")
    private String name;

    private String description;

    private String version;

    private String inputs;

    private String outputs;

    private String categories;

    private String runtime;

    private String settings;

    private String fileName;

    private Long fileSize;

    private String metrics;

    private Integer usageCount;

    private Boolean isStar;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
