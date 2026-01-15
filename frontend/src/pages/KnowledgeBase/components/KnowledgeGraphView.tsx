import { useMemo, useRef, useEffect, useCallback } from "react";
import ForceGraph3D, { ForceGraphMethods } from "react-force-graph-3d";
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from "../knowledge-base.model";
import { Empty } from "antd";
import * as THREE from "three";

export type GraphEntitySelection =
  | { type: "node"; data: KnowledgeGraphNode }
  | { type: "edge"; data: KnowledgeGraphEdge };

interface KnowledgeGraphViewProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  height?: number | string;
  onSelectEntity?: (selection: GraphEntitySelection | null) => void;
}

const KnowledgeGraphView: React.FC<KnowledgeGraphViewProps> = ({
  nodes,
  edges,
  height = 520,
  onSelectEntity,
}) => {
  const graphRef = useRef<ForceGraphMethods>();

  const degreeMap = useMemo(() => {
    const map = new Map<string, number>();
    edges.forEach((edge) => {
      map.set(String(edge.source), (map.get(String(edge.source)) || 0) + 1);
      map.set(String(edge.target), (map.get(String(edge.target)) || 0) + 1);
    });
    return map;
  }, [edges]);

  const graphData = useMemo(
    () => ({
      nodes: nodes.map((node) => ({ ...node })),
      links: edges.map((edge) => {
        const enrichedEdge = {
          ...edge,
          source: edge.source,
          target: edge.target,
          keywords: edge.properties?.keywords || edge.type,
        } as any;
        enrichedEdge.__originalEdge = edge;
        return enrichedEdge;
      }),
    }),
    [nodes, edges]
  );

  const handleLinkSelect = useCallback(
    (link: any) => {
      onSelectEntity?.({ type: "edge", data: normalizeLinkData(link) });
    },
    [onSelectEntity]
  );

  useEffect(() => {
    graphRef.current?.zoomToFit(800);
  }, [graphData]);

  if (!nodes.length) {
    return (
      <div style={{ width: "100%", height }} className="flex items-center justify-center bg-slate-950/80">
        <Empty description="暂无图谱数据" />
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }} className="cosmic-graph-panel">
      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        backgroundColor="#01030f"
        linkOpacity={0.85}
        linkColor={() => "rgba(14,165,233,0.9)"}
        linkWidth={(link: any) => {
          const weight = Number(link.properties?.weight ?? link.properties?.score ?? 1);
          return Math.min(1.2 + weight * 0.4, 4);
        }}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={3.5}
        linkDirectionalParticleSpeed={0.0035}
        linkDirectionalParticleColor={() => "rgba(248,250,252,0.85)"}
        linkCurvature={0.25}
        d3VelocityDecay={0.18}
        linkDistance={(link: any) => computeLinkDistance(link, degreeMap)}
        nodeAutoColorBy={(node: any) => node.properties?.entity_type || "default"}
        nodeOpacity={1}
        nodeLabel={(node: any) => node.id}
        linkLabel={(link: any) => link.keywords}
        nodeThreeObject={(node: any) => {
          const radius = Math.min(12 + (degreeMap.get(node.id) || 1) * 4, 64);
          const color = node.color || "#60a5fa";
          const group = new THREE.Group();

          const coreSprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
              map: getCircleTexture(color, 1),
              depthWrite: false,
              transparent: true,
            })
          );
          coreSprite.scale.set(radius, radius, 1);
          group.add(coreSprite);

          const texture = createNodeLabelTexture(node.id, radius);
          if (texture) {
            const sprite = new THREE.Sprite(
              new THREE.SpriteMaterial({
                map: texture,
                depthWrite: false,
                transparent: true,
              })
            );
            const canvas = texture.image as HTMLCanvasElement | undefined;
            const aspect = canvas ? canvas.width / canvas.height : 2;
            const textHeight = radius * 0.78;
            sprite.scale.set(textHeight * aspect, textHeight, 1);
            sprite.position.set(0, 0, 0.01);
            group.add(sprite);
          }

          return group;
        }}
        linkThreeObjectExtend={true}
        linkThreeObject={(link: any) => {
          const texture = createEdgeLabelTexture(link.keywords || "");
          if (!texture) {
            return new THREE.Object3D();
          }
          const sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
              map: texture,
              depthWrite: false,
              transparent: true,
            })
          );
          const canvas = texture.image as HTMLCanvasElement | undefined;
          const aspect = canvas ? canvas.width / canvas.height : 3;
          const textHeight = 11;
          sprite.scale.set(textHeight * aspect, textHeight, 1);
          sprite.renderOrder = 2;
          (sprite as any).__graphObjType = "link";
          (sprite as any).__data = link;
          sprite.userData.normalizedEdge = normalizeLinkData(link);
          return sprite;
        }}
        linkPositionUpdate={(sprite, { start, end }) => {
          const middlePos = {
            x: start.x + (end.x - start.x) / 2,
            y: start.y + (end.y - start.y) / 2,
            z: start.z + (end.z - start.z) / 2,
          };
          Object.assign(sprite.position, middlePos);
          const dx = end.x - start.x;
          const dy = end.y - start.y;
          const angle = Math.atan2(dy, dx);
          const material = (sprite as THREE.Sprite).material as THREE.SpriteMaterial | undefined;
          if (material) {
            material.rotation = angle;
          }
        }}
        onNodeClick={(node: any) => onSelectEntity?.({ type: "node", data: node })}
        onLinkClick={handleLinkSelect}
        onBackgroundClick={() => onSelectEntity?.(null)}
      />
    </div>
  );
};

export default KnowledgeGraphView;

