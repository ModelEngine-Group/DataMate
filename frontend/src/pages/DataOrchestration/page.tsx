"use client"

import React, { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    GitBranch,
    Play,
    Pause,
    Square,
    Download,
    Upload,
    Plus,
    Settings,
    Database,
    Filter,
    Shuffle,
    Target,
    Zap,
    Clock,
    CheckCircle,
    AlertCircle,
    XCircle,
    Eye,
    Copy,
    Edit,
    ArrowRight,
    ArrowLeft,
} from "lucide-react"
import { useRouter } from "next/navigation"

interface FlowNode {
    id: string
    type: string
    name: string
    description: string
    position: { x: number; y: number }
    config: any
    status: "idle" | "running" | "completed" | "error"
    progress?: number
}

interface FlowConnection {
    id: string
    source: string
    target: string
}

interface FlowTemplate {
    id: number
    name: string
    description: string
    category: string
    nodes: FlowNode[]
    connections: FlowConnection[]
    createdAt: string
    lastUsed?: string
    usageCount: number
}

interface FlowExecution {
    id: number
    templateName: string
    status: "running" | "completed" | "failed" | "paused"
    progress: number
    startTime: string
    endTime?: string
    duration?: string
    processedRecords: number
    totalRecords: number
}

interface DataOrchestrationPageProps {
    onBack?: () => void
}

const nodeTypes = [
    {
        type: "data-source",
        name: "数据源",
        icon: Database,
        description: "从各种数据源读取数据",
        color: "bg-blue-500",
        category: "输入",
    },
    {
        type: "data-filter",
        name: "数据过滤",
        icon: Filter,
        description: "根据条件过滤数据",
        color: "bg-green-500",
        category: "处理",
    },
    {
        type: "data-transform",
        name: "数据转换",
        icon: Shuffle,
        description: "转换数据格式和结构",
        color: "bg-purple-500",
        category: "处理",
    },
    {
        type: "data-validation",
        name: "数据验证",
        icon: Target,
        description: "验证数据质量和完整性",
        color: "bg-orange-500",
        category: "处理",
    },
    {
        type: "data-enhancement",
        name: "数据增强",
        icon: Zap,
        description: "增强和丰富数据内容",
        color: "bg-pink-500",
        category: "处理",
    },
    {
        type: "data-output",
        name: "数据输出",
        icon: Download,
        description: "将处理后的数据输出到目标位置",
        color: "bg-indigo-500",
        category: "输出",
    },
]

const mockTemplates: FlowTemplate[] = [
    {
        id: 1,
        name: "WSI病理图像预处理流程",
        description: "专用于WSI病理图像的标准化预处理流程",
        category: "医学影像",
        nodes: [
            {
                id: "node1",
                type: "data-source",
                name: "WSI图像源",
                description: "读取WSI病理图像",
                position: { x: 100, y: 100 },
                config: { source: "wsi_pathology", format: "svs" },
                status: "idle",
            },
            {
                id: "node2",
                type: "data-validation",
                name: "图像质量检查",
                description: "检查图像质量和完整性",
                position: { x: 300, y: 100 },
                config: { minSize: "1GB", maxSize: "5GB" },
                status: "idle",
            },
            {
                id: "node3",
                type: "data-transform",
                name: "图像标准化",
                description: "标准化图像格式和尺寸",
                position: { x: 500, y: 100 },
                config: { targetFormat: "tiff", normalize: true },
                status: "idle",
            },
            {
                id: "node4",
                type: "data-output",
                name: "处理结果输出",
                description: "输出处理后的图像",
                position: { x: 700, y: 100 },
                config: { destination: "processed_wsi" },
                status: "idle",
            },
        ],
        connections: [
            { id: "conn1", source: "node1", target: "node2" },
            { id: "conn2", source: "node2", target: "node3" },
            { id: "conn3", source: "node3", target: "node4" },
        ],
        createdAt: "2024-01-20",
        lastUsed: "2024-01-23",
        usageCount: 15,
    },
    {
        id: 2,
        name: "文本数据清洗流程",
        description: "通用文本数据清洗和标准化流程",
        category: "文本处理",
        nodes: [
            {
                id: "node1",
                type: "data-source",
                name: "文本数据源",
                description: "读取原始文本数据",
                position: { x: 100, y: 100 },
                config: { source: "text_corpus", encoding: "utf-8" },
                status: "idle",
            },
            {
                id: "node2",
                type: "data-filter",
                name: "内容过滤",
                description: "过滤无效和重复内容",
                position: { x: 300, y: 100 },
                config: { minLength: 10, removeDuplicates: true },
                status: "idle",
            },
            {
                id: "node3",
                type: "data-enhancement",
                name: "文本增强",
                description: "文本清洗和格式化",
                position: { x: 500, y: 100 },
                config: { removeHtml: true, normalizeWhitespace: true },
                status: "idle",
            },
            {
                id: "node4",
                type: "data-output",
                name: "清洗结果输出",
                description: "输出清洗后的文本",
                position: { x: 700, y: 100 },
                config: { format: "jsonl" },
                status: "idle",
            },
        ],
        connections: [
            { id: "conn1", source: "node1", target: "node2" },
            { id: "conn2", source: "node2", target: "node3" },
            { id: "conn3", source: "node3", target: "node4" },
        ],
        createdAt: "2024-01-18",
        lastUsed: "2024-01-22",
        usageCount: 28,
    },
]

