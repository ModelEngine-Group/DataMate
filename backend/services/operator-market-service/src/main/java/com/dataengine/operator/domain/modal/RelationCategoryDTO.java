package com.dataengine.operator.domain.modal;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@AllArgsConstructor
public class RelationCategoryDTO {
    private Integer categoryId;
    private String operatorId;
    private String name;
    private Integer parentId;
}
