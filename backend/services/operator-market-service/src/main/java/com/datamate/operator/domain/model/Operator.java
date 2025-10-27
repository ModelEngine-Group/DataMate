package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@TableName(value = "t_operator")
public class Operator {
    private String id;

    private String name;

    private String description;

    private String version;

    private String inputs;

    private String outputs;

    private String runtime;

    private String settings;

    private String fileName;

    private Boolean isStar;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}

