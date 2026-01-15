import { useMemo, useRef, useEffect } from "react";
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
      links: edges.map((edge) => ({
        ...edge,
        source: edge.source,
        target: edge.target,
        keywords: edge.properties?.keywords || edge.type,
      })),
    }),
    [nodes, edges]
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
        linkOpacity={0.35}
        linkColor={() => "rgba(148,163,184,0.45)"}
        linkDirectionalParticles={1}
        linkDirectionalParticleSpeed={0.004}
        linkDirectionalParticleColor={() => "rgba(248,250,252,0.7)"}
        linkCurvature={0.25}
        d3VelocityDecay={0.18}
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
              map: getCircleTexture(color, 0.95),
              depthWrite: false,
              transparent: true,
            })
          );
          coreSprite.scale.set(radius, radius, 1);
          group.add(coreSprite);

          const haloSprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
              map: getCircleTexture(color, 0.25, true),
              depthWrite: false,
              transparent: true,
            })
          );
          haloSprite.scale.set(radius * 1.8, radius * 1.8, 1);
          group.add(haloSprite);

          const texture = createTextTexture(node.id);
          if (texture) {
            const sprite = new THREE.Sprite(
              new THREE.SpriteMaterial({
                map: texture,
                depthWrite: false,
                transparent: true,
              })
            );
            sprite.position.set(0, radius * 0.04 + radius / 2, 0);
            sprite.scale.set(40, 20, 1);
            group.add(sprite);
          }

          return group;
        }}
        linkThreeObjectExtend={true}
        linkThreeObject={(link: any) => {
          const texture = createTextTexture(link.keywords || "");
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
          sprite.scale.set(70, 26, 1);
          return sprite;
        }}
        linkPositionUpdate={(sprite, { start, end }) => {
          const middlePos = {
            x: start.x + (end.x - start.x) / 2,
            y: start.y + (end.y - start.y) / 2,
            z: start.z + (end.z - start.z) / 2,
          };
          Object.assign(sprite.position, middlePos);
        }}
        onNodeClick={(node: any) => onSelectEntity?.({ type: "node", data: node })}
        onLinkClick={(link: any) => onSelectEntity?.({ type: "edge", data: link })}
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

  const gradient = ctx.createRadialGradient(size / 2, size / 2, soft ? size / 3 : 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, hexToRgba(color, opacity));
  gradient.addColorStop(1, hexToRgba(color, opacity * (soft ? 0 : 0.15)));
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

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

function createTextTexture(text: string) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  if (!context) return null;

  const fontSize = 36;
  context.font = `${fontSize}px "Inter", "PingFang SC", "Microsoft YaHei", sans-serif`;
  const padding = 48;
  const textWidth = context.measureText(text).width;
  canvas.width = textWidth + padding;
  canvas.height = fontSize + padding;
  context.font = `${fontSize}px "Inter", "PingFang SC", "Microsoft YaHei", sans-serif`;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillStyle = "rgba(2,6,23,0.25)";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "rgba(226,232,240,0.72)";
  context.fillText(text, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  return texture;
}
