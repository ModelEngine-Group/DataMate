package com.dataengine.datamanagement.domain.model.dataset;

import java.time.LocalDateTime;

/**
 * 标签实体（与数据库表 t_dm_tags 对齐）
 */
public class Tag {

    private String id; // UUID
    private String name;
    private String description;
    private String category;
    private String color;
    private Long usageCount = 0L;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Tag() {}

    public Tag(String name, String description, String category, String color) {
        this.name = name;
        this.description = description;
        this.category = category;
        this.color = color;
    }

    public void incrementUsage() { this.usageCount = (this.usageCount == null ? 1 : this.usageCount + 1); }
    public void decrementUsage() { if (this.usageCount != null && this.usageCount > 0) this.usageCount--; }

    // Getters & Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public Long getUsageCount() { return usageCount; }
    public void setUsageCount(Long usageCount) { this.usageCount = usageCount; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
