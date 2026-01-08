package com.datamate.cleaning.interfaces.dto;

import java.util.HashMap;
import java.util.List;
import java.util.Map;


import lombok.Getter;
import lombok.Setter;
import org.springaicommunity.mcp.annotation.McpToolParam;

/**
 * OperatorInstance
 */

@Getter
@Setter
public class OperatorInstanceDto {
    @McpToolParam(description = "算子ID")
    private String id;

    @McpToolParam(description = "算子名称")
    private String name;

    @McpToolParam(description = "算子输入类型，取值范围为text/image/audio/video/multimodal")
    private String inputs;

    @McpToolParam(description = "算子输出类型，取值范围为text/image/audio/video/multimodal")
    private String outputs;

    @McpToolParam(description = "算子所属分类的所有ID组成的列表。", required = false)
    private List<String> categories;

    @McpToolParam(description = "算子需要覆盖的参数", required = false)
    private Map<String, Object> overrides = new HashMap<>();
}

