package com.dataengine.datamanagement.domain.model.dataset;

import com.dataengine.shared.domain.AggregateRoot;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

/**
 * 数据集聚合根
 */
@Entity
@Table(name = "datasets")
public class Dataset extends AggregateRoot<String> {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "description", length = 500)
    private String description;

    @Embedded
    private DatasetType type;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private DatasetStatus status;

    @Column(name = "data_source", length = 255)
    private String dataSource;

    @Column(name = "target_location", length = 255)
    private String targetLocation;

    @Column(name = "file_count", nullable = false)
    private Integer fileCount = 0;

    @Column(name = "total_size", nullable = false)
    private Long totalSize = 0L;

    @Column(name = "completion_rate", nullable = false)
    private Float completionRate = 0.0f;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Column(name = "created_by", nullable = false, length = 50)
    private String createdBy;

    @ManyToMany(cascade = CascadeType.PERSIST, fetch = FetchType.LAZY)
    @JoinTable(
        name = "dataset_tags",
        joinColumns = @JoinColumn(name = "dataset_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    private Set<Tag> tags = new HashSet<>();

    @OneToMany(mappedBy = "dataset", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<DatasetFile> files = new HashSet<>();

    protected Dataset() {
        // For JPA
    }

    public Dataset(String id, String name, String description, DatasetType type, 
                   String dataSource, String targetLocation, String createdBy) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.type = type;
        this.dataSource = dataSource;
        this.targetLocation = targetLocation;
        this.createdBy = createdBy;
        this.status = DatasetStatus.ACTIVE;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void updateBasicInfo(String name, String description) {
        if (name != null && !name.trim().isEmpty()) {
            this.name = name;
        }
        if (description != null) {
            this.description = description;
        }
        this.updatedAt = LocalDateTime.now();
    }

    public void updateStatus(DatasetStatus status) {
        this.status = status;
        this.updatedAt = LocalDateTime.now();
    }

    public void addTag(Tag tag) {
        this.tags.add(tag);
        this.updatedAt = LocalDateTime.now();
    }

    public void removeTag(Tag tag) {
        this.tags.remove(tag);
        this.updatedAt = LocalDateTime.now();
    }

    public void addFile(DatasetFile file) {
        this.files.add(file);
        this.fileCount = this.files.size();
        this.totalSize += file.getSize();
        this.updatedAt = LocalDateTime.now();
        updateCompletionRate();
    }

    public void removeFile(DatasetFile file) {
        this.files.remove(file);
        this.fileCount = this.files.size();
        this.totalSize -= file.getSize();
        this.updatedAt = LocalDateTime.now();
        updateCompletionRate();
    }

    private void updateCompletionRate() {
        if (fileCount == 0) {
            this.completionRate = 0.0f;
            return;
        }
        
        long completedFiles = files.stream()
            .filter(file -> file.getStatus() == DatasetFileStatus.COMPLETED)
            .count();
        
        this.completionRate = (float) completedFiles / fileCount * 100;
    }

    @Override
    public String getId() {
        return id;
    }

    // Getters
    public String getName() { return name; }
    public String getDescription() { return description; }
    public DatasetType getType() { return type; }
    public DatasetStatus getStatus() { return status; }
    public String getDataSource() { return dataSource; }
    public String getTargetLocation() { return targetLocation; }
    public Integer getFileCount() { return fileCount; }
    public Long getTotalSize() { return totalSize; }
    public Float getCompletionRate() { return completionRate; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public String getCreatedBy() { return createdBy; }
    public Set<Tag> getTags() { return tags; }
    public Set<DatasetFile> getFiles() { return files; }
}
