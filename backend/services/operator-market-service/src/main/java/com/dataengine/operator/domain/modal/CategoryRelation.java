package com.dataengine.operator.domain.modal;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class CategoryRelation {
    private Integer id;

    private Integer categoryId;

    private String operatorId;

    private Category category;
}
