package com.datamate.common.domain.model.base;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 实体基类
 *
 * @param <ID> 实体ID类型
 */
@Getter
@Setter
@NoArgsConstructor
public abstract class BaseEntity<ID> implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 实体ID
     */
    @TableId(type = IdType.ASSIGN_ID)
    protected ID id;

    /**
     * 创建时间
     */
    @TableField(fill = FieldFill.INSERT)
    protected LocalDateTime createdAt;

    /**
     * 更新时间
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    protected LocalDateTime updatedAt;

    /**
     * 创建人
     */
    @TableField(fill = FieldFill.INSERT)
    protected String createdBy;

    /**
     * 更新人
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    protected String updatedBy;

    public BaseEntity(ID id) {
        super();
        this.id = id;
    }
}
