package com.dataengine.operator.interfaces.dto;


import lombok.Getter;
import lombok.Setter;

/**
 * CreateOperatorRequest
 */

@Getter
@Setter
public class CreateOperatorRequest {

  private String name;

  private String description;

  private String version;

  private String category;

  private String documentation;
}

