package com.datamate.datamanagement.interfaces.dto;

import com.datamate.common.domain.model.LineageEdge;
import com.datamate.common.domain.model.LineageNode;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

/**
 * 数据集血缘
 *
 * @since 2026/1/23
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class DatasetLineage {
    /**
     * 节点列表
     */
    private List<LineageNode> lineageNodes;
    /**
     * 边列表
     */
    private List<LineageEdge> lineageEdges;
}
