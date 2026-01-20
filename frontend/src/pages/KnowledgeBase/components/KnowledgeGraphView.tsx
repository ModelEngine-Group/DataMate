import React, {useMemo, useRef, useEffect} from "react";
import ForceGraph2D from "react-force-graph-2d";
import type {KnowledgeGraphEdge, KnowledgeGraphNode} from "../knowledge-base.model";

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

  useEffect(() => {
    if (graphRef.current) {
      // 1. 调整力导向平衡：减小斥力让独立图块靠近，增加向心力防止飘散
      graphRef.current.d3Force("charge").strength(-250); // 斥力适中
      graphRef.current.d3Force("link").distance(120);    // 边长适中
      graphRef.current.d3Force("center").strength(0.8);  // 增强向心力，让孤立集群往中间靠
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
      val: 8 // 统一基础大小，使视觉更整洁
    })),
    links: edges.map((edge) => ({
      ...edge,
      __originalEdge: edge,
      keywords: edge.properties?.keywords || edge.type || ""
    })),
  }), [nodes, edges, typeColorMap]);

  return (
    <div style={{width: "100%", height, background: "#01030f"}}>
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        backgroundColor="#01030f"

        // --- 边视觉 ---
        linkColor={() => "rgba(255, 255, 255, 0.2)"}
        linkWidth={1.2}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.1}

        // --- 节点绘制 ---
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const {x, y, val: radius, color, id} = node;
          if (!Number.isFinite(x) || !Number.isFinite(y)) return;

          ctx.save();
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.shadowBlur = 10 / globalScale;
          ctx.shadowColor = color;
          ctx.fill();

          // 节点名称
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
          const textPos = {x: start.x + (end.x - start.x) * 0.5, y: start.y + (end.y - start.y) * 0.5};
          const angle = Math.atan2(end.y - start.y, end.x - start.x);
          const bRotate = angle > Math.PI / 2 || angle < -Math.PI / 2;

          ctx.save();
          ctx.translate(textPos.x, textPos.y);
          ctx.rotate(bRotate ? angle + Math.PI : angle);

          ctx.font = `${fontSize}px Sans-Serif`;
          const textWidth = ctx.measureText(label).width;

          // 绘制一个与文字大小相同的透明矩形，颜色必须使用参数中的 'color'
          // 这是 react-force-graph 识别点击对象的关键（Color-picking 技术）
          ctx.fillStyle = color;
          ctx.fillRect(-textWidth / 2 - 2, -fontSize / 2 - 2, textWidth + 4, fontSize + 4);
          ctx.restore();
        }}

        // --- 边文字绘制：优化大小、位置和翻转逻辑 ---
        linkCanvasObjectMode={() => 'after'}
        linkCanvasObject={(link: any, ctx, globalScale) => {
          const MAX_DISPLAY_SCALE = 1.1;
          if (globalScale < MAX_DISPLAY_SCALE) return;

          const label = link.keywords;
          const start = link.source;
          const end = link.target;
          if (typeof start !== 'object' || typeof end !== 'object') return;

          // 边文字比节点文字小一点点（节点12，边11）
          const fontSize = 11 / globalScale;

          const textPos = {
            x: start.x + (end.x - start.x) * 0.5,
            y: start.y + (end.y - start.y) * 0.5
          };

          let angle = Math.atan2(end.y - start.y, end.x - start.x);

          // --- 核心修复：防止文字倒挂 ---
          // 如果角度在 90度 到 270度 之间，旋转180度让文字保持正向
          const bRotate = angle > Math.PI / 2 || angle < -Math.PI / 2;

          ctx.save();
          ctx.translate(textPos.x, textPos.y);
          ctx.rotate(bRotate ? angle + Math.PI : angle);

          ctx.font = `${fontSize}px Sans-Serif`;
          const textWidth = ctx.measureText(label).width;

          // 绘制极小的背景遮罩，紧贴文字
          ctx.fillStyle = 'rgba(1, 3, 15, 0.7)';
          ctx.fillRect(-textWidth / 2 - 1, -fontSize / 2, textWidth + 2, fontSize);

          ctx.fillStyle = '#94e2d5';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          // y轴偏移设为0，使其紧贴线条中心
          ctx.fillText(label, 0, 0);
          ctx.restore();
        }}

        onNodeClick={(node: any) => onSelectEntity?.({type: "node", data: node})}
        onLinkClick={(link: any) => {
          const originalData = link.__originalEdge || link;
          onSelectEntity?.({type: "edge", data: originalData});
        }}
        onBackgroundClick={() => onSelectEntity?.(null)}
        cooldownTicks={120}
        d3VelocityDecay={0.4} // 增加阻力，使布局更快稳定
      />
    </div>
  );
};

export default KnowledgeGraphView;
