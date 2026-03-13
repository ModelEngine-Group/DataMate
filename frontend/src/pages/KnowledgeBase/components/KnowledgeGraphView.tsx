import React, { useMemo, useRef, useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from "../knowledge-base.model";

export type GraphEntitySelection =
  | { type: "node"; data: KnowledgeGraphNode }
  | { type: "edge"; data: KnowledgeGraphEdge };

interface KnowledgeGraphViewProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  height?: number | string;
  onSelectEntity?: (selection: GraphEntitySelection | null) => void;
}

const COLOR_PALETTE = ["#60a5fa", "#f87171", "#fbbf24", "#34d399", "#a78bfa", "#fb7185", "#22d3ee", "#818cf8", "#fb923c", "#4ade80"];

const KnowledgeGraphView: React.FC<KnowledgeGraphViewProps> = ({
  nodes,
  edges,
  height = 520,
  onSelectEntity,
}) => {
  const graphRef = useRef<any>();
  // 新增：用于监听尺寸的容器引用
  const containerRef = useRef<HTMLDivElement>(null);
  // 新增：保存当前实际宽高的状态
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // --- 核心修复：监听容器大小变化 ---
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({ width, height });

        // 强制通知 force-graph 组件更新内部 canvas 尺寸
        if (graphRef.current) {
          graphRef.current.width(width);
          graphRef.current.height(height);
          // 可选：如果希望尺寸变化后图谱自动居中，取消下行注释
          // graphRef.current.zoomToFit(400);
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force("charge").strength(-250);
      graphRef.current.d3Force("link").distance(120);
      graphRef.current.d3Force("center").strength(0.8);
    }
  }, [nodes]);

  const typeColorMap = useMemo(() => {
    const map = new Map<string, string>();
    const types = Array.from(new Set(nodes.map(n => n.properties?.entity_type || (n.labels && n.labels[0]) || 'default')));
    types.forEach((type, i) => map.set(type, COLOR_PALETTE[i % COLOR_PALETTE.length]));
    return map;
  }, [nodes]);

  const graphData = useMemo(() => ({
    nodes: nodes.map((node) => ({
      ...node,
      color: typeColorMap.get(node.properties?.entity_type || (node.labels && node.labels[0]) || 'default'),
      val: 8
    })),
    links: edges.map((edge) => ({
      ...edge,
      __originalEdge: edge,
      keywords: edge.properties?.keywords || edge.type || ""
    })),
  }), [nodes, edges, typeColorMap]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height, background: "#01030f", overflow: "hidden" }}
    >
      <ForceGraph2D
        ref={graphRef}
        // 传入动态计算的宽高
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        backgroundColor="#01030f"

        // --- 边视觉 ---
        linkColor={() => "rgba(255, 255, 255, 0.2)"}
        linkWidth={1.2}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.1}

        // --- 节点绘制 ---
        nodeCanvasObject={(node: never, ctx, globalScale) => {
          const { x, y, val: radius, color, id } = node;
          if (!Number.isFinite(x) || !Number.isFinite(y)) return;

          ctx.save();
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.shadowBlur = 10 / globalScale;
          ctx.shadowColor = color;
          ctx.fill();

          if (globalScale > 0.4) {
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = '#ffffff';
            ctx.shadowBlur = 0;
            ctx.fillText(id, x, y + radius + 2);
          }
          ctx.restore();
        }}

        linkPointerAreaPaint={(link: any, color, ctx, globalScale) => {
          const label = link.keywords;
          if (!label || globalScale < 1.1) return;
          const start = link.source;
          const end = link.target;
          if (typeof start !== 'object' || typeof end !== 'object') return;
          const fontSize = 9 / globalScale;
          const textPos = { x: start.x + (end.x - start.x) * 0.5, y: start.y + (end.y - start.y) * 0.5 };
          const angle = Math.atan2(end.y - start.y, end.x - start.x);
          const bRotate = angle > Math.PI / 2 || angle < -Math.PI / 2;
          ctx.save();
          ctx.translate(textPos.x, textPos.y);
          ctx.rotate(bRotate ? angle + Math.PI : angle);
          ctx.font = `${fontSize}px Sans-Serif`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = color;
          ctx.fillRect(-textWidth / 2 - 2, -fontSize / 2 - 2, textWidth + 4, fontSize + 4);
          ctx.restore();
        }}

        linkCanvasObjectMode={() => 'after'}
        linkCanvasObject={(link: any, ctx, globalScale) => {
          const MAX_DISPLAY_SCALE = 1.1;
          if (globalScale < MAX_DISPLAY_SCALE) return;
          const label = link.keywords;
          const start = link.source;
          const end = link.target;
          if (typeof start !== 'object' || typeof end !== 'object') return;
          const fontSize = 11 / globalScale;
          const textPos = { x: start.x + (end.x - start.x) * 0.5, y: start.y + (end.y - start.y) * 0.5 };
          let angle = Math.atan2(end.y - start.y, end.x - start.x);
          const bRotate = angle > Math.PI / 2 || angle < -Math.PI / 2;
          ctx.save();
          ctx.translate(textPos.x, textPos.y);
          ctx.rotate(bRotate ? angle + Math.PI : angle);
          ctx.font = `${fontSize}px Sans-Serif`;
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = 'rgba(1, 3, 15, 0.7)';
          ctx.fillRect(-textWidth / 2 - 1, -fontSize / 2, textWidth + 2, fontSize);
          ctx.fillStyle = '#94e2d5';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(label, 0, 0);
          ctx.restore();
        }}

        onNodeClick={(node: any) => onSelectEntity?.({ type: "node", data: node })}
        onLinkClick={(link: any) => {
          const originalData = link.__originalEdge || link;
          onSelectEntity?.({ type: "edge", data: originalData });
        }}
        onBackgroundClick={() => onSelectEntity?.(null)}
        cooldownTicks={120}
        d3VelocityDecay={0.4}
      />
    </div>
  );
};

export default KnowledgeGraphView;
