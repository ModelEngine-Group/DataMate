package com.datamate.collection.interfaces.dto;

import com.datamate.collection.common.enums.SyncMode;
import com.datamate.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.HashMap;
import java.util.Map;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * CreateCollectionTaskRequest
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CreateCollectionTaskRequest {
    @NotNull
    @Size(min = 1, max = 100)
    @Schema(name = "name", description = "任务名称", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonProperty("name")
    private String name;

    @Size(max = 500)
    @Schema(name = "description", description = "任务描述", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    @JsonProperty("description")
    private String description;

    @Valid
    @NotNull
    @Schema(name = "config", description = "归集配置，包含源端和目标端配置信息", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonProperty("config")
    private Map<String, Object> config = new HashMap<>();

    @NotNull
    @Valid
    @Schema(name = "syncMode", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonProperty("syncMode")
    private SyncMode syncMode;

    @Schema(name = "scheduleExpression", description = "Cron调度表达式 (syncMode=SCHEDULED 时必填)", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    @JsonProperty("scheduleExpression")
    private String scheduleExpression;

    /** 创建数据集参数 */
    @Valid
    private CreateDatasetRequest dataset;
}

