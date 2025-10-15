package com.dataengine.operator.interfaces.dto;


import lombok.Getter;
import lombok.Setter;

/**
 * UpdateOperatorRequest
 */

@Getter
@Setter
public class UpdateOperatorRequest {
  private String name;

  private String description;

  private String version;

  private String category;

  private String documentation;
}

