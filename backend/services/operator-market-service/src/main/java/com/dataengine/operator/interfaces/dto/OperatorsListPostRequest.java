package com.dataengine.operator.interfaces.dto;

import java.util.ArrayList;
import java.util.List;


import lombok.Getter;
import lombok.Setter;

/**
 * OperatorsListPostRequest
 */

@Getter
@Setter
public class OperatorsListPostRequest {

  private Integer page;

  private Integer size;

  private List<Integer> categories = new ArrayList<>();

  private String operatorName;

  private String labelName;

  private Boolean isStar;
}

