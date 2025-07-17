package com.edatamate.common.dataset;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 数据集实体类
 *
 * @author: dallas
 * @since: 2025-07-14
 */
@Setter
@Getter
@TableName("t_dataset")
public class Dataset {
    /**
     * 数据集ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 数据集名称
     */
    private String name;

    /**
     * 数据集描述
     */
    private String description;

    /**
     * 数据集类型
     */
    private DatasetType type;

    /**
     * 数据集状态
     */
    private DatasetStatus status;

    /**
     * 数据集所属父级ID
     */
    private Long parentId;

    /**
     * 数据集创建时间
     */
    private LocalDateTime createdTime;

    /**
     * 数据集创建人
     */
    private String createdBy;

    /**
     * 数据集更新时间
     */
    private LocalDateTime updatedTime;

    /**
     * 数据集更新人
     */
    private String updatedBy;
}
