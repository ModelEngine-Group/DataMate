from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.base_entity import LineageNode, LineageEdge

log = get_logger(__name__)


class LineageService:
    """血缘服务（Python 版）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_graph(
        self,
        from_node: Optional[LineageNode],
        edge: Optional[LineageEdge],
        to_node: Optional[LineageNode]
    ) -> None:
        """
        生成血缘图

        Args:
            from_node: 源节点
            edge: 边
            to_node: 目的节点
        """
        # 1. 如果 from_node 为空，直接返回不做任何处理
        if from_node is None:
            return

        # 2. 如果 from_node 有值，检查 from_node 是否存在
        existing_from = await self.get_node_by_id(from_node.id) if from_node.id else None

        if existing_from is None:
            # from_node 不存在，创建 from_node，记录 from_graph_id
            from_graph_id = str(uuid4())
            if not from_node.id:
                from_node.id = str(uuid4())
            from_node.graph_id = from_graph_id
            self.db.add(from_node)
            await self.db.flush()
        else:
            # from_node 存在，记录 from_graph_id
            from_graph_id = existing_from.graph_id

        # 处理 edge 和 to_node
        await self._generate_graph(edge, to_node, from_graph_id)

    async def _generate_graph(
        self,
        edge: Optional[LineageEdge],
        to_node: Optional[LineageNode],
        graph_id: Optional[str]
    ) -> None:
        # 无 edge，直接返回
        if edge is None:
            return

        # 有 edge，处理 edge，检查是否有 to_node
        await self._handle_lineage_edge(graph_id, edge)
        if to_node is None:
            return

        # 有 to_node，检查 to_node 是否存在
        existing_to = await self.get_node_by_id(to_node.id) if to_node.id else None

        if existing_to is None:
            # to_node 不存在，创建 to_node 后结束
            if not to_node.id:
                to_node.id = str(uuid4())
            to_node.graph_id = graph_id
            self.db.add(to_node)
            await self.db.flush()
        else:
            # to_node 存在，将 from_node 所在的图并入 to_node 所在的图后结束
            await self._merge_graph(graph_id, existing_to.graph_id)

    async def _handle_lineage_edge(self, graph_id: Optional[str], edge: LineageEdge) -> None:
        stmt = select(LineageEdge).where(
            LineageEdge.graph_id == graph_id,
            LineageEdge.from_node_id == edge.from_node_id,
            LineageEdge.to_node_id == edge.to_node_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            if not edge.id:
                edge.id = str(uuid4())
            edge.graph_id = graph_id
            self.db.add(edge)
            await self.db.flush()
        else:
            edge.id = existing.id
            if edge.graph_id is None:
                edge.graph_id = existing.graph_id
            # 覆盖更新现有记录
            existing.graph_id = edge.graph_id
            existing.process_id = edge.process_id
            existing.edge_type = edge.edge_type
            existing.name = edge.name
            existing.description = edge.description
            existing.edge_metadata = edge.edge_metadata
            existing.from_node_id = edge.from_node_id
            existing.to_node_id = edge.to_node_id
            await self.db.flush()

    async def _merge_graph(self, from_graph_id: Optional[str], to_graph_id: Optional[str]) -> None:
        if not from_graph_id or not to_graph_id or from_graph_id == to_graph_id:
            return

        from_nodes = await self.get_nodes_by_graph_id(from_graph_id)
        to_nodes = await self.get_nodes_by_graph_id(to_graph_id)

        # choose smaller graph as source, larger as target
        source_graph_id = from_graph_id if len(from_nodes) <= len(to_nodes) else to_graph_id
        target_graph_id = to_graph_id if source_graph_id == from_graph_id else from_graph_id
        source_nodes = from_nodes if source_graph_id == from_graph_id else to_nodes

        # update nodes' graph_id
        for node in source_nodes:
            if node is None:
                continue
            node.graph_id = target_graph_id
            self.db.add(node)

        # update edges' graph_id (edges belonging to the source graph)
        edges = await self.get_edges_by_graph_id(source_graph_id)
        for edge in edges:
            if edge is None:
                continue
            edge.graph_id = target_graph_id
            self.db.add(edge)

        await self.db.flush()

    async def get_nodes_by_graph_id(self, graph_id: str) -> List[LineageNode]:
        """从图ID获取图的节点列表"""
        stmt = select(LineageNode).where(LineageNode.graph_id == graph_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_edges_by_graph_id(self, graph_id: str) -> List[LineageEdge]:
        """从图ID获取图的边列表"""
        stmt = select(LineageEdge).where(LineageEdge.graph_id == graph_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_node_by_id(self, node_id: str) -> Optional[LineageNode]:
        """从节点ID获取节点"""
        return await self.db.get(LineageNode, node_id)
