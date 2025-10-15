package com.dataengine.cleaning.interfaces.dto;

import java.util.ArrayList;
import java.util.List;

import lombok.Getter;
import lombok.Setter;

/**
 * CreateCleaningTemplateRequest
 */

@Getter
@Setter
public class CreateCleaningTemplateRequest {

  private String name;

  private String description;

  private List<OperatorInstance> instance = new ArrayList<>();
}

