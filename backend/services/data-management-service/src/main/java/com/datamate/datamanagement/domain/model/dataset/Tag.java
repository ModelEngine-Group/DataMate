package com.datamate.datamanagement.domain.model.dataset;

import com.datamate.common.domain.model.base.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 标签实体（与数据库表 t_dm_tags 对齐）
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Tag extends BaseEntity<String> {
    private String name;
    private String description;
    private String category;
    private String color;
    private Long usageCount = 0L;

    public Tag(String name, String description, String category, String color) {
        this.name = name;
        this.description = description;
        this.category = category;
        this.color = color;
    }

    public void decrementUsage() {
        if (this.usageCount != null && this.usageCount > 0) this.usageCount--;
    }
}
