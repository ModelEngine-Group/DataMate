package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.common.enums.DatasetType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

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
    @Size(min = 1, max = 100)
    @NotBlank(message = "数据集名称不能为空")
    private String name;
    /** 数据集描述 */
    @Size(max = 500)
    private String description;
    /** 数据集类型 */
    @NotNull(message = "数据集类型不能为空")
    private DatasetType datasetType;
    /** 标签列表 */
    private List<String> tags;
    /** 数据源 */
    private String dataSource;
    /** 保留天数 */
    private Integer retentionDays;
}
