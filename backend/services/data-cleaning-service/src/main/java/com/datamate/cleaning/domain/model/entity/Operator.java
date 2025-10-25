package com.datamate.cleaning.domain.model.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@TableName(value = "t_operator", autoResultMap = true)
public class Operator {
    @TableId
    private String id;

    private String name;

    private String description;

    private String version;

    private String inputs;

    private String outputs;

    private String runtime;

    private String settings;

    private Boolean isStar;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
