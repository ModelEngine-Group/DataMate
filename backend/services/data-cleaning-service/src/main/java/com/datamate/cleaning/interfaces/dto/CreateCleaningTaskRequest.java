package com.datamate.cleaning.interfaces.dto;

import java.util.ArrayList;
import java.util.List;


import lombok.Getter;
import lombok.Setter;
import org.springaicommunity.mcp.annotation.McpToolParam;

/**
 * CreateCleaningTaskRequest
 */

@Getter
@Setter
public class CreateCleaningTaskRequest {
    @McpToolParam(description = "新建清洗任务名称")
    private String name;

    @McpToolParam(description = "新建清洗任务描述")
    private String description;

    @McpToolParam(description = "清洗任务使用的源数据集ID")
    private String srcDatasetId;

    @McpToolParam(description = "清洗任务使用的源数据集名称")
    private String srcDatasetName;

    @McpToolParam(description = "清洗任务写入的目标数据集ID", required = false)
    private String destDatasetId;

    @McpToolParam(description = "清洗任务写入的目标数据集名称，若destDatasetId为空，则创建新数据集。")
    private String destDatasetName;

    @McpToolParam(description = "清洗任务创建的目标数据集类型，取值范围为TEXT/IMAGE/VIDEO/AUDIO/OTHER")
    private String destDatasetType;

    @McpToolParam(description = "清洗任务使用的模板名称，与instance参数二选一，至少指定一个，优先级更高", required = false)
    private String templateId;

    @McpToolParam(description = "清洗任务使用的算子列表，与templateId参数二选一，至少指定一个。" +
            "注意：单个任务只能使用一种归属的算子，无法混合使用，如全部使用DataMate算子或全部使用DataJuicer算子。", required = false)
    private List<OperatorInstanceDto> instance = new ArrayList<>();
}

