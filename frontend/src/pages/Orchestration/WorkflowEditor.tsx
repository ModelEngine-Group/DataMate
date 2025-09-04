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

import { Button, Card, Input, Badge, Typography } from "antd"
import TextArea from "antd/es/input/TextArea"
import {
    Play,
    Save,
    ArrowLeft,
    Settings,
    Database,
    Download,
    Trash2,
    Copy,
    Bug,
    Search,
    ChevronDown,
    MessageSquare,
    Brain,
    Cpu,
} from "lucide-react"

const { Title } = Typography

const CustomNode = ({ data, selected }: { data: any; selected: boolean }) => {
    const [isHovered, setIsHovered] = useState(false)

    const getNodeIcon = (type: string) => {
        switch (type) {
            case "knowledge-search":
                return <Database className="w-4 h-4 text-blue-600" />
            case "ai-dialogue":
                return <MessageSquare className="w-4 h-4 text-blue-600" />
            case "data-processing":
                return <Cpu className="w-4 h-4 text-blue-600" />
            default:
                return <Brain className="w-4 h-4 text-blue-600" />
        }
    }

    return (
        <div className="relative" onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
            {(selected || isHovered) && (
                <>
                    {/* Left side handles - inputs */}
                    <Handle
                        type="target"
                        position={Position.Left}
                        id="left-input"
                        className="w-3 h-3 bg-green-500 border-2 border-white shadow-md hover:bg-green-600 transition-all duration-200 hover:scale-110"
                        style={{ left: -6, top: "50%" }}
                    />

                    {/* Right side handles - outputs */}
                    <Handle
                        type="source"
                        position={Position.Right}
                        id="right-output"
                        className="w-3 h-3 bg-blue-500 border-2 border-white shadow-md hover:bg-blue-600 transition-all duration-200 hover:scale-110"
                        style={{ right: -6, top: "50%" }}
                    />

                    {/* Top handle - can be both input and output */}
                    <Handle
                        type="target"
                        position={Position.Top}
                        id="top-input"
                        className="w-3 h-3 bg-green-500 border-2 border-white shadow-md hover:bg-green-600 transition-all duration-200 hover:scale-110"
                        style={{ top: -6, left: "50%" }}
                    />

                    {/* Bottom handle - can be both input and output */}
                    <Handle
                        type="source"
                        position={Position.Bottom}
                        id="bottom-output"
                        className="w-3 h-3 bg-blue-500 border-2 border-white shadow-md hover:bg-blue-600 transition-all duration-200 hover:scale-110"
                        style={{ bottom: -6, left: "50%" }}
                    />
                </>
            )}

            <Card
                className={`w-80 transition-all duration-200 ${selected ? "ring-2 ring-blue-500 shadow-lg" : "shadow-md hover:shadow-lg"
                    }`}
                bodyStyle={{ padding: 0 }}
            >
                <div className="pb-3 bg-blue-50 border-b px-4 pt-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                                {getNodeIcon(data.type)}
                            </div>
                            <div>
                                <div className="font-semibold text-gray-900">{data.name}</div>
                                <div className="text-sm text-gray-600">{data.description}</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                type="text"
                                size="small"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    data.onDuplicate?.(data.id)
                                }}
                                className="h-8 w-8 p-0 text-gray-500 hover:text-gray-700"
                                icon={<Copy className="w-4 h-4" />}
                            />
                            <Button
                                type="text"
                                size="small"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    data.onDelete?.(data.id)
                                }}
                                className="h-8 w-8 p-0 text-gray-500 hover:text-red-600"
                                icon={<Trash2 className="w-4 h-4" />}
                            />
                        </div>
                    </div>
                </div>
                <div className="p-4 space-y-4">
                    {/* Input Section */}
                    <div>
                        <div className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                            输入
                        </div>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-600">AI 模型</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">手动选择</span>
                                    <ChevronDown className="w-4 h-4 text-gray-400" />
                                </div>
                            </div>
                            <Button type="primary" className="w-full">
                                <Settings className="w-4 h-4 mr-2" />
                                装载
                            </Button>
                        </div>
                    </div>

                    {/* Parameters Table */}
                    <div>
                        <div className="font-medium text-gray-900 mb-3">搜索参数设置</div>
                        <div className="bg-gray-50 rounded-lg p-3">
                            <div className="grid grid-cols-5 gap-2 text-xs font-medium text-gray-600 mb-2">
                                <div>查询方式</div>
                                <div>可用上限</div>
                                <div>查询参数</div>
                                <div>检索数量</div>
                                <div>问题优化</div>
                            </div>
                            <div className="grid grid-cols-5 gap-2 text-xs text-gray-700">
                                <div>含义文档</div>
                                <div>5000</div>
                                <div>0.4</div>
                                <div className="text-red-500">✕</div>
                                <div>Qwen-max</div>
                            </div>
                        </div>
                    </div>

                    {/* Output Section */}
                    <div>
                        <div className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                            输出
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">知识库内容</span>
                            <span className="text-gray-500">知识库搜索</span>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    )
}

