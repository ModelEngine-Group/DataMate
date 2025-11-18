package com.datamate.operator.interfaces.dto;

import java.util.ArrayList;
import java.util.List;


import com.datamate.common.interfaces.PagingQuery;
import lombok.Getter;
import lombok.Setter;

/**
 * OperatorsListPostRequest
 */

@Getter
@Setter
public class OperatorsListPostRequest extends PagingQuery {
  private List<String> categories = new ArrayList<>();

  private String operatorName;

  private String labelName;

  private Boolean isStar;
}

