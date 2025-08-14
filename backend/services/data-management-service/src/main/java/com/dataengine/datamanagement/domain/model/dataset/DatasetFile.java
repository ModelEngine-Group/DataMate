package com.dataengine.datamanagement.domain.model.dataset;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * 数据集文件实体
 */
@Entity
@Table(name = "dataset_files")
public class DatasetFile extends com.dataengine.shared.domain.Entity<String> {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @Column(name = "file_name", nullable = false, length = 255)
    private String fileName;

    @Column(name = "original_name", nullable = false, length = 255)
    private String originalName;

    @Column(name = "file_type", nullable = false, length = 100)
    private String fileType;

    @Column(name = "size", nullable = false)
    private Long size;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private DatasetFileStatus status;

    @Column(name = "description", length = 500)
    private String description;

    @Column(name = "file_path", nullable = false, length = 500)
    private String filePath;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Column(name = "uploaded_by", nullable = false, length = 50)
    private String uploadedBy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "dataset_id", nullable = false)
    private Dataset dataset;

    protected DatasetFile() {
        // For JPA
    }

    public DatasetFile(String id, String fileName, String originalName, String fileType,
                      Long size, String description, String filePath, String uploadedBy,
                      Dataset dataset) {
        this.id = id;
        this.fileName = fileName;
        this.originalName = originalName;
        this.fileType = fileType;
        this.size = size;
        this.description = description;
        this.filePath = filePath;
        this.uploadedBy = uploadedBy;
        this.dataset = dataset;
        this.status = DatasetFileStatus.UPLOADED;
        this.updatedAt = LocalDateTime.now();
    }

    public void updateStatus(DatasetFileStatus status) {
        this.status = status;
    }

    public void updateDescription(String description) {
        this.description = description;
    }

    @Override
    public String getId() {
        return id;
    }

    // Getters
    public String getFileName() { return fileName; }
    public String getOriginalName() { return originalName; }
    public String getFileType() { return fileType; }
    public Long getSize() { return size; }
    public DatasetFileStatus getStatus() { return status; }
    public String getDescription() { return description; }
    public String getFilePath() { return filePath; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public String getUploadedBy() { return uploadedBy; }
    public Dataset getDataset() { return dataset; }
}
