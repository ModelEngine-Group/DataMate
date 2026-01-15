import { useMemo, useRef, useEffect, useCallback } from "react";
import ForceGraph3D, { ForceGraphMethods } from "react-force-graph-3d";
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from "../knowledge-base.model";
import { Empty } from "antd";
import * as THREE from "three";
import SpriteText from "three-spritetext";

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
  const lightingInitializedRef = useRef(false);

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

  useEffect(() => {
    if (lightingInitializedRef.current) return;
    const graph = graphRef.current;
    const scene = graph?.scene?.();
    if (!scene) return;

    const ambient = new THREE.AmbientLight(0xffffff, 0.35);
    const key = new THREE.DirectionalLight(0xffffff, 0.8);
    key.position.set(120, 160, 220);
    const rim = new THREE.DirectionalLight(0x3b82f6, 0.5);
    rim.position.set(-140, -120, -180);
    const fill = new THREE.DirectionalLight(0xffffff, 0.45);
    fill.position.set(-60, 40, 140);

    ambient.name = "kg-ambient-light";
    key.name = "kg-key-light";
    rim.name = "kg-rim-light";
    fill.name = "kg-fill-light";

    scene.add(ambient, key, rim, fill);
    lightingInitializedRef.current = true;

    return () => {
      scene.remove(ambient);
      scene.remove(key);
      scene.remove(rim);
      scene.remove(fill);
      lightingInitializedRef.current = false;
    };
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
          const radius = getNodeRadius(node.id, degreeMap);
          const color = node.color || "#60a5fa";
          const group = new THREE.Group();
          const sphereRadius = getSphereDisplayRadius(radius);
          const baseColor = new THREE.Color(color);

          const litSphere = new THREE.Mesh(getSphereGeometry(sphereRadius), getSphereMaterial(baseColor));
          group.add(litSphere);

          const innerSphere = new THREE.Mesh(
            getSphereGeometry(Math.max(sphereRadius * 0.65, 0.6)),
            new THREE.MeshLambertMaterial({
              color: baseColor.clone().offsetHSL(0, 0, 0.15),
              emissive: baseColor.clone().multiplyScalar(0.2),
              transparent: true,
              opacity: 0.75,
            })
          );
          innerSphere.renderOrder = 2;
          group.add(innerSphere);

          const highlightOrb = createHighlightOrb(sphereRadius, baseColor);
          if (highlightOrb) {
            group.add(highlightOrb);
          }

          const label = new SpriteText(node.id || "", 1, "#f8fafc");
          label.center.set(0.5, 0.5);
          label.material.depthWrite = false;
          label.material.depthTest = false;
          label.renderOrder = 50;
          const maxDiameter = radius * 0.95;
          const fontRatio = Math.max(Math.min((radius / 18) * 5, 5), 1.5) * 1.15;
          label.textHeight = Math.min(maxDiameter, radius * 0.7) / fontRatio;
          label.position.set(0, 0, sphereRadius + label.textHeight * 0.95);
          group.add(label);

          return group;
        }}
        linkThreeObjectExtend={true}
        linkThreeObject={(link: any) => {
          const text = String(link.keywords || "").trim();
          if (!text) {
            return new THREE.Object3D();
          }
          const label = new SpriteText(text, 1, "#e2e8f0");
          label.center.set(0.5, 0.5);
          label.material.depthWrite = false;
          label.material.depthTest = false;
          label.renderOrder = 15;
          label.textHeight = 4;
          (label as any).__graphObjType = "link";
          (label as any).__data = link;
          label.userData.normalizedEdge = normalizeLinkData(link);
          return label;
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
          const material = (sprite as SpriteText).material as THREE.SpriteMaterial | undefined;
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
const sphereMaterialCache = new Map<string, THREE.MeshPhongMaterial>();
const sphereGeometryCache = new Map<number, THREE.SphereGeometry>();

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
  return null;
}

function createEdgeLabelTexture(text: string) {
  return createTextTexture(text, {
    fontSize: 10,
    paddingX: 4,
    paddingY: 2,
    backgroundFill: null,
    textFill: "rgba(241,245,249,0.9)",
    maxWidth: 60,
  });
}

function getNodeRadius(nodeId: string, degreeMap: Map<string, number>) {
  const degree = degreeMap.get(nodeId) || 1;
  return Math.min(12 + degree * 4, 64);
}

function getSphereDisplayRadius(nodeRadius: number) {
  return Math.max(nodeRadius * 0.16, 2.2);
}

function getSphereGeometry(radius: number) {
  const key = Number(radius.toFixed(2));
  if (!sphereGeometryCache.has(key)) {
    sphereGeometryCache.set(key, new THREE.SphereGeometry(radius, 48, 48));
  }
  return sphereGeometryCache.get(key)!;
}

function getSphereMaterial(color: THREE.Color) {
  const key = color.getHexString();
  if (!sphereMaterialCache.has(key)) {
    const specular = new THREE.Color(1, 1, 1).lerp(color.clone(), 0.35);
    sphereMaterialCache.set(
      key,
      new THREE.MeshPhongMaterial({
        color: color.clone(),
        emissive: color.clone().multiplyScalar(0.12),
        specular,
        shininess: 85,
        reflectivity: 0.4,
      })
    );
  }
  return sphereMaterialCache.get(key)!;
}

function createHighlightOrb(sphereRadius: number, baseColor: THREE.Color) {
  const orbRadius = Math.max(sphereRadius * 0.28, 0.4);
  const geometry = getSphereGeometry(orbRadius);
  const material = new THREE.MeshBasicMaterial({
    color: baseColor.clone().offsetHSL(0, 0, 0.35),
    transparent: true,
    opacity: 0.85,
  });
  const orb = new THREE.Mesh(geometry, material);
  orb.position.set(sphereRadius * 0.45, sphereRadius * 0.5, sphereRadius * 0.65);
  orb.renderOrder = 6;
  return orb;
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
  const sourceRadius = getNodeRadius(sourceId, degreeMap);
  const targetRadius = getNodeRadius(targetId, degreeMap);
  const minimumGap = (sourceRadius + targetRadius) * 5;

  const degreeBoost = ((degreeMap.get(sourceId) || 1) + (degreeMap.get(targetId) || 1)) / 2;
  const weight = Number(link.properties?.weight ?? link.properties?.score ?? 1);
  const base = 260;
  const dynamicDistance = base + degreeBoost * 55 + weight * 40;

  return Math.min(Math.max(dynamicDistance, minimumGap) * 100, 500);
}
