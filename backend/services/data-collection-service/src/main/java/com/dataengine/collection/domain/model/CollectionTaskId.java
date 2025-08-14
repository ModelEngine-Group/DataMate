package com.dataengine.collection.domain.model;

import com.dataengine.shared.domain.ValueObject;
import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Objects;
import java.util.UUID;

/**
 * 数据归集任务标识
 */
@Embeddable
public class CollectionTaskId extends ValueObject implements Serializable {

    @Column(name = "id")
    private String value;

    protected CollectionTaskId() {
        // JPA constructor
    }

    public CollectionTaskId(String value) {
        this.value = Objects.requireNonNull(value, "CollectionTaskId cannot be null");
    }

    public static CollectionTaskId generate() {
        return new CollectionTaskId(UUID.randomUUID().toString());
    }

    public static CollectionTaskId of(String value) {
        return new CollectionTaskId(value);
    }

    public String getValue() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        CollectionTaskId that = (CollectionTaskId) o;
        return Objects.equals(value, that.value);
    }

    @Override
    public int hashCode() {
        return Objects.hash(value);
    }

    @Override
    public String toString() {
        return "CollectionTaskId{" + value + "}";
    }
}
