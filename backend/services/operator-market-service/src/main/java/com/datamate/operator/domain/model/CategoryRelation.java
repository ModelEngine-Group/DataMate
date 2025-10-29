package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@AllArgsConstructor
@TableName(value = "t_operator_category_relation", autoResultMap = true)
public class CategoryRelation {
    private Integer categoryId;

    private String operatorId;
}
