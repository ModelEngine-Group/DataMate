package com.dataengine.cleaning.domain.model;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 数据集实体（与数据库表 t_dm_datasets 对齐）
 */
@Getter
@Setter
@NoArgsConstructor
public class Dataset {

    private String id; // UUID
    private String name;
    private String description;

    // DB: dataset_type
    private String datasetType;

    private String category;
    // DB: data_source_id
    private Long dataSourceId;
    // DB: path
    private String path;
    // DB: format
    private String format;

    // DB: size_bytes
    private Long sizeBytes = 0L;
    private Long fileCount = 0L;
    private Long recordCount = 0L;

    private Double completionRate = 0.0;
    private Double qualityScore = 0.0;

    private String status; // DRAFT/ACTIVE/ARCHIVED/PROCESSING
    private Boolean isPublic = false;
    private Boolean isFeatured = false;

    private Long downloadCount = 0L;
    private Long viewCount = 0L;

    private Long version = 0L;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private String createdBy;
    private String updatedBy;
}