const circleTextureCache = new Map<string, THREE.Texture>();

function getCircleTexture(color: string, opacity = 1, soft = false) {
  const key = `${color}-${opacity}-${soft}`;
  if (circleTextureCache.has(key)) {
    return circleTextureCache.get(key)!;
  }
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  ctx.clearRect(0, 0, size, size);
  if (soft) {
    const gradient = ctx.createRadialGradient(size / 2, size / 2, size / 3, size / 2, size / 2, size / 2);
    gradient.addColorStop(0, hexToRgba(color, opacity * 0.15));
    gradient.addColorStop(1, hexToRgba(color, 0));
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);
  } else {
    ctx.fillStyle = hexToRgba(color, opacity);
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.closePath();
    ctx.fill();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  circleTextureCache.set(key, texture);
  return texture;
}

function hexToRgba(hex: string, alpha: number) {
  const parsedHex = hex.replace("#", "");
  const bigint = Number.parseInt(parsedHex.length === 3 ? parsedHex.repeat(2) : parsedHex, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function createNodeLabelTexture(text: string, radius: number) {
  const maxWidth = radius * 1.35;
  const fontSize = Math.max(Math.min(radius * 0.8, 26), 12);
  return createTextTexture(text, {
    fontSize,
    padding: 6,
    paddingX: 8,
    paddingY: 4,
    backgroundFill: null,
    textFill: "rgba(248,250,252,0.95)",
    maxWidth,
  });
}

function createEdgeLabelTexture(text: string) {
  return createTextTexture(text, {
    fontSize: 14,
    paddingX: 6,
    paddingY: 4,
    backgroundFill: null,
    textFill: "rgba(241,245,249,0.9)",
    maxWidth: 150,
  });
}

interface TextTextureOptions {
  fontSize?: number;
  padding?: number;
  paddingX?: number;
  paddingY?: number;
  backgroundFill?: string | null;
  textFill?: string;
  maxWidth?: number;
  fontFamily?: string;
}

function createTextTexture(text: string, options: TextTextureOptions = {}) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  if (!context) return null;

  const fontFamily = options.fontFamily ?? '"Inter", "PingFang SC", "Microsoft YaHei", sans-serif';
  let fontSize = options.fontSize ?? 36;
  context.font = `${fontSize}px ${fontFamily}`;

  const maxWidth = options.maxWidth;
  if (maxWidth) {
    while (fontSize > 12 && context.measureText(text).width > maxWidth) {
      fontSize -= 2;
      context.font = `${fontSize}px ${fontFamily}`;
    }
    text = truncateTextToWidth(context, text, maxWidth);
  }

  const paddingX = options.paddingX ?? options.padding ?? 32;
  const paddingY = options.paddingY ?? options.padding ?? 16;
  const textWidth = maxWidth ? Math.min(context.measureText(text).width, maxWidth) : context.measureText(text).width;

  canvas.width = Math.ceil(textWidth + paddingX * 2);
  canvas.height = Math.ceil(fontSize + paddingY * 2);

  context.font = `${fontSize}px ${fontFamily}`;
  context.textAlign = "center";
  context.textBaseline = "middle";

  if (options.backgroundFill !== null) {
    context.fillStyle = options.backgroundFill ?? "rgba(2,6,23,0.25)";
    context.fillRect(0, 0, canvas.width, canvas.height);
  } else {
    context.clearRect(0, 0, canvas.width, canvas.height);
  }

  context.fillStyle = options.textFill ?? "rgba(226,232,240,0.72)";
  context.fillText(text, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  return texture;
}

function truncateTextToWidth(context: CanvasRenderingContext2D, value: string, maxWidth: number) {
  if (!maxWidth || context.measureText(value).width <= maxWidth) {
    return value;
  }
  let truncated = value;
  const ellipsis = "...";
  while (truncated.length > 1 && context.measureText(`${truncated}${ellipsis}`).width > maxWidth) {
    truncated = truncated.slice(0, -1);
  }
  return `${truncated}${ellipsis}`;
}

function normalizeLinkData(link: any): KnowledgeGraphEdge {
  if (!link) {
    return {
      id: "",
      type: "",
      source: "",
      target: "",
      properties: {},
    };
  }

  if ((link as any).__normalizedEdge) {
    return (link as any).__normalizedEdge as KnowledgeGraphEdge;
  }

  const normalized: KnowledgeGraphEdge = {
    id: String(link.id ?? link.__id ?? ""),
    type: String(link.type ?? ""),
    source: extractNodeId(link.source),
    target: extractNodeId(link.target),
    properties: { ...(link.properties ?? {}) },
  };

  if (link.keywords && !normalized.properties.keywords) {
    (normalized.properties as Record<string, unknown>).keywords = link.keywords;
  }

  (link as any).__normalizedEdge = normalized;
  return normalized;
}

function extractNodeId(nodeRef: any) {
  if (nodeRef == null) return "";
  if (typeof nodeRef === "string" || typeof nodeRef === "number") {
    return String(nodeRef);
  }
  return String(nodeRef.id ?? nodeRef.__id ?? nodeRef.name ?? "");
}

function computeLinkDistance(link: any, degreeMap: Map<string, number>) {
  const sourceId = extractNodeId(link.source);
  const targetId = extractNodeId(link.target);
  const degreeBoost = ((degreeMap.get(sourceId) || 1) + (degreeMap.get(targetId) || 1)) / 2;
  const weight = Number(link.properties?.weight ?? link.properties?.score ?? 1);
  const base = 260;
  const distance = base + degreeBoost * 55 + weight * 40;
  return Math.min(distance, 1200);
}
