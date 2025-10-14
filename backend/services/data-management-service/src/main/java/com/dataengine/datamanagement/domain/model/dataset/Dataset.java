package com.dataengine.datamanagement.domain.model.dataset;

import lombok.Getter;
import lombok.Setter;

import java.io.File;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 数据集实体（与数据库表 t_dm_datasets 对齐）
 */
@Getter
@Setter
public class Dataset {

    private String id; // UUID
    private String name;
    private String description;

    // DB: dataset_type
    private String datasetType;

    private String category;
    // DB: data_source_id
    private String dataSourceId;
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

    // 聚合内的便捷集合（非持久化关联，由应用服务填充）
    private List<Tag> tags = new ArrayList<>();
    private List<DatasetFile> files = new ArrayList<>();

    public Dataset() {}

    public Dataset(String name, String description, String datasetType, String category,
                   String dataSourceId, String path, String format, String status, String createdBy) {
        this.name = name;
        this.description = description;
        this.datasetType = datasetType;
        this.category = category;
        this.dataSourceId = dataSourceId;
        this.path = path;
        this.format = format;
        this.status = status;
        this.createdBy = createdBy;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void initCreateParam(String datasetBasePath) {
        this.id = UUID.randomUUID().toString();
        this.path = datasetBasePath + File.separator + this.id;
        this.status = StatusConstants.DatasetStatuses.ACTIVE;
        this.createdBy = "system";
        this.updatedBy = "system";
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void updateBasicInfo(String name, String description, String category) {
        if (name != null && !name.isEmpty()) this.name = name;
        if (description != null) this.description = description;
        if (category != null) this.category = category;
        this.updatedAt = LocalDateTime.now();
    }

    public void updateStatus(String status, String updatedBy) {
        this.status = status;
        this.updatedBy = updatedBy;
        this.updatedAt = LocalDateTime.now();
    }

    public void addFile(DatasetFile file) {
        this.files.add(file);
        this.fileCount = this.fileCount + 1;
        this.sizeBytes = this.sizeBytes + (file.getFileSize() != null ? file.getFileSize() : 0L);
        this.updatedAt = LocalDateTime.now();
    }

    public void removeFile(DatasetFile file) {
        if (this.files.remove(file)) {
            this.fileCount = Math.max(0, this.fileCount - 1);
            this.sizeBytes = Math.max(0, this.sizeBytes - (file.getFileSize() != null ? file.getFileSize() : 0L));
            this.updatedAt = LocalDateTime.now();
        }
    }
}
