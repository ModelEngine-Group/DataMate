package com.dataengine.cleaning.interfaces.dto;

import java.util.ArrayList;
import java.util.List;


import lombok.Getter;
import lombok.Setter;

/**
 * CreateCleaningTaskRequest
 */

@Getter
@Setter
public class CreateCleaningTaskRequest {

  private String name;

  private String description;

  private String srcDatasetId;

  private String srcDatasetName;

  private String destDatasetName;

  private String destDatasetType;

  private List<OperatorInstance> instance = new ArrayList<>();
}

