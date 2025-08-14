package com.dataengine.datamanagement.domain.model.dataset;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;

/**
 * 数据集类型值对象
 */
@Embeddable
public class DatasetType {

    @Column(name = "type_code", nullable = false, length = 50)
    private String code;

    @Column(name = "type_name", nullable = false, length = 100)
    private String name;

    @Column(name = "type_description", length = 255)
    private String description;

    protected DatasetType() {
        // For JPA
    }

    public DatasetType(String code, String name, String description) {
        this.code = code;
        this.name = name;
        this.description = description;
    }

    public String getCode() { return code; }
    public String getName() { return name; }
    public String getDescription() { return description; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DatasetType that = (DatasetType) o;
        return code != null && code.equals(that.code);
    }

    @Override
    public int hashCode() {
        return code != null ? code.hashCode() : 0;
    }
}
