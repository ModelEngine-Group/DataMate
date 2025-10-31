package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Setter
@Getter
@TableName(value = "t_operator_category", autoResultMap = true)
public class Category {
    private String id;

    private String name;

    private String value;

    private String type;

    private String parentId;

    private LocalDateTime createdAt;
}
