package com.datamate.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Setter
@Getter
public class CategoryDto {
    private String id;

    private String name;

    private String value;

    private long count;

    private String type;

    private String parentId;

    private LocalDateTime createdAt;
}
