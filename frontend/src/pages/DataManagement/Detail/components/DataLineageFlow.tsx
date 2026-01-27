import type React from "react"
import { useState, useRef, useEffect, useMemo } from "react"
import { Card, Badge } from "antd"
import { Database, Table, Brain, BookOpen, X } from "lucide-react"
import {Dataset} from "@/pages/DataManagement/dataset.model.ts";
import { queryDatasetLineageByIdUsingGet } from "@/pages/DataManagement/dataset.api.ts";

interface Node {
  id: string
  type: "datasource" | "dataset" | "model" | "knowledge"
  label: string
  x: number
  y: number
  description?: string
  status?: string
  fileCount?: number
  size?: string
  updateTime?: string
}

interface Edge {
  id: string
  from: string
  to: string
  label: string
  edgeType?: string
  processId?: string
  description?: string
}
interface LineageNodeDTO {
  id: string
  name: string
  nodeType?: string
  type?: string
  graphId?: string
  description?: string
  nodeMetadata?: string
  metadata?: string
}

interface LineageEdgeDTO {
  id: string
  graphId?: string
  processId?: string
  edgeType?: string
  name?: string
  description?: string
  edgeMetadata?: string
  metadata?: string
  fromNodeId: string
  toNodeId: string
}

const nodeConfig = {
  datasource: {
    icon: Database,
    color: "oklch(0.5 0.2 250)",
    bgColor: "oklch(0.92 0.05 250)",
    borderColor: "oklch(0.7 0.15 250)",
  },
  dataset: {
    icon: Table,
    color: "oklch(0.5 0.18 200)",
    bgColor: "oklch(0.92 0.05 200)",
    borderColor: "oklch(0.7 0.15 200)",
  },
  model: {
    icon: Brain,
    color: "oklch(0.5 0.18 320)",
    bgColor: "oklch(0.92 0.05 320)",
    borderColor: "oklch(0.7 0.15 320)",
  },
  knowledge: {
    icon: BookOpen,
    color: "oklch(0.5 0.18 140)",
    bgColor: "oklch(0.92 0.05 140)",
    borderColor: "oklch(0.7 0.15 140)",
  },
}

const edgeTypeLabels: Record<string, string> = {
  DATA_COLLECTION: "数据归集",
  DATA_CLEANING: "数据处理",
  DATA_LABELING: "数据标注",
  DATA_SYNTHESIS: "数据合成",
  DATA_RATIO: "数据配比",
}

const nodeTypeToUi: Record<string, Node["type"]> = {
  DATASOURCE: "datasource",
  DATASET: "dataset",
  MODEL: "model",
  KNOWLEDGE_BASE: "knowledge",
  KNOWLEDGE: "knowledge",
}

const layoutColumns: Record<Node["type"], number> = {
  datasource: 0,
  dataset: 1,
  model: 2,
  knowledge: 3,
}

const layoutConfig = {
  startX: 80,
  startY: 90,
  columnGap: 300,
  rowGap: 150,
  nodeWidth: 180,
  nodeHeight: 74,
  canvasWidth: 2000,
  canvasHeight: 720,
}

