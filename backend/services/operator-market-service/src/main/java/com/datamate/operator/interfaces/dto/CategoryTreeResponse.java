package com.datamate.operator.interfaces.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;


@Getter
@Setter
@NoArgsConstructor
public class CategoryTreeResponse {
    private String id;

    private String name;

    private Integer count;

    private List<CategoryDto> categories = new ArrayList<>();
}
