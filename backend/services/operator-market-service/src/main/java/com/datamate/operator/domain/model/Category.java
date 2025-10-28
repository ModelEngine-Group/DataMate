package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@TableName(value = "t_operator_category", autoResultMap = true)
public class Category {
    private Integer id;

    private String name;

    private String type;

    private Integer parentId;
}
