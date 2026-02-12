package com.datamate.common.domain.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.datamate.common.domain.model.LineageEdge;
import com.datamate.common.domain.model.LineageNode;
import com.datamate.common.infrastructure.mapper.LineageEdgeMapper;
import com.datamate.common.infrastructure.mapper.LineageNodeMapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * 血缘服务层
 *
 * @since 2026/1/23
 */
@Component
@RequiredArgsConstructor
public class LineageService {
    private final LineageEdgeMapper lineageEdgeMapper;

    private final LineageNodeMapper lineageNodeMapper;

    /**
     * 生成血缘图
     *
     * @param fromNode 源节点
     * @param edge     边
     * @param toNode   目的节点
     */
    public void generateGraph(LineageNode fromNode, LineageEdge edge, LineageNode toNode) {
        // 如果 fromNode 为空，直接返回不做任何处理
        if (fromNode == null) {
            return;
        }

        // 如果 fromNode 有值，检查 fromNode 是否存在
        LineageNode existingFrom = lineageNodeMapper.selectById(fromNode.getId());

        String fromGraphId;
        if (existingFrom == null) {
            // fromNode 不存在，创建 fromNode，记录 fromGraphId
            fromGraphId = UUID.randomUUID().toString();
            fromNode.setGraphId(fromGraphId);
            lineageNodeMapper.insert(fromNode);
            // 处理 edge 和 toNode
        } else {
            // fromNode 存在，记录 fromGraphId
            fromGraphId = existingFrom.getGraphId();
        }
        // 处理 edge 和 toNode
        generateGraph(edge, toNode, fromGraphId);
    }

    private void generateGraph(LineageEdge edge, LineageNode toNode, String graphId) {
        // 无 edge，直接返回
        if (edge == null) {
            return;
        }

        // 有 edge，处理 edge，检查是否有 toNode
        handleLineageEdge(graphId, edge);
        if (toNode == null) {
            // 无 toNode，返回
            return;
        }

        // 有 toNode，检查 toNode 是否存在
        LineageNode existingTo = lineageNodeMapper.selectById(toNode.getId());

        if (existingTo == null) {
            // toNode 不存在，创建 toNode 后结束
            toNode.setGraphId(graphId);
            lineageNodeMapper.insert(toNode);
        } else {
            // toNode 存在，将 fromNode 所在的图 并入 toNode 所在的图后结束
            mergeGraph(graphId, existingTo.getGraphId());
        }
    }

    private void handleLineageEdge(String graphId, LineageEdge edge) {
        LambdaQueryWrapper<LineageEdge> wrapper = new LambdaQueryWrapper<LineageEdge>()
                .eq(LineageEdge::getGraphId, graphId)
                .eq(LineageEdge::getFromNodeId, edge.getFromNodeId())
                .eq(LineageEdge::getToNodeId, edge.getToNodeId());
        List<LineageEdge> lineageEdges = lineageEdgeMapper.selectList(wrapper);
        if (CollectionUtils.isEmpty(lineageEdges)) {
            edge.setId(UUID.randomUUID().toString());
            edge.setGraphId(graphId);
            lineageEdgeMapper.insert(edge);
        } else {
            edge.setId(lineageEdges.getFirst().getId());
            lineageEdgeMapper.updateById(edge);
        }
    }



    private void mergeGraph(String fromGraphId, String toGraphId) {
        if (fromGraphId == null || toGraphId == null || fromGraphId.equals(toGraphId)) {
            return;
        }

        List<LineageNode> fromNodes = getNodesByGraphId(fromGraphId);
        List<LineageNode> toNodes = getNodesByGraphId(toGraphId);

        // choose smaller graph as source, larger as target
        String sourceGraphId = fromNodes.size() <= toNodes.size() ? fromGraphId : toGraphId;
        String targetGraphId = sourceGraphId.equals(fromGraphId) ? toGraphId : fromGraphId;
        List<LineageNode> sourceNodes = sourceGraphId.equals(fromGraphId) ? fromNodes : toNodes;

        // update nodes' graphId
        for (LineageNode node : sourceNodes) {
            if (node == null) continue;
            node.setGraphId(targetGraphId);
            lineageNodeMapper.updateById(node);
        }

        // update edges' graphId (edges belonging to the source graph)
        List<LineageEdge> edges = getEdgesByGraphId(sourceGraphId);
        if (edges == null) {
            edges = Collections.emptyList();
        }
        for (LineageEdge edge : edges) {
            if (edge == null) continue;
            edge.setGraphId(targetGraphId);
            lineageEdgeMapper.updateById(edge);
        }
    }

    /**
     * 从图ID获取图的节点列表
     *
     * @param graphId 图ID
     * @return 图的节点列表
     */
    public List<LineageNode> getNodesByGraphId(String graphId) {
        LambdaQueryWrapper<LineageNode> wrapper = new LambdaQueryWrapper<LineageNode>()
                .eq(LineageNode::getGraphId, graphId);
        return lineageNodeMapper.selectList(wrapper);
    }

    /**
     * 从图ID获取图的边列表
     *
     * @param graphId 图ID
     * @return 图的边列表
     */
    public List<LineageEdge> getEdgesByGraphId(String graphId) {
        LambdaQueryWrapper<LineageEdge> wrapper = new LambdaQueryWrapper<LineageEdge>()
                .eq(LineageEdge::getGraphId, graphId);
        return lineageEdgeMapper.selectList(wrapper);
    }

    /**
     * 从节点ID获取节点
     *
     * @param nodeId 节点ID
     * @return 对应节点
     */
    public LineageNode getNodeById(String nodeId) {
        return lineageNodeMapper.selectById(nodeId);
    }
}