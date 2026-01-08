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
    @McpToolParam(description = "算子分类id列表，每个父分类下的id放到一个列表中，最后汇总成一个大的列表", required = false)
    private List<List<String>> categories = new ArrayList<>();

    @McpToolParam(description = "算子关键词，支持查询算子名称和算子描述关键词查询", required = false)
    private String keyword;

    @McpToolParam(description = "算子关联的标签名称，当前暂不支持", required = false)
    private String labelName;

    @McpToolParam(description = "算子是否被收藏", required = false)
    private Boolean isStar;
}