const nodeTypes: NodeTypes = {
    customNode: CustomNode,
}

interface WorkflowEditorProps {
    onBack: () => void
    onSave: (workflow: any) => void
    initialWorkflow?: any
}

const nodeTypeTemplates = [
    {
        type: "knowledge-search",
        name: "知识库搜索",
        description: "查询、过滤和检索知识库中的文档内容，为AI模型提供上下文信息",
        icon: Database,
        category: "数据源",
        inputs: 1,
        outputs: 1,
    },
    {
        type: "ai-dialogue",
        name: "AI 对话",
        description: "AI 大模型对话",
        icon: MessageSquare,
        category: "AI处理",
        inputs: 1,
        outputs: 1,
    },
    {
        type: "data-processing",
        name: "数据处理",
        description: "对数据进行清洗、转换和处理",
        icon: Cpu,
        category: "数据处理",
        inputs: 1,
        outputs: 1,
    },
    {
        type: "data-output",
        name: "数据输出",
        description: "将处理后的数据输出到指定位置",
        icon: Download,
        category: "数据输出",
        inputs: 1,
        outputs: 0,
    },
]

export default function WorkflowEditor({ onBack, onSave, initialWorkflow }: WorkflowEditorProps) {
    const [workflow, setWorkflow] = useState({
        id: initialWorkflow?.id || Date.now(),
        name: initialWorkflow?.name || "新建流程",
        description: initialWorkflow?.description || "描述您的数据处理流程",
        category: initialWorkflow?.category || "自定义",
    })

    const [nodes, setNodes, onNodesChange] = useNodesState([])
    const [edges, setEdges, onEdgesChange] = useEdgesState([])
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
    const [searchTerm, setSearchTerm] = useState("")

    const filteredNodeTypes = nodeTypeTemplates.filter(
        (nodeType) =>
            nodeType.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            nodeType.description.toLowerCase().includes(searchTerm.toLowerCase()),
    )

    const onConnect = useCallback(
        (params: Connection) => {
            if (params.source === params.target) return
            const newEdge = {
                ...params,
                id: `edge-${params.source}-${params.target}-${Date.now()}`,
                type: "smoothstep",
                animated: true,
                style: {
                    stroke: "#3b82f6",
                    strokeWidth: 3,
                    strokeDasharray: "0",
                },
                markerEnd: {
                    type: "arrowclosed",
                    color: "#3b82f6",
                },
            }
            setEdges((eds) => addEdge(newEdge, eds))
        },
        [setEdges],
    )

    const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        setSelectedNodeId(node.id)
    }, [])

    const onPaneClick = useCallback(() => {
        setSelectedNodeId(null)
    }, [])

    const onDragStart = (event: React.DragEvent, nodeType: string) => {
        event.dataTransfer.setData("application/reactflow", nodeType)
        event.dataTransfer.effectAllowed = "move"
    }

    const deleteNode = useCallback(
        (nodeId: string) => {
            setNodes((nds) => nds.filter((node) => node.id !== nodeId))
            setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId))
        },
        [setNodes, setEdges],
    )

    const duplicateNode = useCallback(
        (nodeId: string) => {
            const nodeToDuplicate = nodes.find((node) => node.id === nodeId)
            if (!nodeToDuplicate) return

            const newNode: Node = {
                ...nodeToDuplicate,
                id: `${nodeToDuplicate.data.type}_${Date.now()}`,
                position: {
                    x: nodeToDuplicate.position.x + 50,
                    y: nodeToDuplicate.position.y + 50,
                },
                data: {
                    ...nodeToDuplicate.data,
                    id: `${nodeToDuplicate.data.type}_${Date.now()}`,
                },
            }

            setNodes((nds) => nds.concat(newNode))
        },
        [nodes, setNodes],
    )

    const handleSave = () => {
        const workflowData = {
            ...workflow,
            nodes: nodes.map((node) => ({
                id: node.id,
                type: node.data.type,
                name: node.data.name,
                description: node.data.description,
                position: node.position,
                config: node.data.config || {},
            })),
            connections: edges.map((edge) => ({
                id: edge.id,
                source: edge.source,
                target: edge.target,
            })),
        }
        onSave(workflowData)
    }

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault()
        event.dataTransfer.dropEffect = "move"
    }, [])

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault()

            const type = event.dataTransfer.getData("application/reactflow")
            if (typeof type === "undefined" || !type) {
                return
            }

            const position = {
                x: event.clientX - 400, // Adjust for sidebar width
                y: event.clientY - 100, // Adjust for header height
            }

            const nodeTemplate = nodeTypeTemplates.find((template) => template.type === type)
            if (!nodeTemplate) return

            const newNode: Node = {
                id: `${type}_${Date.now()}`,
                type: "customNode",
                position,
                data: {
                    id: `${type}_${Date.now()}`,
                    type: type,
                    name: nodeTemplate.name,
                    description: nodeTemplate.description,
                    onDelete: deleteNode,
                    onDuplicate: duplicateNode,
                },
            }

            setNodes((nds) => nds.concat(newNode))
        },
        [setNodes, deleteNode, duplicateNode],
    )

    return (
        <div className="h-screen flex bg-gray-50">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button type="text" size="small" onClick={onBack} className="text-gray-600 hover:text-gray-900" icon={<ArrowLeft className="w-4 h-4 mr-2" />}>
                            返回
                        </Button>
                        <div className="h-6 w-px bg-gray-300" />
                        <div>
                            <Input
                                value={workflow.name}
                                onChange={(e) => setWorkflow((prev) => ({ ...prev, name: e.target.value }))}
                                className="text-lg font-semibold border-none p-0 h-auto bg-transparent focus-visible:ring-0"
                                placeholder="流程名称"
                                bordered={false}
                            />
                            <Input
                                value={workflow.description}
                                onChange={(e) => setWorkflow((prev) => ({ ...prev, description: e.target.value }))}
                                className="text-sm text-gray-600 border-none p-0 h-auto bg-transparent focus-visible:ring-0 mt-1"
                                placeholder="流程描述"
                                bordered={false}
                            />
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button type="default" size="small" icon={<Bug className="w-4 h-4 mr-2" />}>
                            调试
                        </Button>
                        <Button type="default" size="small" icon={<Play className="w-4 h-4 mr-2" />}>
                            运行
                        </Button>
                        <Button type="primary" onClick={handleSave} size="small" icon={<Save className="w-4 h-4 mr-2" />}>
                            保存
                        </Button>
                    </div>
                </div>
            </div>

            {/* Component Library Sidebar */}
            <div className="w-80 bg-white border-r border-gray-200 flex flex-col mt-20">
                <div className="p-4 border-b border-gray-200">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                        <Input
                            placeholder="搜索组件..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-10"
                        />
                    </div>
                </div>
                <div style={{ flex: 1, overflowY: "auto" }}>
                    <div className="p-4 space-y-3">
                        {filteredNodeTypes.map((nodeType) => (
                            <Card
                                key={nodeType.type}
                                className="cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                                draggable
                                onDragStart={(event) => onDragStart(event, nodeType.type)}
                                bodyStyle={{ padding: 16 }}
                            >
                                <div className="flex items-start gap-3">
                                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <nodeType.icon className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-gray-900 mb-1">{nodeType.name}</div>
                                        <div className="text-sm text-gray-600 leading-relaxed">{nodeType.description}</div>
                                        <Badge color="blue" style={{ marginTop: 8, fontSize: 12 }}>
                                            {nodeType.category}
                                        </Badge>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Canvas */}
            <div className="flex-1 mt-20">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    onDrop={onDrop}
                    onDragOver={onDragOver}
                    nodeTypes={nodeTypes}
                    fitView
                    className="bg-gray-50"
                    connectionLineStyle={{
                        stroke: "#3b82f6",
                        strokeWidth: 3,
                        strokeDasharray: "5,5",
                    }}
                    connectionLineType="smoothstep"
                    defaultEdgeOptions={{
                        type: "smoothstep",
                        animated: true,
                        style: {
                            stroke: "#3b82f6",
                            strokeWidth: 3,
                            strokeDasharray: "0",
                        },
                        markerEnd: {
                            type: "arrowclosed",
                            color: "#3b82f6",
                        },
                    }}
                    isValidConnection={(connection) => {
                        if (connection.source === connection.target) {
                            return false
                        }
                        return true
                    }}
                >
                    <Controls />
                    <MiniMap />
                    <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
                </ReactFlow>
            </div>

            {/* Properties Panel */}
            {selectedNodeId && (
                <div className="w-80 bg-white border-l border-gray-200 mt-20">
                    <div className="p-4 border-b border-gray-200">
                        <Title level={4} style={{ margin: 0 }}>节点配置</Title>
                    </div>
                    <div style={{ height: "calc(100% - 56px)", overflowY: "auto" }}>
                        <div className="p-4 ">
                            {(() => {
                                const selectedNode = nodes.find((node) => node.id === selectedNodeId)
                                if (!selectedNode) return null

                                return (
                                    <>
                                        <div>
                                            <label htmlFor="node-name" className="block font-medium mb-1">节点名称</label>
                                            <Input
                                                id="node-name"
                                                value={selectedNode.data.name}
                                                onChange={(e) => {
                                                    setNodes((nds) =>
                                                        nds.map((node) =>
                                                            node.id === selectedNode.id
                                                                ? { ...node, data: { ...node.data, name: e.target.value } }
                                                                : node,
                                                        ),
                                                    )
                                                }}
                                                className="mt-1"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="node-description" className="block font-medium mb-1">节点描述</label>
                                            <TextArea
                                                id="node-description"
                                                value={selectedNode.data.description}
                                                onChange={(e) => {
                                                    setNodes((nds) =>
                                                        nds.map((node) =>
                                                            node.id === selectedNode.id
                                                                ? { ...node, data: { ...node.data, description: e.target.value } }
                                                                : node,
                                                        ),
                                                    )
                                                }}
                                                className="mt-1"
                                                rows={3}
                                            />
                                        </div>
                                    </>
                                )
                            })()}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
