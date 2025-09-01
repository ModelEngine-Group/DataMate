package com.dataengine.datamanagement.domain.model.dataset;

import java.time.LocalDateTime;

/**
 * 数据集文件实体（与数据库表 t_dm_dataset_files 对齐）
 */
public class DatasetFile {

    private String id; // UUID
    private String datasetId; // UUID
    private String fileName;
    private String filePath;
    private String fileType; // IMAGE/TEXT/VIDEO/AUDIO
    private Long fileSize; // bytes
    private String fileFormat;
    private LocalDateTime uploadTime;
    private LocalDateTime lastAccessTime;
    private String status; // ACTIVE, PROCESSING, DELETED

    public DatasetFile() {}

    public DatasetFile(String datasetId, String fileName, String filePath, String fileType, Long fileSize, String fileFormat) {
        this.datasetId = datasetId;
        this.fileName = fileName;
        this.filePath = filePath;
        this.fileType = fileType;
        this.fileSize = fileSize;
        this.fileFormat = fileFormat;
        this.status = "ACTIVE";
    }

    // Getters & Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getDatasetId() { return datasetId; }
    public void setDatasetId(String datasetId) { this.datasetId = datasetId; }

    public String getFileName() { return fileName; }
    public void setFileName(String fileName) { this.fileName = fileName; }

    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }

    public String getFileType() { return fileType; }
    public void setFileType(String fileType) { this.fileType = fileType; }

    public Long getFileSize() { return fileSize; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }

    public String getFileFormat() { return fileFormat; }
    public void setFileFormat(String fileFormat) { this.fileFormat = fileFormat; }

    public LocalDateTime getUploadTime() { return uploadTime; }
    public void setUploadTime(LocalDateTime uploadTime) { this.uploadTime = uploadTime; }

    public LocalDateTime getLastAccessTime() { return lastAccessTime; }
    public void setLastAccessTime(LocalDateTime lastAccessTime) { this.lastAccessTime = lastAccessTime; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
