package com.dataengine.cleaning.interfaces.dto;

import java.util.ArrayList;
import java.util.List;


import lombok.Getter;
import lombok.Setter;

/**
 * UpdateCleaningTemplateRequest
 */

@Getter
@Setter
public class UpdateCleaningTemplateRequest {

    private String id;

    private String name;

    private String description;

    private List<OperatorInstance> instance = new ArrayList<>();
}