const mockExecutions: FlowExecution[] = [
    {
        id: 1,
        templateName: "WSI病理图像预处理流程",
        status: "running",
        progress: 65,
        startTime: "2024-01-23 14:30:00",
        processedRecords: 650,
        totalRecords: 1000,
    },
    {
        id: 2,
        templateName: "文本数据清洗流程",
        status: "completed",
        progress: 100,
        startTime: "2024-01-23 10:15:00",
        endTime: "2024-01-23 12:45:00",
        duration: "2h 30m",
        processedRecords: 50000,
        totalRecords: 50000,
    },
    {
        id: 3,
        templateName: "WSI病理图像预处理流程",
        status: "failed",
        progress: 25,
        startTime: "2024-01-22 16:20:00",
        endTime: "2024-01-22 16:45:00",
        duration: "25m",
        processedRecords: 250,
        totalRecords: 1000,
    },
]

export default function DataOrchestrationPage({ onBack }: DataOrchestrationPageProps) {
    const router = useRouter();
    const [templates, setTemplates] = useState<FlowTemplate[]>(mockTemplates)
    const [executions, setExecutions] = useState<FlowExecution[]>(mockExecutions)
    const [selectedTemplate, setSelectedTemplate] = useState<FlowTemplate | null>(null)
    const [showWorkflowEditor, setShowWorkflowEditor] = useState(false)

    const startNewFlow = () => {
        setShowWorkflowEditor(true)
    }

    const handleSaveWorkflow = (workflow: any) => {
        setTemplates([workflow, ...templates])
        setShowWorkflowEditor(false)
    }

    const handleBackFromEditor = () => {
        setShowWorkflowEditor(false)
    }

    if (showWorkflowEditor) {
        const WorkflowEditor = React.lazy(() => import("./workflow-editor/page.tsx"))
        return (
            <React.Suspense fallback={<div>Loading...</div>}>
                <WorkflowEditor onBack={handleBackFromEditor} onSave={handleSaveWorkflow} />
            </React.Suspense>
        )
    }

    const executeTemplate = (template: FlowTemplate) => {
        const newExecution: FlowExecution = {
            id: Date.now(),
            templateName: template.name,
            status: "running",
            progress: 0,
            startTime: new Date().toLocaleString(),
            processedRecords: 0,
            totalRecords: 1000,
        }

        setExecutions([newExecution, ...executions])

        // 模拟执行进度
        const interval = setInterval(() => {
            setExecutions((prev) =>
                prev.map((exec) => {
                    if (exec.id === newExecution.id) {
                        const newProgress = Math.min(exec.progress + Math.random() * 10, 100)
                        return {
                            ...exec,
                            progress: newProgress,
                            status: newProgress >= 100 ? "completed" : "running",
                            processedRecords: Math.floor((newProgress / 100) * exec.totalRecords),
                            endTime: newProgress >= 100 ? new Date().toLocaleString() : undefined,
                        }
                    }
                    return exec
                }),
            )
        }, 500)

        setTimeout(() => clearInterval(interval), 10000)
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "running":
                return <Clock className="w-4 h-4 text-blue-500" />
            case "completed":
                return <CheckCircle className="w-4 h-4 text-green-500" />
            case "failed":
                return <XCircle className="w-4 h-4 text-red-500" />
            case "paused":
                return <Pause className="w-4 h-4 text-yellow-500" />
            default:
                return <AlertCircle className="w-4 h-4 text-gray-500" />
        }
    }

    const getStatusBadge = (status: string) => {
        const statusConfig = {
            running: { label: "运行中", color: "bg-blue-100 text-blue-800" },
            completed: { label: "已完成", color: "bg-green-100 text-green-800" },
            failed: { label: "失败", color: "bg-red-100 text-red-800" },
            paused: { label: "已暂停", color: "bg-yellow-100 text-yellow-800" },
        }
        return statusConfig[status as keyof typeof statusConfig] || statusConfig.running
    }

    const getNodeIcon = (nodeType: string) => {
        const nodeTypeInfo = nodeTypes.find((nt) => nt.type === nodeType)
        const IconComponent = nodeTypeInfo?.icon || Settings
        return <IconComponent className="w-4 h-4" />
    }

    return (
        <div className="space-y-6 p-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="sm" onClick={()=>router.back()}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        返回
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">数据智能编排</h1>
                        <p className="text-gray-600 mt-2">可视化设计和管理数据处理流程</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setSelectedTemplate(null)}>
                        <Upload className="w-4 h-4 mr-2" />
                        导入模板
                    </Button>
                    <Button onClick={startNewFlow}>
                        <Plus className="w-4 h-4 mr-2" />
                        新建流程
                    </Button>
                </div>
            </div>

            {/* Main Content */}
            <Tabs defaultValue="templates">
                <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="templates" className="flex items-center gap-2">
                        <GitBranch className="w-4 h-4" />
                        流程模板 ({templates.length})
                    </TabsTrigger>
                    <TabsTrigger value="executions" className="flex items-center gap-2">
                        <Play className="w-4 h-4" />
                        执行历史 ({executions.length})
                    </TabsTrigger>
                    <TabsTrigger value="monitoring" className="flex items-center gap-2">
                        <Eye className="w-4 h-4" />
                        实时监控
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="templates" className="space-y-4">
                    <div className="grid gap-4">
                        {templates.map((template) => (
                            <Card key={template.id} className="hover:shadow-md transition-shadow">
                                <CardContent className="pt-6">
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                                    <GitBranch className="w-5 h-5 text-orange-600" />
                                                </div>
                                                <div>
                                                    <h4 className="font-semibold">{template.name}</h4>
                                                    <p className="text-sm text-gray-600">{template.description}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Badge variant="secondary">{template.category}</Badge>
                                                <Button variant="outline" size="sm" onClick={() => setSelectedTemplate(template)}>
                                                    <Eye className="w-4 h-4 mr-1" />
                                                    查看
                                                </Button>
                                                <Button size="sm" onClick={() => executeTemplate(template)}>
                                                    <Play className="w-4 h-4 mr-1" />
                                                    执行
                                                </Button>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-6 text-sm text-gray-600">
                                            <div className="flex items-center gap-1">
                                                <Settings className="w-4 h-4" />
                                                <span>{template.nodes.length} 个节点</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <ArrowRight className="w-4 h-4" />
                                                <span>{template.connections.length} 个连接</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Clock className="w-4 h-4" />
                                                <span>创建于 {template.createdAt}</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Target className="w-4 h-4" />
                                                <span>使用 {template.usageCount} 次</span>
                                            </div>
                                        </div>

                                        {/* Flow Preview */}
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-sm font-medium text-gray-700">流程预览:</span>
                                            </div>
                                            <div className="flex items-center gap-2 overflow-x-auto">
                                                {template.nodes.map((node, index) => (
                                                    <div key={node.id} className="flex items-center gap-2 flex-shrink-0">
                                                        <div className="flex items-center gap-2 bg-white rounded px-3 py-1 border">
                                                            {getNodeIcon(node.type)}
                                                            <span className="text-xs font-medium">{node.name}</span>
                                                        </div>
                                                        {index < template.nodes.length - 1 && <ArrowRight className="w-4 h-4 text-gray-400" />}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </TabsContent>

                <TabsContent value="executions" className="space-y-4">
                    <div className="grid gap-4">
                        {executions.map((execution) => (
                            <Card key={execution.id}>
                                <CardContent className="pt-6">
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                {getStatusIcon(execution.status)}
                                                <div>
                                                    <h4 className="font-semibold">{execution.templateName}</h4>
                                                    <p className="text-sm text-gray-600">执行ID: {execution.id}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Badge className={getStatusBadge(execution.status).color}>
                                                    {getStatusBadge(execution.status).label}
                                                </Badge>
                                                {execution.status === "running" && (
                                                    <div className="flex gap-1">
                                                        <Button variant="outline" size="sm">
                                                            <Pause className="w-4 h-4" />
                                                        </Button>
                                                        <Button variant="outline" size="sm">
                                                            <Square className="w-4 h-4" />
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {execution.status === "running" && (
                                            <div className="space-y-2">
                                                <div className="flex justify-between text-sm">
                                                    <span>执行进度</span>
                                                    <span>
                                                        {execution.processedRecords.toLocaleString()} / {execution.totalRecords.toLocaleString()}
                                                    </span>
                                                </div>
                                                <Progress value={execution.progress} className="h-2" />
                                            </div>
                                        )}

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                            <div>
                                                <span className="text-gray-500">开始时间:</span>
                                                <div className="font-medium">{execution.startTime}</div>
                                            </div>
                                            {execution.endTime && (
                                                <div>
                                                    <span className="text-gray-500">结束时间:</span>
                                                    <div className="font-medium">{execution.endTime}</div>
                                                </div>
                                            )}
                                            {execution.duration && (
                                                <div>
                                                    <span className="text-gray-500">执行时长:</span>
                                                    <div className="font-medium">{execution.duration}</div>
                                                </div>
                                            )}
                                            <div>
                                                <span className="text-gray-500">处理记录:</span>
                                                <div className="font-medium">{execution.processedRecords.toLocaleString()}</div>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </TabsContent>

                <TabsContent value="monitoring" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center gap-2">
                                    <Play className="w-5 h-5 text-blue-500" />
                                    <div>
                                        <p className="text-2xl font-bold">{executions.filter((e) => e.status === "running").length}</p>
                                        <p className="text-sm text-gray-500">运行中</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center gap-2">
                                    <CheckCircle className="w-5 h-5 text-green-500" />
                                    <div>
                                        <p className="text-2xl font-bold">{executions.filter((e) => e.status === "completed").length}</p>
                                        <p className="text-sm text-gray-500">已完成</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center gap-2">
                                    <XCircle className="w-5 h-5 text-red-500" />
                                    <div>
                                        <p className="text-2xl font-bold">{executions.filter((e) => e.status === "failed").length}</p>
                                        <p className="text-sm text-gray-500">失败</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center gap-2">
                                    <GitBranch className="w-5 h-5 text-purple-500" />
                                    <div>
                                        <p className="text-2xl font-bold">{templates.length}</p>
                                        <p className="text-sm text-gray-500">流程模板</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Real-time Execution Monitor */}
                    <Card>
                        <CardHeader>
                            <CardTitle>实时执行监控</CardTitle>
                            <CardDescription>当前正在执行的流程实时状态</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {executions.filter((e) => e.status === "running").length > 0 ? (
                                <div className="space-y-4">
                                    {executions
                                        .filter((e) => e.status === "running")
                                        .map((execution) => (
                                            <div key={execution.id} className="border rounded-lg p-4">
                                                <div className="flex items-center justify-between mb-3">
                                                    <h4 className="font-medium">{execution.templateName}</h4>
                                                    <Badge className="bg-blue-100 text-blue-800">运行中</Badge>
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="flex justify-between text-sm">
                                                        <span>进度: {Math.round(execution.progress)}%</span>
                                                        <span>
                                                            {execution.processedRecords.toLocaleString()} / {execution.totalRecords.toLocaleString()}
                                                        </span>
                                                    </div>
                                                    <Progress value={execution.progress} className="h-2" />
                                                    <div className="text-xs text-gray-500">开始时间: {execution.startTime}</div>
                                                </div>
                                            </div>
                                        ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-gray-500">
                                    <Clock className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                                    <p>当前没有正在执行的流程</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Template Detail Modal */}
            {selectedTemplate && (
                <Card className="border-2 border-blue-200">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <GitBranch className="w-5 h-5 text-orange-500" />
                                    {selectedTemplate.name}
                                </CardTitle>
                                <CardDescription>{selectedTemplate.description}</CardDescription>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm">
                                    <Copy className="w-4 h-4 mr-1" />
                                    复制
                                </Button>
                                <Button variant="outline" size="sm">
                                    <Edit className="w-4 h-4 mr-1" />
                                    编辑
                                </Button>
                                <Button size="sm" onClick={() => executeTemplate(selectedTemplate)}>
                                    <Play className="w-4 h-4 mr-1" />
                                    执行
                                </Button>
                                <Button variant="outline" onClick={() => setSelectedTemplate(null)}>
                                    关闭
                                </Button>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="text-center p-4 bg-blue-50 rounded-lg">
                                    <Settings className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                                    <div className="text-2xl font-bold text-blue-600">{selectedTemplate.nodes.length}</div>
                                    <div className="text-sm text-gray-600">处理节点</div>
                                </div>
                                <div className="text-center p-4 bg-green-50 rounded-lg">
                                    <ArrowRight className="w-8 h-8 mx-auto mb-2 text-green-500" />
                                    <div className="text-2xl font-bold text-green-600">{selectedTemplate.connections.length}</div>
                                    <div className="text-sm text-gray-600">节点连接</div>
                                </div>
                                <div className="text-center p-4 bg-purple-50 rounded-lg">
                                    <Target className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                                    <div className="text-2xl font-bold text-purple-600">{selectedTemplate.usageCount}</div>
                                    <div className="text-sm text-gray-600">使用次数</div>
                                </div>
                                <div className="text-center p-4 bg-orange-50 rounded-lg">
                                    <Clock className="w-8 h-8 mx-auto mb-2 text-orange-500" />
                                    <div className="text-2xl font-bold text-orange-600">{selectedTemplate.createdAt}</div>
                                    <div className="text-sm text-gray-600">创建日期</div>
                                </div>
                            </div>

                            <div>
                                <h4 className="font-semibold mb-4">流程节点详情</h4>
                                <div className="space-y-3">
                                    {selectedTemplate.nodes.map((node, index) => (
                                        <div key={node.id} className="flex items-start gap-3 p-4 border rounded-lg">
                                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium">
                                                {index + 1}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-2">
                                                    {getNodeIcon(node.type)}
                                                    <h5 className="font-medium">{node.name}</h5>
                                                    <Badge variant="secondary" className="text-xs">
                                                        {nodeTypes.find((nt) => nt.type === node.type)?.category}
                                                    </Badge>
                                                </div>
                                                <p className="text-sm text-gray-600 mb-2">{node.description}</p>
                                                {Object.keys(node.config).length > 0 && (
                                                    <div className="text-xs text-gray-500 bg-gray-50 rounded p-2">
                                                        <strong>配置:</strong> {JSON.stringify(node.config, null, 2)}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
