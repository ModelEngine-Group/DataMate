package com.dataengine.cleaning.domain.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 数据集实体（与数据库表 t_dm_datasets 对齐）
 */
@Getter
@Setter
@NoArgsConstructor
@JsonIgnoreProperties({"tags"})
public class DatasetResponse {
    /** 数据集ID */
    private String id;
    /** 数据集名称 */
    private String name;
    /** 数据集描述 */
    private String description;
    /** 数据集类型 */
    private String datasetType;
    /** 数据集状态 */
    private String status;
    /** 数据源 */
    private String dataSource;
    /** 目标位置 */
    private String targetLocation;
    /** 文件数量 */
    private Integer fileCount;
    /** 总大小（字节） */
    private Long totalSize;
    /** 完成率（0-100） */
    private Float completionRate;
    /** 创建时间 */
    private LocalDateTime createdAt;
    /** 更新时间 */
    private LocalDateTime updatedAt;
    /** 创建者 */
    private String createdBy;
}
