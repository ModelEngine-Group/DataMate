package com.datamate.collection.domain.model.entity;

import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;

@Data
@EqualsAndHashCode(callSuper = false)
public class DataxTemplate {

    /**
     * 模板ID（UUID）
     */
    private String id;

    /**
     * 模板名称
     */
    private String name;

    /**
     * 源数据源类型
     */
    private String sourceType;

    /**
     * 目标数据源类型
     */
    private String targetType;

    /**
     * 模板内容（JSON格式）
     */
    private String templateContent;

    /**
     * 模板描述
     */
    private String description;

    /**
     * 版本号
     */
    private String version;

    /**
     * 是否为系统模板
     */
    private Boolean isSystem;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;

    /**
     * 创建者
     */
    private String createdBy;

    /**
     * 更新者
     */
    private String updatedBy;
}
