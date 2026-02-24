package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.common.enums.DatasetStatusType;
import com.datamate.datamanagement.common.enums.DatasetType;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springaicommunity.mcp.annotation.McpToolParam;

import java.util.List;

/**
 * 创建数据集请求DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CreateDatasetRequest {
    /** 数据集名称 */
    @Size(min = 1, max = 255, message = "数据集名称长度不能超过255个字符")
    @NotBlank(message = "数据集名称不能为空")
    @McpToolParam(description = "数据集名称")
    private String name;
    /** 数据集描述 */
    @Size(max = 500, message = "数据集描述长度不能超过500个字符")
    @McpToolParam(description = "数据集描述", required = false)
    private String description;
    /** 数据集类型 */
    @NotNull(message = "数据集类型不能为空")
    @McpToolParam(description = "数据集类型，取值范围为TEXT/IMAGE/VIDEO/AUDIO/OTHER")
    private DatasetType datasetType;
    /** 标签列表 */
    @Size(max = 20, message = "标签数量不能超过20个")
    @McpToolParam(description = "标签列表", required = false)
    private List<String> tags;
    /** 数据源 */
    @Size(max = 255, message = "数据源长度不能超过255个字符")
    @McpToolParam(description = "数据源", required = false)
    private String dataSource;
    /** 保留天数 */
    @Min(value = 0, message = "保留天数必须为非负整数")
    @McpToolParam(description = "保留天数", required = false)
    private Integer retentionDays;
    /** 数据集状态 */
    @McpToolParam(description = "数据集状态", required = false)
    private DatasetStatusType status;
}
