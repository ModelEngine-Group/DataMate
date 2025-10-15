package com.dataengine.cleaning.interfaces.dto;

import java.util.HashMap;
import java.util.Map;


import lombok.Getter;
import lombok.Setter;

/**
 * OperatorInstance
 */

@Getter
@Setter
public class OperatorInstance {

    private String id;

    private Map<String, Object> overrides = new HashMap<>();
}

