"use client"

import type React from "react"
import { useState, useCallback } from "react"
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  type Connection,
  type Node,
  type NodeTypes,
  BackgroundVariant,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { Card, Button, Input, Badge, Tabs, Switch, Divider, Select } from "antd"
import TextArea from "antd/es/input/TextArea"
import {
  Play,
  Save,
  ArrowLeft,
  Database,
  Trash2,
  Copy,
  Search,
  Plus,
  Clock,
  Zap,
  BarChart3,
  Brain,
  FileText,
  Target,
  Sparkles,
  Settings,
  Filter,
  BookOpen,
  TrendingUp,
  GitBranch,
  Eye,
  CheckCircle,
  AlertCircle,
  PlayCircle,
  Code,
} from "lucide-react"

interface NodeConfig {
  name: string
  description: string
  pythonCode: string
  // Removed schedule from NodeConfig interface
}

// Removed all specific config interfaces
// Removed DataCollectionConfig, DataCleaningConfig, DataRatioConfig, KnowledgeGenerationConfig, ModelTrainingConfig, ModelReportConfig

const SmartOrchestrationNode = ({ data, selected }: { data: any; selected: boolean }) => {
  const [isHovered, setIsHovered] = useState(false)

  const getNodeIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      "data-collection": <Database className="w-5 h-5" />,
      "data-cleaning": <Filter className="w-5 h-5" />,
      "data-ratio": <BarChart3 className="w-5 h-5" />,
      "knowledge-generation": <Brain className="w-5 h-5" />,
      "model-training": <Target className="w-5 h-5" />,
      "model-report": <FileText className="w-5 h-5" />,
    }
    return icons[type] || <Settings className="w-5 h-5" />
  }

  const getNodeColor = (type: string) => {
    const colors: Record<string, { bg: string; border: string; icon: string }> = {
      "data-collection": { bg: "bg-blue-50", border: "border-blue-300", icon: "text-blue-600" },
      "data-cleaning": { bg: "bg-green-50", border: "border-green-300", icon: "text-green-600" },
      "data-ratio": { bg: "bg-purple-50", border: "border-purple-300", icon: "text-purple-600" },
      "knowledge-generation": { bg: "bg-orange-50", border: "border-orange-300", icon: "text-orange-600" },
      "model-training": { bg: "bg-red-50", border: "border-red-300", icon: "text-red-600" },
      "model-report": { bg: "bg-cyan-50", border: "border-cyan-300", icon: "text-cyan-600" },
    }
    return colors[type] || { bg: "bg-gray-50", border: "border-gray-300", icon: "text-gray-600" }
  }

  const nodeColor = getNodeColor(data.type)

  return (
    <div className="relative" onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
      {/* Connection handles */}
      {(selected || isHovered) && (
        <>
          <Handle
            type="target"
            position={Position.Left}
            className="w-3 h-3 bg-green-500 border-2 border-white shadow-md hover:scale-110 transition-transform"
            style={{ left: -6 }}
          />
          <Handle
            type="source"
            position={Position.Right}
            className="w-3 h-3 bg-blue-500 border-2 border-white shadow-md hover:scale-110 transition-transform"
            style={{ right: -6 }}
          />
        </>
      )}

      <Card
        className={`w-80 border-2 ${nodeColor.border} transition-all duration-200 ${
          selected ? "ring-2 ring-blue-500 shadow-xl" : "shadow-md hover:shadow-lg"
        }`}
      >
        <div className={`pb-3 ${nodeColor.bg} border-b p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 ${nodeColor.bg} rounded-lg flex items-center justify-center border ${nodeColor.border}`}
              >
                <div className={nodeColor.icon}>{getNodeIcon(data.type)}</div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{data.name}</h3>
                <p className="text-xs text-gray-600">{data.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                type="text"
                size="small"
                onClick={(e: any) => {
                  e.stopPropagation()
                  data.onDuplicate?.(data.id)
                }}
                className="h-7 w-7 p-0"
                icon={<Copy className="w-3.5 h-3.5" />}
              />
              <Button
                type="text"
                size="small"
                onClick={(e: any) => {
                  e.stopPropagation()
                  data.onDelete?.(data.id)
                }}
                className="h-7 w-7 p-0 hover:text-red-600"
                icon={<Trash2 className="w-3.5 h-3.5" />}
                danger
              />
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">状态</span>
              <Badge color={data.config?.enabled ? "blue" : "default"} className="text-xs">
                {data.config?.enabled ? "已启用" : "已禁用"}
              </Badge>
            </div>
            <div className="pt-2 border-t">
              <span className="text-xs text-gray-500">点击节点查看详细配置</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

const nodeTypes: NodeTypes = {
  smartNode: SmartOrchestrationNode,
}

const nodeTemplates = [
  {
    type: "data-collection",
    name: "数据归集",
    description: "从多种数据源收集和同步数据",
    icon: Database,
    category: "数据源",
    // Removed defaultConfig, replaced by defaultConfigs object later
  },
  {
    type: "data-cleaning",
    name: "数据清洗",
    description: "清洗和预处理数据",
    icon: Filter,
    category: "数据处理",
    // Removed defaultConfig
  },
  {
    type: "data-ratio",
    name: "数据配比",
    description: "划分训练集、验证集和测试集",
    icon: BarChart3,
    category: "数据处理",
    // Removed defaultConfig
  },
  {
    type: "knowledge-generation",
    name: "知识生成",
    description: "生成知识库和向量化",
    icon: Brain,
    category: "知识处理",
    // Removed defaultConfig
  },
  {
    type: "model-training",
    name: "模型训练",
    description: "训练机器学习模型",
    icon: Target,
    category: "模型",
    // Removed defaultConfig
  },
  {
    type: "model-report",
    name: "模型报告",
    description: "生成模型评估报告",
    icon: FileText,
    category: "输出",
    // Removed defaultConfig
  },
]

const workflowTemplates = [
  {
    id: "data-flywheel",
    name: "数据飞轮 - 持续学习流程",
    description: "自动化数据收集、清洗、训练的持续学习循环",
    category: "智能学习",
    icon: <TrendingUp className="w-5 h-5" />,
    schedule: "0 0 */6 * * ?", // Every 6 hours
    nodes: [
      { type: "data-collection", position: { x: 100, y: 200 } },
      { type: "data-cleaning", position: { x: 450, y: 200 } },
      { type: "data-ratio", position: { x: 800, y: 200 } },
      { type: "model-training", position: { x: 1150, y: 200 } },
      { type: "model-report", position: { x: 1500, y: 200 } },
    ],
  },
  {
    id: "knowledge-pipeline",
    name: "知识库构建流程",
    description: "秒级知识库检索和更新流程",
    category: "知识管理",
    icon: <BookOpen className="w-5 h-5" />,
    schedule: "*/30 * * * * ?", // Every 30 seconds
    nodes: [
      { type: "data-collection", position: { x: 100, y: 200 } },
      { type: "data-cleaning", position: { x: 450, y: 200 } },
      { type: "knowledge-generation", position: { x: 800, y: 200 } },
    ],
  },
  {
    id: "full-pipeline",
    name: "完整AI流程",
    description: "从数据收集到模型报告的完整流程",
    category: "综合",
    icon: <GitBranch className="w-5 h-5" />,
    schedule: "0 0 0 * * ?", // Daily at midnight
    nodes: [
      { type: "data-collection", position: { x: 100, y: 150 } },
      { type: "data-cleaning", position: { x: 450, y: 150 } },
      { type: "data-ratio", position: { x: 800, y: 50 } },
      { type: "knowledge-generation", position: { x: 800, y: 250 } },
      { type: "model-training", position: { x: 1150, y: 150 } },
      { type: "model-report", position: { x: 1500, y: 150 } },
    ],
  },
]

const mockExecutions = [
  {
    id: 1,
    workflowName: "数据飞轮 - 持续学习流程",
    status: "running",
    startTime: "2025-11-26 14:30:00",
    progress: 60,
    currentNode: "model-training",
  },
  {
    id: 2,
    workflowName: "知识库构建流程",
    status: "success",
    startTime: "2025-11-26 14:28:30",
    endTime: "2025-11-26 14:29:15",
    duration: "45s",
  },
  {
    id: 3,
    workflowName: "完整AI流程",
    status: "failed",
    startTime: "2025-11-26 12:00:00",
    endTime: "2025-11-26 12:15:32",
    duration: "15m 32s",
    error: "数据清洗节点执行失败: 字段格式错误",
  },
]

interface SmartOrchestrationProps {
  onBack?: () => void
}

export default function SmartOrchestrationPage({ onBack }: SmartOrchestrationProps) {
  const [view, setView] = useState<"list" | "editor" | "execution">("list")
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(null)
  const [workflow, setWorkflow] = useState({
    id: Date.now(),
    name: "新建流程",
    description: "",
    category: "自定义",
    schedule: {
      enabled: false,
      cronExpression: "0 0 * * * ?",
      timezone: "Asia/Shanghai",
      triggerType: "manual" as "manual" | "schedule" | "api",
    },
  })

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([])
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  const filteredTemplates = nodeTemplates.filter(
    (t) =>
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.description.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const onConnect = useCallback(
    (params: Connection) => {
      if (params.source === params.target) return

      const newEdge = {
        ...params,
        id: `edge-${params.source}-${params.target}-${Date.now()}`,
        type: "smoothstep",
        animated: true,
        style: { stroke: "#3b82f6", strokeWidth: 2 },
        markerEnd: { type: "arrowclosed" as const, color: "#3b82f6" },
      }

      setEdges((eds) => addEdge(newEdge, eds))
    },
    [setEdges],
  )

  const deleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId))
      setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId))
    },
    [setNodes, setEdges],
  )

  const duplicateNode = useCallback(
    (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId)
      if (!node) return

      const newNode: Node = {
        ...node,
        id: `${node.data.type}_${Date.now()}`,
        position: { x: node.position.x + 50, y: node.position.y + 50 },
        data: { ...node.data, id: `${node.data.type}_${Date.now()}` },
      }

      setNodes((nds) => [...nds, newNode])
    },
    [nodes, setNodes],
  )

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData("application/reactflow", nodeType)
    event.dataTransfer.effectAllowed = "move"
  }

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()

      const type = event.dataTransfer.getData("application/reactflow")
      if (!type) return

      const position = { x: event.clientX - 400, y: event.clientY - 100 }
      const template = nodeTemplates.find((t) => t.type === type)
      if (!template) return

      // Find the default config from the new defaultConfigs object
      const defaultConfig = defaultConfigs[type]
      if (!defaultConfig) return // Should not happen if template exists

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type: "smartNode",
        position,
        data: {
          id: `${type}_${Date.now()}`,
          type,
          name: template.name,
          description: template.description,
          config: { ...defaultConfig }, // Use default config from the new object
          onDelete: deleteNode,
          onDuplicate: duplicateNode,
        },
      }

      setNodes((nds) => [...nds, newNode])
    },
    [setNodes, deleteNode, duplicateNode],
  )

  const loadTemplate = (templateId: string) => {
    const template = workflowTemplates.find((t) => t.id === templateId)
    if (!template) return

    const newNodes: Node[] = template.nodes
      .map((nodeSpec, index) => {
        const nodeTemplate = nodeTemplates.find((t) => t.type === nodeSpec.type)
        if (!nodeTemplate) return null

        // Find the default config from the new defaultConfigs object
        const defaultConfig = defaultConfigs[nodeSpec.type]
        if (!defaultConfig) return null // Should not happen

        return {
          id: `${nodeSpec.type}_${Date.now()}_${index}`,
          type: "smartNode",
          position: nodeSpec.position,
          data: {
            id: `${nodeSpec.type}_${Date.now()}_${index}`,
            type: nodeSpec.type,
            name: nodeTemplate.name,
            description: nodeTemplate.description,
            config: { ...defaultConfig }, // Use default config from the new object
            onDelete: deleteNode,
            onDuplicate: duplicateNode,
          },
        }
      })
      .filter(Boolean) as Node[]

    // Connect nodes sequentially
    const newEdges = newNodes.slice(0, -1).map((node, index) => ({
      id: `edge-${node.id}-${newNodes[index + 1].id}`,
      source: node.id,
      target: newNodes[index + 1].id,
      type: "smoothstep",
      animated: true,
      style: { stroke: "#3b82f6", strokeWidth: 2 },
      markerEnd: { type: "arrowclosed" as const, color: "#3b82f6" },
    }))

    setNodes(newNodes)
    setEdges(newEdges)
    setWorkflow((prev) => ({
      ...prev,
      name: template.name,
      description: template.description,
      category: template.category,
      schedule: {
        ...prev.schedule,
        enabled: true,
        cronExpression: template.schedule,
        triggerType: "schedule",
      },
    }))
    setView("editor")
  }

  const handleSave = () => {
    console.log("[v0] Saving workflow:", { workflow, nodes, edges })
    // Save logic here
    setView("list")
  }

  const handleBack = () => {
    if (view === "editor" || view === "execution") {
      setView("list")
    } else {
      onBack?.()
    }
  }

  const handleRunWorkflow = () => {
    console.log("[v0] Running workflow:", { workflow, nodes, edges })
    // Here you would trigger the workflow execution
  }

  const selectedNode = selectedNodeId ? nodes.find((n) => n.id === selectedNodeId) : null

  if (view === "execution") {
    return <ExecutionDetailView executionId={selectedExecutionId!} onBack={handleBack} />
  }

  if (view === "list") {
    return (
      <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">数据智能编排</h1>
            <p className="text-gray-600 mt-2">可视化设计和管理数据处理流程，支持定时调度和实时触发</p>
          </div>
          <div className="flex gap-2">
            {onBack && (
              <Button type="default" onClick={onBack} icon={<ArrowLeft className="w-4 h-4" />}>
                返回
              </Button>
            )}
            <Button onClick={() => setView("editor")} icon={<Plus className="w-4 h-4" />}>
              新建流程
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <GitBranch className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">12</p>
                <p className="text-sm text-gray-500">活跃流程</p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">156</p>
                <p className="text-sm text-gray-500">成功执行</p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">3</p>
                <p className="text-sm text-gray-500">运行中</p>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">8</p>
                <p className="text-sm text-gray-500">定时任务</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Workflow Templates */}
        <Card>
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-orange-600" />
              流程模板
            </h2>
            <p className="text-sm text-gray-500 mt-1">快速开始，使用预定义的流程模板</p>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {workflowTemplates.map((template) => (
                <Card key={template.id} className="hover:shadow-lg transition-shadow cursor-pointer border-2">
                  <div className="pt-6 p-4">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white">
                          {template.icon}
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{template.name}</h3>
                          <Badge color="default" className="mt-1 text-xs">
                            {template.category}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{template.description}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 p-2 rounded">
                        <Clock className="w-3.5 h-3.5" />
                        <span className="font-mono">{template.schedule}</span>
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t">
                        <span className="text-xs text-gray-500">{template.nodes.length} 个节点</span>
                        <Button size="small" onClick={() => loadTemplate(template.id)} icon={<Play className="w-3.5 h-3.5" />}>
                          使用模板
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-blue-600" />
              执行历史
            </h2>
            <p className="text-sm text-gray-500 mt-1">查看流程执行记录和运行状态</p>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {mockExecutions.map((execution) => (
                <Card
                  key={execution.id}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => {
                    setSelectedExecutionId(execution.id)
                    setView("execution")
                  }}
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-gray-900">{execution.workflowName}</h3>
                          <Badge
                            color={
                              execution.status === "success"
                                ? "green"
                                : execution.status === "running"
                                  ? "blue"
                                  : "red"
                            }
                          >
                            {execution.status === "success"
                              ? "成功"
                              : execution.status === "running"
                                ? "运行中"
                                : "失败"}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                          <span>开始时间: {execution.startTime}</span>
                          {execution.duration && <span>耗时: {execution.duration}</span>}
                        </div>
                        {execution.status === "running" && (
                          <div className="mt-3">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs text-gray-500">进度: {execution.progress}%</span>
                              <span className="text-xs text-gray-500">当前: {execution.currentNode}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${execution.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                        {execution.error && (
                          <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700 flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                            <span>{execution.error}</span>
                          </div>
                        )}
                      </div>
                      <Button type="default" size="small" icon={<Eye className="w-4 h-4" />}>
                        查看详情
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-50 bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button type="text" size="small" onClick={handleBack} icon={<ArrowLeft className="w-4 h-4" />}>
              返回
            </Button>
            <Divider type="vertical" className="h-6" />
            <div>
              <Input
                value={workflow.name}
                onChange={(e) => setWorkflow((prev) => ({ ...prev, name: e.target.value }))}
                className="text-lg font-semibold border-none p-0 h-auto bg-transparent focus-visible:ring-0"
              />
              <Input
                value={workflow.description}
                onChange={(e) => setWorkflow((prev) => ({ ...prev, description: e.target.value }))}
                className="text-sm text-gray-600 border-none p-0 h-auto bg-transparent focus-visible:ring-0 mt-1"
                placeholder="流程描述"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-gray-100 px-3 py-2 rounded-lg">
              <Clock className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-600">定时调度</span>
              <Switch
                checked={workflow.schedule.enabled}
                onChange={(checked) =>
                  setWorkflow((prev) => ({ ...prev, schedule: { ...prev.schedule, enabled: checked } }))
                }
              />
            </div>
            <Button type="default" size="small" onClick={handleRunWorkflow} icon={<Play className="w-4 h-4" />}>
              运行
            </Button>
            <Button size="small" onClick={handleSave} icon={<Save className="w-4 h-4" />}>
              保存
            </Button>
          </div>
        </div>

        {workflow.schedule.enabled && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-xs block mb-1">触发方式</label>
                <Select
                  value={workflow.schedule.triggerType}
                  onChange={(value: any) =>
                    setWorkflow((prev) => ({ ...prev, schedule: { ...prev.schedule, triggerType: value } }))
                  }
                  style={{ width: '100%' }}
                >
                  <Select.Option value="manual">手动触发</Select.Option>
                  <Select.Option value="schedule">定时调度</Select.Option>
                  <Select.Option value="api">API触发</Select.Option>
                </Select>
              </div>
              {workflow.schedule.triggerType === "schedule" && (
                <>
                  <div>
                    <label className="text-xs block mb-1">Cron 表达式</label>
                    <Input
                      value={workflow.schedule.cronExpression}
                      onChange={(e) =>
                        setWorkflow((prev) => ({
                          ...prev,
                          schedule: { ...prev.schedule, cronExpression: e.target.value },
                        }))
                      }
                      className="mt-1 font-mono text-sm"
                      placeholder="0 0 * * * ?"
                    />
                  </div>
                  <div>
                    <label className="text-xs block mb-1">时区</label>
                    <Select
                      value={workflow.schedule.timezone}
                      onChange={(value) =>
                        setWorkflow((prev) => ({ ...prev, schedule: { ...prev.schedule, timezone: value } }))
                      }
                      style={{ width: '100%' }}
                    >
                      <Select.Option value="Asia/Shanghai">Asia/Shanghai</Select.Option>
                      <Select.Option value="UTC">UTC</Select.Option>
                      <Select.Option value="America/New_York">America/New_York</Select.Option>
                    </Select>
                  </div>
                </>
              )}
            </div>
            {workflow.schedule.triggerType === "schedule" && (
              <div className="mt-3 text-xs text-blue-700 space-y-1">
                <p className="font-semibold">常用Cron示例:</p>
                <p>• */30 * * * * ? - 每30秒执行 (秒级知识库检索)</p>
                <p>• 0 */5 * * * ? - 每5分钟执行</p>
                <p>• 0 0 */6 * * ? - 每6小时执行 (数据飞轮)</p>
                <p>• 0 0 0 * * ? - 每天午夜执行</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Node Library Sidebar */}
      <div className="w-80 bg-white border-r flex flex-col mt-20">
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="搜索节点..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <div className="flex-1 overflow-auto">
          <div className="p-4 space-y-3">
            {filteredTemplates.map((template) => (
              <Card
                key={template.type}
                className="cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow border-2"
                draggable
                onDragStart={(e) => onDragStart(e, template.type)}
              >
                <div className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white flex-shrink-0">
                      <template.icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 mb-1">{template.name}</h3>
                      <p className="text-xs text-gray-600 leading-relaxed mb-2">{template.description}</p>
                      <Badge color="default" className="text-xs">
                        {template.category}
                      </Badge>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 mt-20">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
          onPaneClick={() => setSelectedNodeId(null)}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          className="bg-gray-50"
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        </ReactFlow>
      </div>

      {/* Configuration Panel */}
      {selectedNode && (
        <div className="w-96 bg-white border-l mt-20">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">节点配置</h2>
            <p className="text-sm text-gray-600 mt-1">{String(selectedNode.data.name || '')}</p>
          </div>
          <div className="h-full overflow-auto">
            <div className="p-4 space-y-6">
              <Tabs defaultActiveKey="basic" className="w-full">
                <Tabs.TabPane tab="节点配置" key="basic">
                  <div className="space-y-4 mt-4">
                    <NodeConfigPanel node={selectedNode} setNodes={setNodes} />
                  </div>
                </Tabs.TabPane>
              </Tabs>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function NodeConfigPanel({ node, setNodes }: any) {
  const config = node.data.config as NodeConfig

  const getCodeTemplate = (nodeType: string) => {
    const templates: Record<string, string> = {
      "data-collection": `# 数据归集 PythonOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from sqlalchemy import create_engine

def collect_data(**context):
    """
    从数据源采集数据
    """
    # 数据库连接配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'password',
        'database': 'mydb'
    }
    
    # 创建数据库连接
    engine = create_engine(
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    # 增量查询
    execution_date = context['execution_date']
    query = f"""
        SELECT * FROM users 
        WHERE updated_at > '{execution_date}'
        ORDER BY updated_at
    """
    
    # 读取数据
    df = pd.read_sql(query, engine)
    
    # 保存到XCom
    context['ti'].xcom_push(key='collected_data', value=df.to_json())
    
    print(f"[v0] 采集完成，共 {len(df)} 条记录")
    return len(df)

# 创建PythonOperator
data_collection_task = PythonOperator(
    task_id='data_collection',
    python_callable=collect_data,
    provide_context=True,
)`,

      "data-cleaning": `# 数据清洗 PythonOperator
from airflow.operators.python import PythonOperator
import pandas as pd
import json

def clean_data(**context):
    """
    清洗和预处理数据
    """
    # 从上游节点获取数据
    ti = context['ti']
    data_json = ti.xcom_pull(key='collected_data')
    df = pd.read_json(data_json)
    
    # 移除空值
    df = df.dropna(subset=['important_column'])
    
    # 移除重复
    df = df.drop_duplicates(subset=['id'])
    
    # 文本标准化
    df['name'] = df['name'].str.strip().str.lower()
    
    # 数据类型转换
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    
    # 异常值处理
    df = df[(df['age'] > 0) & (df['age'] < 120)]
    
    # 保存清洗后的数据
    ti.xcom_push(key='cleaned_data', value=df.to_json())
    
    print(f"[v0] 清洗完成，保留 {len(df)} 条有效记录")
    return len(df)

# 创建PythonOperator
data_cleaning_task = PythonOperator(
    task_id='data_cleaning',
    python_callable=clean_data,
    provide_context=True,
)`,

      "data-ratio": `# 数据配比 PythonOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from sklearn.model_selection import train_test_split

def split_data(**context):
    """
    按比例划分训练集、验证集、测试集
    """
    # 从上游节点获取数据
    ti = context['ti']
    data_json = ti.xcom_pull(key='cleaned_data')
    df = pd.read_json(data_json)
    
    # 配置比例
    train_ratio = 0.7
    val_ratio = 0.15
    test_ratio = 0.15
    
    # 是否分层抽样
    stratify_column = 'label'  # 设置为None则不分层
    
    # 第一次切分：训练集 vs (验证集+测试集)
    train_df, temp_df = train_test_split(
        df,
        test_size=(1 - train_ratio),
        stratify=df[stratify_column] if stratify_column else None,
        random_state=42
    )
    
    # 第二次切分：验证集 vs 测试集
    val_df, test_df = train_test_split(
        temp_df,
        test_size=test_ratio / (val_ratio + test_ratio),
        stratify=temp_df[stratify_column] if stratify_column else None,
        random_state=42
    )
    
    # 保存划分后的数据集
    ti.xcom_push(key='train_data', value=train_df.to_json())
    ti.xcom_push(key='val_data', value=val_df.to_json())
    ti.xcom_push(key='test_data', value=test_df.to_json())
    
    print(f"[v0] 数据划分完成:")
    print(f"  训练集: {len(train_df)} 条 ({train_ratio*100}%)")
    print(f"  验证集: {len(val_df)} 条 ({val_ratio*100}%)")
    print(f"  测试集: {len(test_df)} 条 ({test_ratio*100}%)")
    
    return {
        'train': len(train_df),
        'val': len(val_df),
        'test': len(test_df)
    }

# 创建PythonOperator
data_ratio_task = PythonOperator(
    task_id='data_ratio',
    python_callable=split_data,
    provide_context=True,
)`,

      "knowledge-generation": `# 知识生成 PythonOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

def generate_knowledge(**context):
    """
    生成知识库，包括文档切片和向量化
    """
    # 从上游节点获取数据
    ti = context['ti']
    data_json = ti.xcom_pull(key='cleaned_data')
    df = pd.read_json(data_json)
    
    # 文档切片配置
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\\n\\n", "\\n", "。", "！", "？", "，", " ", ""]
    )
    
    # 处理每个文档
    documents = []
    for idx, row in df.iterrows():
        text = row['content']
        chunks = text_splitter.split_text(text)
        
        for chunk in chunks:
            documents.append({
                'text': chunk,
                'metadata': {
                    'source_id': row['id'],
                    'title': row.get('title', ''),
                    'chunk_index': chunks.index(chunk)
                }
            })
    
    # 创建嵌入模型
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key="your-api-key"
    )
    
    # 创建向量数据库
    vectorstore = Chroma.from_texts(
        texts=[doc['text'] for doc in documents],
        embedding=embeddings,
        metadatas=[doc['metadata'] for doc in documents],
        persist_directory="./chroma_db"
    )
    
    vectorstore.persist()
    
    # 保存知识库信息
    ti.xcom_push(key='knowledge_base', value={
        'total_chunks': len(documents),
        'vectorstore_path': './chroma_db'
    })
    
    print(f"[v0] 知识库生成完成，共 {len(documents)} 个文档块")
    return len(documents)

# 创建PythonOperator
knowledge_generation_task = PythonOperator(
    task_id='knowledge_generation',
    python_callable=generate_knowledge,
    provide_context=True,
)`,

      "model-training": `# 模型训练 PythonOperator
from airflow.operators.python import PythonOperator
import pandas as pd
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

def train_model(**context):
    """
    训练机器学习模型
    """
    # 从上游节点获取数据
    ti = context['ti']
    train_json = ti.xcom_pull(key='train_data')
    val_json = ti.xcom_pull(key='val_data')
    
    train_df = pd.read_json(train_json)
    val_df = pd.read_json(val_json)
    
    # 准备特征和标签
    feature_columns = ['feature1', 'feature2', 'feature3']
    label_column = 'label'
    
    X_train = train_df[feature_columns]
    y_train = train_df[label_column]
    X_val = val_df[feature_columns]
    y_val = val_df[label_column]
    
    # 创建并训练模型
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    print("[v0] 开始训练模型...")
    model.fit(X_train, y_train)
    
    # 验证集评估
    y_pred = model.predict(X_val)
    metrics = {
        'accuracy': accuracy_score(y_val, y_pred),
        'precision': precision_score(y_val, y_pred, average='weighted'),
        'recall': recall_score(y_val, y_pred, average='weighted'),
        'f1': f1_score(y_val, y_pred, average='weighted')
    }
    
    # 保存模型
    run_id = context['run_id']
    model_path = f"./models/model_{run_id}.pkl"
    joblib.dump(model, model_path)
    
    # 保存结果
    ti.xcom_push(key='model_path', value=model_path)
    ti.xcom_push(key='metrics', value=json.dumps(metrics))
    
    print(f"[v0] 模型训练完成:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    return metrics

# 创建PythonOperator
model_training_task = PythonOperator(
    task_id='model_training',
    python_callable=train_model,
    provide_context=True,
)`,

      "model-report": `# 模型报告 PythonOperator
from airflow.operators.python import PythonOperator
import pandas as pd
import json
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import joblib

def generate_report(**context):
    """
    生成模型评估报告
    """
    # 从上游节点获取数据
    ti = context['ti']
    model_path = ti.xcom_pull(key='model_path')
    metrics_json = ti.xcom_pull(key='metrics')
    test_json = ti.xcom_pull(key='test_data')
    
    metrics = json.loads(metrics_json)
    test_df = pd.read_json(test_json)
    
    # 加载模型
    model = joblib.load(model_path)
    
    # 准备测试数据
    feature_columns = ['feature1', 'feature2', 'feature3']
    label_column = 'label'
    
    X_test = test_df[feature_columns]
    y_test = test_df[label_column]
    y_pred = model.predict(X_test)
    
    # 生成混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig('./reports/confusion_matrix.png')
    plt.close()
    
    # 生成分类报告
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # 生成PDF报告
    run_id = context['run_id']
    report_path = f"./reports/model_report_{run_id}.pdf"
    c = canvas.Canvas(report_path, pagesize=letter)
    
    # 写入报告标题
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Model Evaluation Report")
    
    # 写入指标
    c.setFont("Helvetica", 12)
    y_position = 700
    for metric, value in metrics.items():
        c.drawString(100, y_position, f"{metric.upper()}: {value:.4f}")
        y_position -= 30
    
    c.save()
    
    # 保存报告路径
    ti.xcom_push(key='report_path', value=report_path)
    
    print(f"[v0] 报告生成完成: {report_path}")
    print("\\n详细指标:")
    print(json.dumps(report, indent=2))
    
    return {
        'report_path': report_path,
        'metrics': metrics
    }

# 创建PythonOperator
model_report_task = PythonOperator(
    task_id='model_report',
    python_callable=generate_report,
    provide_context=True,
)`,
    }

    return (
      templates[nodeType] ||
      `# PythonOperator 示例
from airflow.operators.python import PythonOperator

def execute(**context):
    """
    在这里编写你的代码
    """
    # 获取上游数据
    ti = context['ti']
    data = ti.xcom_pull(key='your_key')
    
    # 处理逻辑
    result = process(data)
    
    # 推送结果到XCom
    ti.xcom_push(key='result', value=result)
    
    return result

# 创建PythonOperator
task = PythonOperator(
    task_id='your_task',
    python_callable=execute,
    provide_context=True,
)`
    )
  }

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="node-name" className="block mb-1">节点名称 *</label>
        <Input
          id="node-name"
          value={config.name}
          onChange={(e) => {
            setNodes((nds: any) =>
              nds.map((n: any) =>
                n.id === node.id ? { ...n, data: { ...n.data, config: { ...config, name: e.target.value } } } : n,
              ),
            )
          }}
          placeholder="输入节点名称"
          className="mt-1"
        />
      </div>

      <div>
        <label htmlFor="node-description" className="block mb-1">节点描述</label>
        <TextArea
          id="node-description"
          value={config.description}
          onChange={(e) => {
            setNodes((nds: any) =>
              nds.map((n: any) =>
                n.id === node.id
                  ? { ...n, data: { ...n.data, config: { ...config, description: e.target.value } } }
                  : n,
              ),
            )
          }}
          placeholder="输入节点描述（可选）"
          className="mt-1"
          rows={2}
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block">Python代码</label>
          <Button
            type="default"
            size="small"
            onClick={() => {
              const template = getCodeTemplate(node.data.type)
              setNodes((nds: any) =>
                nds.map((n: any) =>
                  n.id === node.id ? { ...n, data: { ...n.data, config: { ...config, pythonCode: template } } } : n,
                ),
              )
            }}
            icon={<Code className="w-4 h-4" />}
          >
            加载示例
          </Button>
        </div>
        <TextArea
          value={config.pythonCode}
          onChange={(e) => {
            setNodes((nds: any) =>
              nds.map((n: any) =>
                n.id === node.id ? { ...n, data: { ...n.data, config: { ...config, pythonCode: e.target.value } } } : n,
              ),
            )
          }}
          placeholder="输入Python代码或点击'加载示例'查看模板"
          className="mt-1 font-mono text-xs"
          rows={20}
        />
        <p className="mt-2 text-xs text-gray-500">
          提示：使用 <code className="px-1 py-0.5 bg-gray-100 rounded">kwargs['ti'].xcom_pull()</code> 获取上游数据， 使用{" "}
          <code className="px-1 py-0.5 bg-gray-100 rounded">kwargs['ti'].xcom_push()</code> 传递数据到下游节点
        </p>
      </div>
    </div>
  )
}

const defaultConfigs: Record<string, NodeConfig> = {
  "data-collection": {
    name: "数据归集",
    description: "从数据源采集数据",
    pythonCode: "",
  },
  "data-cleaning": {
    name: "数据清洗",
    description: "清洗和预处理数据",
    pythonCode: "",
  },
  "data-ratio": {
    name: "数据配比",
    description: "划分训练集、验证集、测试集",
    pythonCode: "",
  },
  "knowledge-generation": {
    name: "知识生成",
    description: "生成知识库向量",
    pythonCode: "",
  },
  "model-training": {
    name: "模型训练",
    description: "训练机器学习模型",
    pythonCode: "",
  },
  "model-report": {
    name: "模型报告",
    description: "生成模型评估报告",
    pythonCode: "",
  },
}

function ExecutionDetailView({ executionId, onBack }: { executionId: number; onBack: () => void }) {
  const execution = mockExecutions.find((e) => e.id === executionId)

  if (!execution) return null

  // Mock execution data with node states
  const executionNodes: Node[] = [
    {
      id: "data-collection-1",
      type: "smartNode",
      position: { x: 100, y: 200 },
      data: {
        id: "data-collection-1",
        type: "data-collection",
        name: "数据归集",
        description: "从MySQL数据库收集数据",
        status: "success",
        startTime: "14:30:00",
        endTime: "14:30:45",
        duration: "45s",
        records: 15000,
      },
    },
    {
      id: "data-cleaning-1",
      type: "smartNode",
      position: { x: 450, y: 200 },
      data: {
        id: "data-cleaning-1",
        type: "data-cleaning",
        name: "数据清洗",
        description: "清洗和预处理数据",
        status: execution.status === "running" && execution.currentNode === "data-cleaning" ? "running" : "success",
        startTime: "14:30:45",
        endTime: execution.status === "running" ? undefined : "14:31:20",
        duration: execution.status === "running" ? undefined : "35s",
        recordsBefore: 15000,
        recordsAfter: 14850,
      },
    },
    {
      id: "data-ratio-1",
      type: "smartNode",
      position: { x: 800, y: 200 },
      data: {
        id: "data-ratio-1",
        type: "data-ratio",
        name: "数据配比",
        description: "划分训练集、验证集和测试集",
        status:
          execution.status === "running" && execution.currentNode === "data-ratio"
            ? "running"
            : execution.status === "running"
              ? "pending"
              : "success",
        startTime: execution.status === "running" ? undefined : "14:31:20",
        endTime: execution.status === "running" ? undefined : "14:31:25",
        duration: execution.status === "running" ? undefined : "5s",
      },
    },
    {
      id: "model-training-1",
      type: "smartNode",
      position: { x: 1150, y: 200 },
      data: {
        id: "model-training-1",
        type: "model-training",
        name: "模型训练",
        description: "训练机器学习模型",
        status:
          execution.status === "running" && execution.currentNode === "model-training"
            ? "running"
            : execution.status === "running"
              ? "pending"
              : "success",
        startTime:
          execution.status === "running" && execution.currentNode === "model-training" ? "14:31:25" : undefined,
        progress: execution.status === "running" && execution.currentNode === "model-training" ? 60 : undefined,
      },
    },
    {
      id: "model-report-1",
      type: "smartNode",
      position: { x: 1500, y: 200 },
      data: {
        id: "model-report-1",
        type: "model-report",
        name: "模型报告",
        description: "生成模型评估报告",
        status: "pending",
      },
    },
  ]

  const executionEdges = [
    {
      id: "edge-1-2",
      source: "data-collection-1",
      target: "data-cleaning-1",
      type: "smoothstep",
      animated: false,
      style: { stroke: "#10b981", strokeWidth: 2 },
      markerEnd: { type: "arrowclosed" as const, color: "#10b981" },
    },
    {
      id: "edge-2-3",
      source: "data-cleaning-1",
      target: "data-ratio-1",
      type: "smoothstep",
      animated: execution.status === "running",
      style: { stroke: execution.status === "running" ? "#3b82f6" : "#10b981", strokeWidth: 2 },
      markerEnd: { type: "arrowclosed" as const, color: execution.status === "running" ? "#3b82f6" : "#10b981" },
    },
    {
      id: "edge-3-4",
      source: "data-ratio-1",
      target: "model-training-1",
      type: "smoothstep",
      animated: false,
      style: { stroke: "#94a3b8", strokeWidth: 2 },
      markerEnd: { type: "arrowclosed" as const, color: "#94a3b8" },
    },
    {
      id: "edge-4-5",
      source: "model-training-1",
      target: "model-report-1",
      type: "smoothstep",
      animated: false,
      style: { stroke: "#94a3b8", strokeWidth: 2 },
      markerEnd: { type: "arrowclosed" as const, color: "#94a3b8" },
    },
  ]

  const ExecutionNode = ({ data }: { data: any }) => {
    const nodeColor =
      data.status === "success"
        ? { bg: "bg-green-50", border: "border-green-300", icon: "text-green-600" }
        : data.status === "running"
          ? { bg: "bg-blue-50", border: "border-blue-300", icon: "text-blue-600" }
          : data.status === "failed"
            ? { bg: "bg-red-50", border: "border-red-300", icon: "text-red-600" }
            : { bg: "bg-gray-50", border: "border-gray-300", icon: "text-gray-400" }

    const getNodeIcon = (type: string) => {
      const icons: Record<string, React.ReactNode> = {
        "data-collection": <Database className="w-5 h-5" />,
        "data-cleaning": <Filter className="w-5 h-5" />,
        "data-ratio": <BarChart3 className="w-5 h-5" />,
        "knowledge-generation": <Brain className="w-5 h-5" />,
        "model-training": <Target className="w-5 h-5" />,
        "model-report": <FileText className="w-5 h-5" />,
      }
      return icons[type] || <Settings className="w-5 h-5" />
    }

    return (
      <div className="relative">
        <Handle type="target" position={Position.Left} style={{ visibility: "hidden" }} />
        <Handle type="source" position={Position.Right} style={{ visibility: "hidden" }} />

        <Card className={`w-80 border-2 ${nodeColor.border}`}>
          <div className={`pb-3 ${nodeColor.bg} border-b p-4`}>
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 ${nodeColor.bg} rounded-lg flex items-center justify-center border ${nodeColor.border}`}
              >
                <div className={nodeColor.icon}>{getNodeIcon(data.type)}</div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{data.name}</h3>
                <p className="text-xs text-gray-600">{data.description}</p>
              </div>
              <Badge
                color={
                  data.status === "success"
                    ? "green"
                    : data.status === "running"
                      ? "blue"
                      : data.status === "failed"
                        ? "red"
                        : "default"
                }
                className="text-xs"
              >
                {data.status === "success"
                  ? "成功"
                  : data.status === "running"
                    ? "运行中"
                    : data.status === "failed"
                      ? "失败"
                      : "等待"}
              </Badge>
            </div>
          </div>
          <div className="p-4">
            <div className="space-y-2 text-sm">
              {data.startTime && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">开始时间</span>
                  <span className="font-mono text-xs">{data.startTime}</span>
                </div>
              )}
              {data.endTime && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">结束时间</span>
                  <span className="font-mono text-xs">{data.endTime}</span>
                </div>
              )}
              {data.duration && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">耗时</span>
                  <Badge color="default" className="text-xs">
                    {data.duration}
                  </Badge>
                </div>
              )}
              {data.progress !== undefined && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-600">进度</span>
                    <span className="text-xs font-semibold">{data.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${data.progress}%` }}
                    />
                  </div>
                </div>
              )}
              {data.records !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">处理记录</span>
                  <span className="font-semibold">{data.records.toLocaleString()}</span>
                </div>
              )}
              {data.recordsBefore !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">清洗前/后</span>
                  <span className="font-semibold">
                    {data.recordsBefore.toLocaleString()} → {data.recordsAfter.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    )
  }

  const executionNodeTypes: NodeTypes = {
    smartNode: ExecutionNode,
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button type="text" size="small" onClick={onBack} icon={<ArrowLeft className="w-4 h-4" />}>
              返回
            </Button>
            <Divider type="vertical" className="h-6" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">{execution.workflowName}</h1>
              <p className="text-sm text-gray-600 mt-1">
                执行ID: {execution.id} · 开始时间: {execution.startTime}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              color={
                execution.status === "success"
                  ? "green"
                  : execution.status === "running"
                    ? "blue"
                    : "red"
              }
              className="text-sm px-3 py-1"
            >
              {execution.status === "success" ? "执行成功" : execution.status === "running" ? "运行中" : "执行失败"}
            </Badge>
            {execution.duration && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                <span>总耗时: {execution.duration}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Execution Flow */}
      <div className="flex-1">
        <ReactFlow
          nodes={executionNodes}
          edges={executionEdges}
          nodeTypes={executionNodeTypes}
          fitView
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          className="bg-gray-50"
        >
          <Controls showInteractive={false} />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        </ReactFlow>
      </div>

      {/* Execution Logs */}
      <div className="h-64 bg-white border-t">
        <div className="px-6 py-3 border-b">
          <h2 className="font-semibold text-gray-900">执行日志</h2>
        </div>
        <div className="h-52 px-6 py-3 overflow-auto">
          <div className="space-y-2 font-mono text-xs">
            <div className="flex gap-2">
              <span className="text-gray-500">14:30:00</span>
              <span className="text-blue-600">[INFO]</span>
              <span>开始执行流程: {execution.workflowName}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-500">14:30:00</span>
              <span className="text-blue-600">[INFO]</span>
              <span>启动数据归集节点</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-500">14:30:45</span>
              <span className="text-green-600">[SUCCESS]</span>
              <span>数据归集完成，收集 15,000 条记录</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-500">14:30:45</span>
              <span className="text-blue-600">[INFO]</span>
              <span>启动数据清洗节点</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-500">14:31:05</span>
              <span className="text-blue-600">[INFO]</span>
              <span>移除 50 条空值记录</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-500">14:31:15</span>
              <span className="text-blue-600">[INFO]</span>
              <span>移除 100 条重复记录</span>
            </div>
            {execution.status === "running" && (
              <>
                <div className="flex gap-2">
                  <span className="text-gray-500">14:31:20</span>
                  <span className="text-green-600">[SUCCESS]</span>
                  <span>数据清洗完成，剩余 14,850 条记录</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-gray-500">14:31:25</span>
                  <span className="text-blue-600">[INFO]</span>
                  <span>启动模型训练节点</span>
                </div>
                <div className="flex gap-2 animate-pulse">
                  <span className="text-gray-500">14:32:10</span>
                  <span className="text-blue-600">[INFO]</span>
                  <span>训练进度: Epoch 60/100, Loss: 0.245, Accuracy: 0.892</span>
                </div>
              </>
            )}
            {execution.status === "failed" && execution.error && (
              <div className="flex gap-2">
                <span className="text-gray-500">14:31:20</span>
                <span className="text-red-600">[ERROR]</span>
                <span>{execution.error}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
