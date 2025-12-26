package com.datamate.cleaning.interfaces.dto;

import java.util.HashMap;
import java.util.List;
import java.util.Map;


import lombok.Getter;
import lombok.Setter;

/**
 * OperatorInstance
 */

@Getter
@Setter
public class OperatorInstanceDto {

    private String id;

    private String name;

    private String inputs;

    private String outputs;

    private List<String> categories;

    private Map<String, Object> overrides = new HashMap<>();
}

