package com.datamate.collection.domain.model.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.collection.common.enums.SyncMode;
import com.datamate.collection.common.enums.TaskStatus;
import com.datamate.collection.common.enums.TemplateType;
import com.datamate.common.domain.model.base.BaseEntity;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.Map;
import java.util.UUID;

/**
 * 数据采集任务实体（与数据库表 t_dc_collection_tasks 对齐）
 */
@Getter
@Setter
@TableName(value = "t_dc_collection_tasks", autoResultMap = true)
public class CollectionTask extends BaseEntity<String> {
    private String name;
    private String description;
    private TemplateType taskType; // 任务类型
    private String targetPath; // 目标存储路径
    private String config; // DataX JSON 配置，包含源端和目标端配置信息
    private TaskStatus status;
    private SyncMode syncMode; // ONCE / SCHEDULED
    private String scheduleExpression;
    private Integer retryCount;
    private Integer timeoutSeconds;
    private Long maxRecords;
    private String sortField;
    private String lastExecutionId;

    public void addPath() {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            Map<String, Object> parameter = objectMapper.readValue(
                config,
                new TypeReference<>() {}
            );
            parameter.put("destPath", "/dataset/local/" + id);
            parameter.put("filePaths", Collections.singletonList(parameter.get("destPath")));
            config = objectMapper.writeValueAsString(parameter);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }

    public void initCreateParam() {
        this.id = UUID.randomUUID().toString();
        this.targetPath = "/dataset/local/" + id;
        this.status = TaskStatus.READY;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
}
