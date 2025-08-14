package com.dataengine.collection.domain.model;

import com.dataengine.shared.domain.ValueObject;
import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Objects;
import java.util.UUID;

/**
 * 数据源标识
 */
@Embeddable
public class DataSourceId extends ValueObject implements Serializable {

    @Column(name = "id")
    private String value;

    protected DataSourceId() {
        // JPA constructor
    }

    public DataSourceId(String value) {
        this.value = Objects.requireNonNull(value, "DataSourceId cannot be null");
    }

    public static DataSourceId generate() {
        return new DataSourceId(UUID.randomUUID().toString());
    }

    public static DataSourceId of(String value) {
        return new DataSourceId(value);
    }

    public String getValue() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DataSourceId that = (DataSourceId) o;
        return Objects.equals(value, that.value);
    }

    @Override
    public int hashCode() {
        return Objects.hash(value);
    }

    @Override
    public String toString() {
        return "DataSourceId{" + value + "}";
    }
}