export default function DataLineageFlow({ dataset }: { dataset: Dataset }) {
  const [graphNodes, setGraphNodes] = useState<Node[]>([])
  const [graphEdges, setGraphEdges] = useState<Edge[]>([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null)
  const [draggedNode, setDraggedNode] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [renderTrigger, setRenderTrigger] = useState(0)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const edgeHitAreasRef = useRef<Array<{ id: string; x: number; y: number; width: number; height: number }>>([])
  const datasetId = dataset?.id

  const layoutGraph = useMemo(() => {
    return (nodes: LineageNodeDTO[], edges: LineageEdgeDTO[]): { nodes: Node[]; edges: Edge[] } => {
      const columns: Record<Node["type"], Node[]> = {
        datasource: [],
        dataset: [],
        model: [],
        knowledge: [],
      }

      const mappedNodes: Node[] = nodes.map((node) => {
        const rawType = node.nodeType ?? node.type ?? "DATASET"
        const uiType = nodeTypeToUi[rawType] ?? "dataset"
        const columnIndex = layoutColumns[uiType]
        const baseX = layoutConfig.startX + columnIndex * layoutConfig.columnGap
        const currentY = layoutConfig.startY + columns[uiType].length * layoutConfig.rowGap
        const mapped: Node = {
          id: node.id,
          type: uiType,
          label: node.name,
          description: node.description,
          x: baseX,
          y: currentY,
        }
        columns[uiType].push(mapped)
        return mapped
      })

      const mappedEdges: Edge[] = edges.map((edge, index) => ({
        id: edge.id || `${edge.fromNodeId}-${edge.toNodeId}-${index}`,
        from: edge.fromNodeId,
        to: edge.toNodeId,
        label: edge.name || (edge.edgeType ? edgeTypeLabels[edge.edgeType] || edge.edgeType : "处理流程"),
        edgeType: edge.edgeType,
        processId: edge.processId,
        description: edge.description,
      }))

      return { nodes: mappedNodes, edges: mappedEdges }
    }
  }, [])

  useEffect(() => {
    if (!datasetId) {
      setGraphNodes([])
      setGraphEdges([])
      return
    }

    const fetchLineage = async () => {
      try {
        const res = await queryDatasetLineageByIdUsingGet(datasetId)
        const payload = res?.data?.data ?? res?.data
        const lineageNodes: LineageNodeDTO[] = payload?.lineageNodes ?? []
        const lineageEdges: LineageEdgeDTO[] = payload?.lineageEdges ?? []
        const { nodes, edges } = layoutGraph(lineageNodes, lineageEdges)
        setGraphNodes(nodes)
        setGraphEdges(edges)
      } catch (error) {
        setGraphNodes([])
        setGraphEdges([])
      }
    }

    fetchLineage()
  }, [datasetId, layoutGraph])

  useEffect(() => {
    if (selectedNode && !graphNodes.some((node) => node.id === selectedNode.id)) {
      setSelectedNode(null)
    }
  }, [graphNodes, selectedNode])

  useEffect(() => {
    if (selectedEdge && !graphEdges.some((edge) => edge.id === selectedEdge.id)) {
      setSelectedEdge(null)
    }
  }, [graphEdges, selectedEdge])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    ctx.clearRect(0, 0, rect.width, rect.height)
    edgeHitAreasRef.current = []

    graphEdges.forEach((edge) => {
      const fromNode = graphNodes.find((n) => n.id === edge.from)
      const toNode = graphNodes.find((n) => n.id === edge.to)
      if (!fromNode || !toNode) return

      const isEdgeActive = hoveredEdge === edge.id || selectedEdge?.id === edge.id
      const isHighlighted =
        isEdgeActive ||
        hoveredNode === edge.from ||
        hoveredNode === edge.to ||
        selectedNode?.id === edge.from ||
        selectedNode?.id === edge.to

      const startX = fromNode.x + layoutConfig.nodeWidth
      const startY = fromNode.y + layoutConfig.nodeHeight / 2
      const endX = toNode.x
      const endY = toNode.y + layoutConfig.nodeHeight / 2

      const controlPointOffset = Math.abs(endX - startX) * 0.4
      const cp1x = startX + controlPointOffset
      const cp1y = startY
      const cp2x = endX - controlPointOffset
      const cp2y = endY

      ctx.beginPath()
      ctx.moveTo(startX, startY)
      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY)

      const gradient = ctx.createLinearGradient(startX, startY, endX, endY)
      const fromConfig = nodeConfig[fromNode.type]
      const toConfig = nodeConfig[toNode.type]

      if (isHighlighted) {
        gradient.addColorStop(0, fromConfig.color)
        gradient.addColorStop(1, toConfig.color)
        ctx.strokeStyle = gradient
        ctx.lineWidth = 3
      } else {
        ctx.strokeStyle = "oklch(0.85 0.03 250)"
        ctx.lineWidth = 2
      }

      if (isHighlighted) {
        ctx.setLineDash([])
      } else {
        ctx.setLineDash([5, 3])
      }

      ctx.stroke()
      ctx.setLineDash([])

      const arrowSize = isHighlighted ? 10 : 8
      const angle = Math.atan2(endY - cp2y, endX - cp2x)

      ctx.beginPath()
      ctx.moveTo(endX, endY)
      ctx.lineTo(endX - arrowSize * Math.cos(angle - Math.PI / 6), endY - arrowSize * Math.sin(angle - Math.PI / 6))
      ctx.lineTo(endX - arrowSize * Math.cos(angle + Math.PI / 6), endY - arrowSize * Math.sin(angle + Math.PI / 6))
      ctx.closePath()
      ctx.fillStyle = isHighlighted ? toConfig.color : "oklch(0.85 0.03 250)"
      ctx.fill()

      const t = 0.5
      const midX =
        Math.pow(1 - t, 3) * startX +
        3 * Math.pow(1 - t, 2) * t * cp1x +
        3 * (1 - t) * Math.pow(t, 2) * cp2x +
        Math.pow(t, 3) * endX
      const midY =
        Math.pow(1 - t, 3) * startY +
        3 * Math.pow(1 - t, 2) * t * cp1y +
        3 * (1 - t) * Math.pow(t, 2) * cp2y +
        Math.pow(t, 3) * endY

      const padding = 6
      const textWidth = ctx.measureText(edge.label).width
      ctx.fillStyle = "oklch(1 0 0)"
      ctx.shadowColor = "rgba(0, 0, 0, 0.1)"
      ctx.shadowBlur = 4
      ctx.shadowOffsetY = 1
      ctx.beginPath()
      ctx.roundRect(midX - textWidth / 2 - padding, midY - 8, textWidth + padding * 2, 16, 4)
      ctx.fill()
      ctx.shadowBlur = 0
      ctx.shadowOffsetY = 0

      ctx.fillStyle = isHighlighted ? fromConfig.color : "oklch(0.5 0.05 250)"
      ctx.font = "600 11px Geist"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText(edge.label, midX, midY)

      edgeHitAreasRef.current.push({
        id: edge.id,
        x: midX - textWidth / 2 - padding,
        y: midY - 8,
        width: textWidth + padding * 2,
        height: 16,
      })
    })
  }, [graphEdges, graphNodes, hoveredEdge, hoveredNode, renderTrigger, selectedEdge, selectedNode])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!draggedNode || !containerRef.current) return

      const container = containerRef.current
      const rect = container.getBoundingClientRect()
      const x = e.clientX - rect.left - dragOffset.x
      const y = e.clientY - rect.top - dragOffset.y

      setGraphNodes((prevNodes) => {
        const nodeIndex = prevNodes.findIndex((node) => node.id === draggedNode)
        if (nodeIndex === -1) return prevNodes
        const updated = [...prevNodes]
        updated[nodeIndex] = {
          ...updated[nodeIndex],
          x: Math.max(12, Math.min(x, rect.width - layoutConfig.nodeWidth - 12)),
          y: Math.max(12, Math.min(y, rect.height - layoutConfig.nodeHeight - 12)),
        }
        return updated
      })
      setRenderTrigger((prev) => prev + 1)
    }

    const handleMouseUp = () => {
      setDraggedNode(null)
    }

    if (draggedNode) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
    }
  }, [draggedNode, dragOffset])

  const handleNodeClick = (node: Node) => {
    setSelectedNode(node)
    setSelectedEdge(null)
  }

  const findEdgeAt = (x: number, y: number): Edge | null => {
    const hit = edgeHitAreasRef.current.find(
      (area) => x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height
    )
    if (!hit) return null
    return graphEdges.find((edge) => edge.id === hit.id) || null
  }

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const hitEdge = findEdgeAt(x, y)
    if (hitEdge) {
      setSelectedEdge(hitEdge)
      setSelectedNode(null)
    }
  }

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const hitEdge = findEdgeAt(x, y)
    setHoveredEdge(hitEdge?.id ?? null)
  }

  const handleNodeMouseDown = (e: React.MouseEvent, node: Node) => {
    e.stopPropagation()
    if (!containerRef.current) return

    const container = containerRef.current
    const rect = container.getBoundingClientRect()
    const offsetX = e.clientX - rect.left - node.x
    const offsetY = e.clientY - rect.top - node.y

    setDragOffset({ x: offsetX, y: offsetY })
    setDraggedNode(node.id)
  }

  const getRelatedNodes = (nodeId: string): string[] => {
    const related = new Set<string>()
    graphEdges.forEach((edge) => {
      if (edge.from === nodeId) related.add(edge.to)
      if (edge.to === nodeId) related.add(edge.from)
    })
    return Array.from(related)
  }

  const stats = useMemo(
    () => ({
      nodes: graphNodes.length,
      edges: graphEdges.length,
    }),
    [graphNodes.length, graphEdges.length]
  )

  return (
    <div className="flex gap-4">
      <Card className="flex-1 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b bg-white/80 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="text-sm font-semibold text-foreground">数据血缘图</div>
            <div className="text-xs text-muted-foreground">
              {stats.nodes} 个节点 · {stats.edges} 条边
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: nodeConfig.datasource.color }} />
              数据源
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: nodeConfig.dataset.color }} />
              数据集
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: nodeConfig.model.color }} />
              模型
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: nodeConfig.knowledge.color }} />
              知识库
            </span>
          </div>
        </div>
        <div
          ref={containerRef}
          className="relative overflow-auto"
          style={{
            height: "calc(100vh - 244px)",
            backgroundImage:
              "radial-gradient(circle at 1px 1px, oklch(0.88 0.01 250) 1px, transparent 0)",
            backgroundSize: "18px 18px",
          }}
          onClick={() => {
            setSelectedNode(null)
            setSelectedEdge(null)
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-background/80 via-transparent to-muted/30 pointer-events-none" />
          <canvas
            ref={canvasRef}
            className="absolute inset-0"
            style={{
              width: `${layoutConfig.canvasWidth}px`,
              height: `${layoutConfig.canvasHeight}px`,
              cursor: hoveredEdge ? "pointer" : "default",
            }}
            onClick={(e) => {
              e.stopPropagation()
              handleCanvasClick(e)
            }}
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={() => setHoveredEdge(null)}
          />

          {graphNodes.length === 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
              <div className="text-sm">暂无血缘数据</div>
              <div className="text-xs mt-2">完成归集或关联流程后将自动生成血缘图</div>
            </div>
          )}

          {graphNodes.map((node) => {
            const config = nodeConfig[node.type]
            const Icon = config.icon
            const isSelected = selectedNode?.id === node.id
            const isHovered = hoveredNode === node.id
            const relatedNodes = selectedNode ? getRelatedNodes(selectedNode.id) : []
            const isRelated = selectedNode && relatedNodes.includes(node.id)
            const isDimmed = selectedNode && selectedNode.id !== node.id && !isRelated

            return (
              <div
                key={node.id}
                className="absolute transition-all duration-300 cursor-move select-none"
                style={{
                  left: `${node.x}px`,
                  top: `${node.y}px`,
                  opacity: isDimmed ? 0.3 : 1,
                  transform: isHovered || isSelected ? "scale(1.05)" : "scale(1)",
                  filter: isHovered || isSelected ? "drop-shadow(0 4px 12px rgba(0,0,0,0.15))" : "none",
                }}
                onClick={(e) => {
                  e.stopPropagation()
                  handleNodeClick(node)
                }}
                onMouseDown={(e) => handleNodeMouseDown(e, node)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                <div
                  className="relative flex items-center gap-3 px-4 py-3 rounded-2xl border-2 bg-white/90 backdrop-blur transition-all duration-300 overflow-hidden"
                  style={{
                    width: `${layoutConfig.nodeWidth}px`,
                    borderColor: isSelected || isRelated ? config.color : "oklch(0.9 0 0)",
                    boxShadow: isSelected
                      ? `0 8px 24px ${config.color}30, 0 0 0 4px ${config.color}15`
                      : isHovered
                        ? "0 4px 16px rgba(0,0,0,0.12)"
                        : "0 2px 8px rgba(0,0,0,0.06)",
                  }}
                >
                  <div
                    className="absolute inset-0 opacity-5 transition-opacity duration-300"
                    style={{
                      background: `linear-gradient(135deg, ${config.color} 0%, transparent 100%)`,
                      opacity: isHovered || isSelected ? 0.08 : 0.03,
                    }}
                  />

                  <div
                    className="relative p-2 rounded-lg transition-all duration-300"
                    style={{
                      backgroundColor: config.bgColor,
                      transform: isHovered ? "rotate(5deg) scale(1.1)" : "rotate(0deg) scale(1)",
                    }}
                  >
                    <Icon className="w-5 h-5 transition-transform duration-300" style={{ color: config.color }} />
                  </div>

                  <div className="relative min-w-[100px]">
                    <div className="text-sm font-semibold text-foreground whitespace-nowrap">{node.label}</div>
                    {node.status && (
                      <div className="flex items-center gap-1.5 mt-1">
                        <div
                          className="w-2 h-2 rounded-full animate-pulse"
                          style={{
                            backgroundColor: node.status === "运转" ? "oklch(0.6 0.2 140)" : "oklch(0.7 0.2 40)",
                          }}
                        />
                        <span className="text-xs text-muted-foreground">{node.status}</span>
                      </div>
                    )}
                    {node.fileCount !== undefined && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {node.fileCount} 个文件 · {node.size}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {selectedNode && (
        <Card
          className="w-80 border-2 shadow-lg animate-in slide-in-from-right duration-300"
          style={{
            borderColor: nodeConfig[selectedNode.type].color,
            height: "calc(100vh - 200px)",
          }}
        >
          <div className="h-full flex flex-col">
            <div
              className="flex items-start justify-between p-4 border-b"
              style={{ backgroundColor: nodeConfig[selectedNode.type].bgColor }}
            >
              <div className="flex items-start gap-3 flex-1">
                <div className="p-2 rounded-lg" style={{ backgroundColor: nodeConfig[selectedNode.type].color }}>
                  {(() => {
                    const Icon = nodeConfig[selectedNode.type].icon
                    return <Icon className="w-5 h-5 text-white" />
                  })()}
                </div>
                <div className="space-y-1 flex-1 min-w-0">
                  <h3 className="text-base font-semibold text-balance">{selectedNode.label}</h3>
                  <Badge
                    variant="outline"
                    className="text-xs"
                    style={{
                      borderColor: nodeConfig[selectedNode.type].color,
                      color: nodeConfig[selectedNode.type].color,
                    }}
                  >
                    {selectedNode.type === "datasource" && "数据源"}
                    {selectedNode.type === "dataset" && "数据集"}
                    {selectedNode.type === "model" && "模型"}
                    {selectedNode.type === "knowledge" && "知识库"}
                  </Badge>
                </div>
              </div>
              <button
                className="h-8 w-8 -mt-1 -mr-1 flex-shrink-0 flex items-center justify-center rounded-md bg-white hover:bg-gray-100 border border-gray-200 shadow-sm transition-colors"
                onClick={() => setSelectedNode(null)}
              >
                <X className="w-4 h-4 text-gray-700" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-4 space-y-4">
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">基本信息</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1.5 border-b">
                    <span className="text-muted-foreground">ID:</span>
                    <span className="font-mono text-xs">{selectedNode.id}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b">
                    <span className="text-muted-foreground">名称:</span>
                    <span>{selectedNode.label}</span>
                  </div>
                  {selectedNode.status && (
                    <div className="flex justify-between py-1.5 border-b">
                      <span className="text-muted-foreground">状态:</span>
                      <span className="flex items-center gap-1.5">
                        <div
                          className="w-2 h-2 rounded-full animate-pulse"
                          style={{
                            backgroundColor:
                              selectedNode.status === "运转" ? "oklch(0.6 0.2 140)" : "oklch(0.7 0.2 40)",
                          }}
                        />
                        {selectedNode.status}
                      </span>
                    </div>
                  )}
                  {selectedNode.fileCount !== undefined && (
                    <div className="flex justify-between py-1.5 border-b">
                      <span className="text-muted-foreground">文件数:</span>
                      <span>{selectedNode.fileCount}</span>
                    </div>
                  )}
                  {selectedNode.size && (
                    <div className="flex justify-between py-1.5 border-b">
                      <span className="text-muted-foreground">数据大小:</span>
                      <span>{selectedNode.size}</span>
                    </div>
                  )}
                  {selectedNode.updateTime && (
                    <div className="flex justify-between py-1.5 border-b">
                      <span className="text-muted-foreground">更新时间:</span>
                      <span className="text-xs">{selectedNode.updateTime}</span>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">描述</h4>
                <p className="text-sm text-muted-foreground">{selectedNode.description}</p>
              </div>

              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">上游依赖</h4>
                <div className="space-y-1.5">
                  {graphEdges
                    .filter((e) => e.to === selectedNode.id)
                    .map((e) => {
                      const fromNode = graphNodes.find((n) => n.id === e.from)
                      return fromNode ? (
                        <div
                          key={e.from}
                          className="flex items-center gap-2 p-2 rounded-md bg-muted/50 hover:bg-muted transition-colors cursor-pointer"
                        >
                          <div
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: nodeConfig[fromNode.type].color }}
                          />
                          <span className="text-sm flex-1 truncate">{fromNode.label}</span>
                        </div>
                      ) : null
                    })}
                  {graphEdges.filter((e) => e.to === selectedNode.id).length === 0 && (
                    <p className="text-sm text-muted-foreground">无上游依赖</p>
                  )}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">下游影响</h4>
                <div className="space-y-1.5">
                  {graphEdges
                    .filter((e) => e.from === selectedNode.id)
                    .map((e) => {
                      const toNode = graphNodes.find((n) => n.id === e.to)
                      return toNode ? (
                        <div
                          key={e.to}
                          className="flex items-center gap-2 p-2 rounded-md bg-muted/50 hover:bg-muted transition-colors cursor-pointer"
                        >
                          <div
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: nodeConfig[toNode.type].color }}
                          />
                          <span className="text-sm flex-1 truncate">{toNode.label}</span>
                        </div>
                      ) : null
                    })}
                  {graphEdges.filter((e) => e.from === selectedNode.id).length === 0 && (
                    <p className="text-sm text-muted-foreground">无下游影响</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {!selectedNode && selectedEdge && (
        <Card
          className="w-80 border-2 shadow-lg animate-in slide-in-from-right duration-300"
          style={{
            borderColor: "oklch(0.6 0.05 250)",
            height: "calc(100vh - 200px)",
          }}
        >
          <div className="h-full flex flex-col">
            <div className="flex items-start justify-between p-4 border-b bg-muted/40">
              <div className="space-y-1 flex-1 min-w-0">
                <h3 className="text-base font-semibold text-balance">流程详情</h3>
                <Badge variant="outline" className="text-xs text-muted-foreground">
                  {selectedEdge.edgeType
                    ? edgeTypeLabels[selectedEdge.edgeType] || selectedEdge.edgeType
                    : "处理流程"}
                </Badge>
              </div>
              <button
                className="h-8 w-8 -mt-1 -mr-1 flex-shrink-0 flex items-center justify-center rounded-md bg-white hover:bg-gray-100 border border-gray-200 shadow-sm transition-colors"
                onClick={() => setSelectedEdge(null)}
              >
                <X className="w-4 h-4 text-gray-700" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4 space-y-4">
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">基本信息</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1.5 border-b">
                    <span className="text-muted-foreground">ID:</span>
                    <span className="font-mono text-xs">{selectedEdge.id}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b">
                    <span className="text-muted-foreground">名称:</span>
                    <span>{selectedEdge.label}</span>
                  </div>
                  {selectedEdge.processId && (
                    <div className="flex justify-between py-1.5 border-b">
                      <span className="text-muted-foreground">流程ID:</span>
                      <span className="font-mono text-xs">{selectedEdge.processId}</span>
                    </div>
                  )}
                </div>
              </div>
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">上下游关系</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1.5 border-b">
                    <span className="text-muted-foreground">上游:</span>
                    <span>{graphNodes.find((n) => n.id === selectedEdge.from)?.label || selectedEdge.from}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b">
                    <span className="text-muted-foreground">下游:</span>
                    <span>{graphNodes.find((n) => n.id === selectedEdge.to)?.label || selectedEdge.to}</span>
                  </div>
                </div>
              </div>
              {selectedEdge.description && (
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground mb-2">描述</h4>
                  <p className="text-sm text-muted-foreground">{selectedEdge.description}</p>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
