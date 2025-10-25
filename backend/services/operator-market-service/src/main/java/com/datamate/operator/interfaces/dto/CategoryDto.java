package com.datamate.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class CategoryDto {
    private Integer id;

    private String name;

    private String type;

    private Integer parentId;
}
