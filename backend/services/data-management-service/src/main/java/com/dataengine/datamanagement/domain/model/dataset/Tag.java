package com.dataengine.datamanagement.domain.model.dataset;

import jakarta.persistence.*;
import java.util.HashSet;
import java.util.Set;

/**
 * 标签实体
 */
@Entity
@Table(name = "tags")
public class Tag extends com.dataengine.shared.domain.Entity<String> {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @Column(name = "name", nullable = false, unique = true, length = 50)
    private String name;

    @Column(name = "color", length = 7)
    private String color;

    @Column(name = "description", length = 200)
    private String description;

    @Column(name = "usage_count", nullable = false)
    private Integer usageCount = 0;

    @ManyToMany(mappedBy = "tags", fetch = FetchType.LAZY)
    private Set<Dataset> datasets = new HashSet<>();

    protected Tag() {
        // For JPA
    }

    public Tag(String id, String name, String color, String description) {
        this.id = id;
        this.name = name;
        this.color = color;
        this.description = description;
    }

    public void incrementUsage() {
        this.usageCount++;
    }

    public void decrementUsage() {
        if (this.usageCount > 0) {
            this.usageCount--;
        }
    }

    @Override
    public String getId() {
        return id;
    }

    // Getters
    public String getName() { return name; }
    public String getColor() { return color; }
    public String getDescription() { return description; }
    public Integer getUsageCount() { return usageCount; }
    public Set<Dataset> getDatasets() { return datasets; }
}
