package com.dataengine.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SubCategory {
    private long id;

    private String name;

    private long count;

    private String type;

    private long parentId;
}
