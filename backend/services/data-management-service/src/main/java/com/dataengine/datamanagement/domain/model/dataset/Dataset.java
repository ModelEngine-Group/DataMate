package com.dataengine.datamanagement.domain.model.dataset;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

/**
 * 数据集实体（与数据库表 t_dm_datasets 对齐）
 */
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

    private String status; // DRAFT/ACTIVE/ARCHIVED
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
    private Set<Tag> tags = new HashSet<>();
    private Set<DatasetFile> files = new HashSet<>();

    public Dataset() {}

    public Dataset(String name, String description, String datasetType, String category,
                   Long dataSourceId, String path, String format, String status, String createdBy) {
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

    // Getters & Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getDatasetType() { return datasetType; }
    public void setDatasetType(String datasetType) { this.datasetType = datasetType; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public Long getDataSourceId() { return dataSourceId; }
    public void setDataSourceId(Long dataSourceId) { this.dataSourceId = dataSourceId; }

    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }

    public String getFormat() { return format; }
    public void setFormat(String format) { this.format = format; }

    public Long getSizeBytes() { return sizeBytes; }
    public void setSizeBytes(Long sizeBytes) { this.sizeBytes = sizeBytes; }

    public Long getFileCount() { return fileCount; }
    public void setFileCount(Long fileCount) { this.fileCount = fileCount; }

    public Long getRecordCount() { return recordCount; }
    public void setRecordCount(Long recordCount) { this.recordCount = recordCount; }

    public Double getCompletionRate() { return completionRate; }
    public void setCompletionRate(Double completionRate) { this.completionRate = completionRate; }

    public Double getQualityScore() { return qualityScore; }
    public void setQualityScore(Double qualityScore) { this.qualityScore = qualityScore; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Boolean getPublic() { return isPublic; }
    public void setPublic(Boolean aPublic) { isPublic = aPublic; }

    public Boolean getFeatured() { return isFeatured; }
    public void setFeatured(Boolean featured) { isFeatured = featured; }

    public Long getDownloadCount() { return downloadCount; }
    public void setDownloadCount(Long downloadCount) { this.downloadCount = downloadCount; }

    public Long getViewCount() { return viewCount; }
    public void setViewCount(Long viewCount) { this.viewCount = viewCount; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    public String getCreatedBy() { return createdBy; }
    public void setCreatedBy(String createdBy) { this.createdBy = createdBy; }

    public String getUpdatedBy() { return updatedBy; }
    public void setUpdatedBy(String updatedBy) { this.updatedBy = updatedBy; }

    public Set<Tag> getTags() { return tags; }
    public void setTags(Set<Tag> tags) { this.tags = tags; }

    public Set<DatasetFile> getFiles() { return files; }
    public void setFiles(Set<DatasetFile> files) { this.files = files; }
}
