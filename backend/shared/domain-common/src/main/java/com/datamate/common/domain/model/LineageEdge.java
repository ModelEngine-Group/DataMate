package com.datamate.common.domain.model;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.domain.enums.EdgeType;
import lombok.Getter;
import lombok.Setter;

/**
 * 数据血缘：边表
 * 边表示处理流程（归集任务、数据清洗、数据标注、数据合成、数据配比等）
 *
 * @since 2026/1/23
 */

@Getter
@Setter
@TableName("t_lineage_edge")
public class LineageEdge {
    /**
     * 边ID
     */
    @TableId(type = IdType.ASSIGN_ID)
    private String id;
    /**
     * 图ID
     */
    private String graphId;

    /**
     * 处理流程ID
     */
    private String processId;

    /**
     * 边类型：DATA_COLLECTION/DATA_CLEANING/DATA_LABELING/DATA_SYNTHESIS/DATA_RATIO等
     */
    private EdgeType edgeType;

    /**
     * 边名称
     */
    private String name;

    /**
     * 边描述
     */
    private String description;

    /**
     * 边扩展信息（JSON）
     */
    private String edgeMetadata;

    /**
     * 源节点ID
     */
    private String fromNodeId;

    /**
     * 目标节点ID
     */
    private String toNodeId;
}
