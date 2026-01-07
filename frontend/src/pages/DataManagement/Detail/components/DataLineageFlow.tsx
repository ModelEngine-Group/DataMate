import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Card, Badge } from "antd"
import { Database, Table, Brain, BookOpen, X } from "lucide-react"
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts"

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
  from: string
  to: string
  label: string
}

const nodes: Node[] = [
  {
    id: "source1",
    type: "datasource",
    label: "MySQL 数据库",
    x: 80,
    y: 100,
    description: "业务数据库",
    status: "运转",
    updateTime: "2026-01-06 15:22:08",
  },
  {
    id: "source2",
    type: "datasource",
    label: "API 接口",
    x: 80,
    y: 250,
    description: "外部数据源",
    status: "运转",
    updateTime: "2026-01-06 14:30:15",
  },
  {
    id: "source3",
    type: "datasource",
    label: "日志文件",
    x: 80,
    y: 400,
    description: "系统日志",
    status: "运转",
    updateTime: "2026-01-06 16:05:42",
  },
  {
    id: "dataset1",
    type: "dataset",
    label: "原始数据集",
    x: 380,
    y: 100,
    description: "未处理的原始数据",
    fileCount: 14,
    size: "3.449 MB",
    updateTime: "2026-01-06 15:22:08",
  },
  {
    id: "dataset2",
    type: "dataset",
    label: "清洗数据集",
    x: 680,
    y: 175,
    description: "清洗后的干净数据",
    fileCount: 8,
    size: "2.156 MB",
    updateTime: "2026-01-06 15:45:20",
  },
  {
    id: "dataset3",
    type: "dataset",
    label: "合成数据集",
    x: 980,
    y: 250,
    description: "特征工程后的数据",
    fileCount: 5,
    size: "1.823 MB",
    updateTime: "2026-01-06 16:10:35",
  },
  {
    id: "model1",
    type: "model",
    label: "预测模型",
    x: 1280,
    y: 150,
    description: "ML 预测模型",
    status: "训练中",
    updateTime: "2026-01-06 16:30:12",
  },
  {
    id: "model2",
    type: "model",
    label: "分类模型",
    x: 1280,
    y: 350,
    description: "分类算法模型",
    status: "已完成",
    updateTime: "2026-01-06 16:25:48",
  },
  {
    id: "kb1",
    type: "knowledge",
    label: "业务知识库",
    x: 1600,
    y: 250,
    description: "结构化知识存储",
    fileCount: 32,
    size: "8.742 MB",
    updateTime: "2026-01-06 16:45:05",
  },
]

const edges: Edge[] = [
  { from: "source1", to: "dataset1", label: "数据归集" },
  { from: "source2", to: "dataset1", label: "数据归集" },
  { from: "source3", to: "dataset1", label: "数据归集" },
  { from: "dataset1", to: "dataset2", label: "数据清洗" },
  { from: "dataset2", to: "dataset3", label: "数据合成" },
  { from: "dataset2", to: "kb1", label: "知识生成" },
  { from: "dataset3", to: "model1", label: "模型训练" },
  { from: "dataset3", to: "model2", label: "模型训练" },
]

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

export default function DataLineageFlow(dataset: Dataset) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [draggedNode, setDraggedNode] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [renderTrigger, setRenderTrigger] = useState(0)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

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

    edges.forEach((edge) => {
      const fromNode = nodes.find((n) => n.id === edge.from)
      const toNode = nodes.find((n) => n.id === edge.to)
      if (!fromNode || !toNode) return

      const isHighlighted =
        hoveredNode === edge.from ||
        hoveredNode === edge.to ||
        selectedNode?.id === edge.from ||
        selectedNode?.id === edge.to

      const startX = fromNode.x + 140
      const startY = fromNode.y + 35
      const endX = toNode.x
      const endY = toNode.y + 35

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
    })
  }, [hoveredNode, renderTrigger, selectedNode])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!draggedNode || !containerRef.current) return

      const container = containerRef.current
      const rect = container.getBoundingClientRect()
      const x = e.clientX - rect.left - dragOffset.x
      const y = e.clientY - rect.top - dragOffset.y

      const nodeIndex = nodes.findIndex((n) => n.id === draggedNode)
      if (nodeIndex !== -1) {
        nodes[nodeIndex].x = Math.max(0, Math.min(x, rect.width - 120))
        nodes[nodeIndex].y = Math.max(0, Math.min(y, rect.height - 70))
        setRenderTrigger((prev) => prev + 1)
      }
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
    edges.forEach((edge) => {
      if (edge.from === nodeId) related.add(edge.to)
      if (edge.to === nodeId) related.add(edge.from)
    })
    return Array.from(related)
  }

  return (
    <div className="flex gap-4">
      <Card className="flex-1 overflow-hidden">
        <div
          ref={containerRef}
          className="relative bg-gradient-to-br from-background via-background to-muted/20 overflow-auto"
          style={{ height: "calc(100vh - 200px)" }}
        >
          <canvas ref={canvasRef} className="absolute inset-0" style={{ width: "1900px", height: "600px" }} />

          {nodes.map((node) => {
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
                onClick={() => handleNodeClick(node)}
                onMouseDown={(e) => handleNodeMouseDown(e, node)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                <div
                  className="relative flex items-center gap-3 px-4 py-3 rounded-xl border-2 bg-background transition-all duration-300 overflow-hidden"
                  style={{
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
                  {edges
                    .filter((e) => e.to === selectedNode.id)
                    .map((e) => {
                      const fromNode = nodes.find((n) => n.id === e.from)
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
                  {edges.filter((e) => e.to === selectedNode.id).length === 0 && (
                    <p className="text-sm text-muted-foreground">无上游依赖</p>
                  )}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">下游影响</h4>
                <div className="space-y-1.5">
                  {edges
                    .filter((e) => e.from === selectedNode.id)
                    .map((e) => {
                      const toNode = nodes.find((n) => n.id === e.to)
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
                  {edges.filter((e) => e.from === selectedNode.id).length === 0 && (
                    <p className="text-sm text-muted-foreground">无下游影响</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
