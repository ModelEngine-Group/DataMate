package com.datamate.operator.interfaces.dto;

import java.util.ArrayList;
import java.util.List;


import com.datamate.common.interfaces.PagingQuery;
import lombok.Getter;
import lombok.Setter;
import org.springaicommunity.mcp.annotation.McpToolParam;

/**
 * OperatorsListPostRequest
 */

@Getter
@Setter
public class OperatorsListPostRequest extends PagingQuery {
  private List<String> categories = new ArrayList<>();

  @McpToolParam(description = "算子关键词，支持查询算子名称和算子描述关键词查询", required = false)
  private String keyword;

  private String labelName;

  private Boolean isStar;
}

