package com.datamate.common.domain.model;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.domain.enums.NodeType;
import lombok.Getter;
import lombok.Setter;

/**
 * 数据血缘：节点表
 * 节点表示实体对象（归集来源、数据集、知识库、模型等）
 *
 * @since 2026/1/23
 */
@Getter
@Setter
@TableName("t_lineage_node")
public class LineageNode {
    /**
     * 节点ID
     */
    @TableId(type = IdType.ASSIGN_ID)
    private String id;

    /**
     * 图ID
     */
    private String graphId;

    /**
     * 节点类型：DATASOURCE/DATASET/KNOWLEDGE_BASE/MODEL等
     */
    private NodeType nodeType;

    /**
     * 节点名称
     */
    private String name;

    /**
     * 节点描述
     */
    private String description;

    /**
     * 节点扩展信息（JSON）
     */
    private String nodeMetadata;
}
