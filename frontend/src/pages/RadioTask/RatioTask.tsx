"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
    Plus,
    Eye,
    Clock,
    ArrowLeft,
    Play,
    Search,
    CheckCircle,
    AlertCircle,
    Pause,
    DownloadIcon,
    Database,
    BarChart3,
    Shuffle,
    PieChart,
    Grid3X3,
    List,
    ArrowUpDown,
} from "lucide-react"

interface RatioTask {
    id: number
    name: string
    status: "pending" | "running" | "completed" | "failed" | "paused"
    progress: number
    sourceDatasets: string[]
    targetCount: number
    generatedCount: number
    createdAt: string
    ratioType: "dataset" | "label"
    estimatedTime?: string
    quality?: number
    errorMessage?: string
    ratioConfigs: RatioConfig[]
}

interface RatioConfig {
    id: string
    name: string
    type: "dataset" | "label"
    quantity: number
    percentage: number
    source: string
}

interface Dataset {
    id: string
    name: string
    status: string
    type: string
    format: string
    size: string
    records: number
    createdAt: string
    creator: string
    description?: string
    labels?: string[]
}

const mockRatioTasks: RatioTask[] = [
    {
        id: 1,
        name: "多领域数据配比任务",
        status: "completed",
        progress: 100,
        sourceDatasets: ["orig_20250724_64082", "financial_qa_dataset", "medical_corpus"],
        targetCount: 10000,
        generatedCount: 10000,
        createdAt: "2025-01-24",
        ratioType: "dataset",
        estimatedTime: "已完成",
        quality: 94,
        ratioConfigs: [
            { id: "1", name: "通用文本", type: "dataset", quantity: 4000, percentage: 40, source: "orig_20250724_64082" },
            { id: "2", name: "金融问答", type: "dataset", quantity: 3000, percentage: 30, source: "financial_qa_dataset" },
            { id: "3", name: "医疗语料", type: "dataset", quantity: 3000, percentage: 30, source: "medical_corpus" },
        ],
    },
    {
        id: 2,
        name: "标签配比训练集",
        status: "running",
        progress: 68,
        sourceDatasets: ["teacher_model_outputs", "image_text_pairs"],
        targetCount: 8000,
        generatedCount: 5440,
        createdAt: "2025-01-25",
        ratioType: "label",
        estimatedTime: "剩余 12 分钟",
        quality: 89,
        ratioConfigs: [
            { id: "1", name: "问答", type: "label", quantity: 2500, percentage: 31.25, source: "teacher_model_outputs_问答" },
            { id: "2", name: "推理", type: "label", quantity: 2000, percentage: 25, source: "teacher_model_outputs_推理" },
            { id: "3", name: "图像", type: "label", quantity: 1800, percentage: 22.5, source: "image_text_pairs_图像" },
            { id: "4", name: "描述", type: "label", quantity: 1700, percentage: 21.25, source: "image_text_pairs_描述" },
        ],
    },
    {
        id: 3,
        name: "平衡数据集配比",
        status: "failed",
        progress: 25,
        sourceDatasets: ["orig_20250724_64082", "financial_qa_dataset"],
        targetCount: 5000,
        generatedCount: 1250,
        createdAt: "2025-01-25",
        ratioType: "dataset",
        errorMessage: "数据源连接失败，请检查数据集状态",
        ratioConfigs: [
            { id: "1", name: "通用文本", type: "dataset", quantity: 2500, percentage: 50, source: "orig_20250724_64082" },
            { id: "2", name: "金融问答", type: "dataset", quantity: 2500, percentage: 50, source: "financial_qa_dataset" },
        ],
    },
    {
        id: 4,
        name: "文本分类配比任务",
        status: "pending",
        progress: 0,
        sourceDatasets: ["text_classification_data", "sentiment_analysis_data"],
        targetCount: 6000,
        generatedCount: 0,
        createdAt: "2025-01-26",
        ratioType: "label",
        estimatedTime: "预计 15 分钟",
        ratioConfigs: [
            {
                id: "1",
                name: "正面",
                type: "label",
                quantity: 2000,
                percentage: 33.33,
                source: "sentiment_analysis_data_正面",
            },
            {
                id: "2",
                name: "负面",
                type: "label",
                quantity: 2000,
                percentage: 33.33,
                source: "sentiment_analysis_data_负面",
            },
            {
                id: "3",
                name: "中性",
                type: "label",
                quantity: 2000,
                percentage: 33.33,
                source: "sentiment_analysis_data_中性",
            },
        ],
    },
    {
        id: 5,
        name: "多模态数据配比",
        status: "paused",
        progress: 45,
        sourceDatasets: ["image_caption_data", "video_description_data"],
        targetCount: 12000,
        generatedCount: 5400,
        createdAt: "2025-01-23",
        ratioType: "dataset",
        estimatedTime: "已暂停",
        quality: 91,
        ratioConfigs: [
            { id: "1", name: "图像描述", type: "dataset", quantity: 7000, percentage: 58.33, source: "image_caption_data" },
            {
                id: "2",
                name: "视频描述",
                type: "dataset",
                quantity: 5000,
                percentage: 41.67,
                source: "video_description_data",
            },
        ],
    },
]

const mockDatasets: Dataset[] = [
    {
        id: "orig_20250724_64082",
        name: "orig_20250724_64082",
        status: "原始数据集",
        type: "预训练文本",
        format: "jsonl",
        size: "272KB",
        records: 50,
        createdAt: "2025.07.24 12:04:42 GMT+08:00",
        creator: "test_zhang_lsv",
        description: "高质量的中文文本数据，适用于问答对生成",
        labels: ["教育", "科技", "文学"],
    },
    {
        id: "teacher_model_outputs",
        name: "teacher_model_outputs",
        status: "处理完成",
        type: "结构化数据",
        format: "json",
        size: "1.2GB",
        records: 10000,
        createdAt: "2025.01.15 09:30:15 GMT+08:00",
        creator: "ai_trainer",
        description: "教师模型的输出数据，用于知识蒸馏",
        labels: ["问答", "推理", "知识"],
    },
    {
        id: "image_text_pairs",
        name: "image_text_pairs",
        status: "原始数据集",
        type: "多模态数据",
        format: "mixed",
        size: "5.8GB",
        records: 25000,
        createdAt: "2025.01.10 14:22:33 GMT+08:00",
        creator: "data_team",
        description: "图文对数据集，包含高质量的图像和对应描述",
        labels: ["图像", "描述", "多模态"],
    },
    {
        id: "financial_qa_dataset",
        name: "financial_qa_dataset",
        status: "处理完成",
        type: "领域数据",
        format: "jsonl",
        size: "856KB",
        records: 3200,
        createdAt: "2025.01.18 16:20:10 GMT+08:00",
        creator: "finance_team",
        description: "金融领域问答数据集",
        labels: ["金融", "问答", "专业"],
    },
    {
        id: "medical_corpus",
        name: "medical_corpus",
        status: "原始数据集",
        type: "领域数据",
        format: "txt",
        size: "2.1GB",
        records: 15000,
        createdAt: "2025.01.12 10:15:30 GMT+08:00",
        creator: "medical_team",
        description: "医疗领域文本语料库",
        labels: ["医疗", "诊断", "治疗"],
    },
]

export default function RatioTasksPage() {
    const [activeTab, setActiveTab] = useState("tasks")
    const [showCreateTask, setShowCreateTask] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const [filterStatus, setFilterStatus] = useState("all")
    const [filterType, setFilterType] = useState("all")
    const [sortBy, setSortBy] = useState("createdAt")
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
    const [viewMode, setViewMode] = useState<"card" | "table">("card")

    // 配比任务相关状态
    const [ratioTaskForm, setRatioTaskForm] = useState({
        name: "",
        description: "",
        ratioType: "dataset" as "dataset" | "label",
        selectedDatasets: [] as string[],
        ratioConfigs: [] as RatioConfig[],
        totalTargetCount: 10000,
        autoStart: true,
    })

    const [tasks, setTasks] = useState<RatioTask[]>(mockRatioTasks)
    const [datasets] = useState<Dataset[]>(mockDatasets)

    // 过滤和排序任务
    const filteredAndSortedTasks = tasks
        .filter((task) => {
            const matchesSearch = task.name.toLowerCase().includes(searchQuery.toLowerCase())
            const matchesStatus = filterStatus === "all" || task.status === filterStatus
            const matchesType = filterType === "all" || task.ratioType === filterType
            return matchesSearch && matchesStatus && matchesType
        })
        .sort((a, b) => {
            let aValue: any, bValue: any

            switch (sortBy) {
                case "name":
                    aValue = a.name.toLowerCase()
                    bValue = b.name.toLowerCase()
                    break
                case "targetCount":
                    aValue = a.targetCount
                    bValue = b.targetCount
                    break
                case "generatedCount":
                    aValue = a.generatedCount
                    bValue = b.generatedCount
                    break
                case "progress":
                    aValue = a.progress
                    bValue = b.progress
                    break
                case "createdAt":
                default:
                    aValue = new Date(a.createdAt).getTime()
                    bValue = new Date(b.createdAt).getTime()
                    break
            }

            if (sortOrder === "asc") {
                return aValue > bValue ? 1 : -1
            } else {
                return aValue < bValue ? 1 : -1
            }
        })

    const handleCreateRatioTask = () => {
        if (!ratioTaskForm.name || ratioTaskForm.ratioConfigs.length === 0) {
            return
        }

        const newTask: RatioTask = {
            id: Date.now(),
            name: ratioTaskForm.name,
            status: ratioTaskForm.autoStart ? "pending" : "paused",
            progress: 0,
            sourceDatasets: ratioTaskForm.selectedDatasets,
            targetCount: ratioTaskForm.totalTargetCount,
            generatedCount: 0,
            createdAt: new Date().toISOString().split("T")[0],
            ratioType: ratioTaskForm.ratioType,
            estimatedTime: "预计 20 分钟",
            ratioConfigs: ratioTaskForm.ratioConfigs,
        }

        setTasks([newTask, ...tasks])
        setShowCreateTask(false)

        // 重置表单
        setRatioTaskForm({
            name: "",
            description: "",
            ratioType: "dataset",
            selectedDatasets: [],
            ratioConfigs: [],
            totalTargetCount: 10000,
            autoStart: true,
        })

        // 如果自动开始，模拟任务执行
        if (ratioTaskForm.autoStart) {
            setTimeout(() => {
                setTasks((prev) => prev.map((task) => (task.id === newTask.id ? { ...task, status: "running" } : task)))

                const interval = setInterval(() => {
                    setTasks((prev) =>
                        prev.map((task) => {
                            if (task.id === newTask.id && task.status === "running") {
                                const newProgress = Math.min(task.progress + Math.random() * 10 + 5, 100)
                                const isCompleted = newProgress >= 100
                                return {
                                    ...task,
                                    progress: newProgress,
                                    generatedCount: Math.floor((newProgress / 100) * task.targetCount),
                                    status: isCompleted ? "completed" : "running",
                                    estimatedTime: isCompleted ? "已完成" : `剩余 ${Math.ceil((100 - newProgress) / 15)} 分钟`,
                                }
                            }
                            return task
                        }),
                    )
                }, 1000)

                setTimeout(() => clearInterval(interval), 8000)
            }, 1000)
        }
    }

    const handleDatasetSelection = (datasetId: string, checked: boolean) => {
        if (checked) {
            setRatioTaskForm((prev) => ({
                ...prev,
                selectedDatasets: [...prev.selectedDatasets, datasetId],
            }))
        } else {
            setRatioTaskForm((prev) => ({
                ...prev,
                selectedDatasets: prev.selectedDatasets.filter((id) => id !== datasetId),
                ratioConfigs: prev.ratioConfigs.filter((config) => config.source !== datasetId),
            }))
        }
    }

    const updateRatioConfig = (source: string, quantity: number) => {
        setRatioTaskForm((prev) => {
            const existingIndex = prev.ratioConfigs.findIndex((config) => config.source === source)
            const totalOtherQuantity = prev.ratioConfigs
                .filter((config) => config.source !== source)
                .reduce((sum, config) => sum + config.quantity, 0)

            const newConfig: RatioConfig = {
                id: source,
                name: source,
                type: prev.ratioType,
                quantity: Math.min(quantity, prev.totalTargetCount - totalOtherQuantity),
                percentage: Math.round((quantity / prev.totalTargetCount) * 100),
                source,
            }

            if (existingIndex >= 0) {
                const newConfigs = [...prev.ratioConfigs]
                newConfigs[existingIndex] = newConfig
                return { ...prev, ratioConfigs: newConfigs }
            } else {
                return { ...prev, ratioConfigs: [...prev.ratioConfigs, newConfig] }
            }
        })
    }

    const generateAutoRatio = () => {
        const selectedCount = ratioTaskForm.selectedDatasets.length
        if (selectedCount === 0) return

        const baseQuantity = Math.floor(ratioTaskForm.totalTargetCount / selectedCount)
        const remainder = ratioTaskForm.totalTargetCount % selectedCount

        const newConfigs: RatioConfig[] = ratioTaskForm.selectedDatasets.map((datasetId, index) => {
            const quantity = baseQuantity + (index < remainder ? 1 : 0)
            return {
                id: datasetId,
                name: datasetId,
                type: ratioTaskForm.ratioType,
                quantity,
                percentage: Math.round((quantity / ratioTaskForm.totalTargetCount) * 100),
                source: datasetId,
            }
        })

        setRatioTaskForm((prev) => ({ ...prev, ratioConfigs: newConfigs }))
    }

    const getStatusBadge = (status: string) => {
        const statusConfig = {
            pending: { label: "等待中", color: "bg-yellow-100 text-yellow-800", icon: Clock },
            running: { label: "运行中", color: "bg-blue-100 text-blue-800", icon: Play },
            completed: { label: "已完成", color: "bg-green-100 text-green-800", icon: CheckCircle },
            failed: { label: "失败", color: "bg-red-100 text-red-800", icon: AlertCircle },
            paused: { label: "已暂停", color: "bg-gray-100 text-gray-800", icon: Pause },
        }
        return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    }

    const handleTaskAction = (taskId: number, action: string) => {
        setTasks((prev) =>
            prev.map((task) => {
                if (task.id === taskId) {
                    switch (action) {
                        case "pause":
                            return { ...task, status: "paused" as const }
                        case "resume":
                            return { ...task, status: "running" as const }
                        case "stop":
                            return { ...task, status: "failed" as const, progress: task.progress }
                        default:
                            return task
                    }
                }
                return task
            }),
        )
    }

    const renderCreateTaskPage = () => {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <Button variant="outline" onClick={() => setShowCreateTask(false)}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        返回
                    </Button>
                    <div>
                        <h3 className="text-lg font-semibold">创建数据配比任务</h3>
                        <p className="text-sm text-gray-600">选择多个数据集进行配比创建</p>
                    </div>
                </div>

                <div className="grid grid-cols-12 gap-6">
                    {/* 左侧：数据集选择 */}
                    <div className="col-span-5">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Database className="w-5 h-5" />
                                    数据集选择
                                </CardTitle>
                                <CardDescription>选择需要进行配比的数据集</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2">
                                        <Label className="text-sm">配比方式:</Label>
                                        <Select
                                            value={ratioTaskForm.ratioType}
                                            onValueChange={(value: "dataset" | "label") =>
                                                setRatioTaskForm({ ...ratioTaskForm, ratioType: value, ratioConfigs: [] })
                                            }
                                        >
                                            <SelectTrigger className="w-32">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="dataset">按数据集</SelectItem>
                                                <SelectItem value="label">按标签</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="flex-1 relative">
                                        <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                        <Input placeholder="搜索数据集" className="pl-10" />
                                    </div>
                                </div>

                                <ScrollArea className="h-500">
                                    <div className="space-y-2">
                                        {datasets.map((dataset) => (
                                            <div
                                                key={dataset.id}
                                                className={`p-3 border rounded-lg cursor-pointer transition-colors ${ratioTaskForm.selectedDatasets.includes(dataset.id)
                                                    ? "border-blue-200 bg-blue-50"
                                                    : "hover:bg-gray-50"
                                                    }`}
                                                onClick={() =>
                                                    handleDatasetSelection(dataset.id, !ratioTaskForm.selectedDatasets.includes(dataset.id))
                                                }
                                            >
                                                <div className="flex items-start gap-3">
                                                    <Checkbox
                                                        checked={ratioTaskForm.selectedDatasets.includes(dataset.id)}
                                                        onChange={(checked) => handleDatasetSelection(dataset.id, checked)}
                                                    />
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-medium text-sm truncate">{dataset.name}</span>
                                                            <Badge variant="outline" className="text-xs">
                                                                {dataset.type}
                                                            </Badge>
                                                        </div>
                                                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{dataset.description}</p>
                                                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                                            <span>{dataset.records.toLocaleString()}条</span>
                                                            <span>{dataset.size}</span>
                                                            <span>{dataset.format}</span>
                                                        </div>
                                                        {ratioTaskForm.ratioType === "label" && dataset.labels && (
                                                            <div className="flex flex-wrap gap-1 mt-2">
                                                                {dataset.labels.map((label, index) => (
                                                                    <Badge key={index} variant="secondary" className="text-xs">
                                                                        {label}
                                                                    </Badge>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </ScrollArea>

                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <span className="text-sm text-gray-600">已选择 {ratioTaskForm.selectedDatasets.length} 个数据集</span>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setRatioTaskForm({ ...ratioTaskForm, selectedDatasets: [], ratioConfigs: [] })}
                                    >
                                        清空选择
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* 右侧：配比配置 */}
                    <div className="col-span-7">
                        <Card>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="flex items-center gap-2">
                                            <PieChart className="w-5 h-5" />
                                            配比配置
                                        </CardTitle>
                                        <CardDescription>设置每个数据集的配比数量</CardDescription>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={generateAutoRatio}
                                            disabled={ratioTaskForm.selectedDatasets.length === 0}
                                        >
                                            <Shuffle className="w-4 h-4 mr-1" />
                                            平均分配
                                        </Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* 基本配置 */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-medium">任务名称 *</Label>
                                        <Input
                                            value={ratioTaskForm.name}
                                            onChange={(e) => setRatioTaskForm({ ...ratioTaskForm, name: e.target.value })}
                                            placeholder="输入配比任务名称"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-sm font-medium">目标总数量 *</Label>
                                        <Input
                                            type="number"
                                            value={ratioTaskForm.totalTargetCount}
                                            onChange={(e) => setRatioTaskForm({ ...ratioTaskForm, totalTargetCount: Number(e.target.value) })}
                                            placeholder="目标总数量"
                                            min="1"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-sm font-medium">任务描述</Label>
                                    <Textarea
                                        value={ratioTaskForm.description}
                                        onChange={(e) => setRatioTaskForm({ ...ratioTaskForm, description: e.target.value })}
                                        placeholder="描述配比任务的目的和要求（可选）"
                                        rows={2}
                                        className="resize-none"
                                    />
                                </div>

                                {/* 配比设置 */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-sm font-medium">配比设置</Label>
                                        <span className="text-xs text-gray-500">
                                            已配置: {ratioTaskForm.ratioConfigs.reduce((sum, config) => sum + config.quantity, 0)} /{" "}
                                            {ratioTaskForm.totalTargetCount}
                                        </span>
                                    </div>

                                    {ratioTaskForm.selectedDatasets.length === 0 ? (
                                        <div className="text-center py-8 text-gray-500">
                                            <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                                            <p className="text-sm">请先选择数据集</p>
                                        </div>
                                    ) : (
                                        <ScrollArea className="h-500">
                                            <div className="space-y-3">
                                                {ratioTaskForm.selectedDatasets.map((datasetId) => {
                                                    const dataset = datasets.find((d) => d.id === datasetId)
                                                    const config = ratioTaskForm.ratioConfigs.find((c) => c.source === datasetId)
                                                    const currentQuantity = config?.quantity || 0

                                                    if (!dataset) return null

                                                    return (
                                                        <div key={datasetId} className="p-3 border rounded-lg">
                                                            <div className="flex items-center justify-between mb-3">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="font-medium text-sm">{dataset.name}</span>
                                                                    <Badge variant="outline" className="text-xs">
                                                                        {dataset.records.toLocaleString()}条
                                                                    </Badge>
                                                                </div>
                                                                <div className="text-xs text-gray-500">{config?.percentage || 0}%</div>
                                                            </div>

                                                            {ratioTaskForm.ratioType === "dataset" ? (
                                                                <div className="space-y-2">
                                                                    <div className="flex items-center gap-2">
                                                                        <Label className="text-xs">数量:</Label>
                                                                        <Input
                                                                            type="number"
                                                                            value={currentQuantity}
                                                                            onChange={(e) => updateRatioConfig(datasetId, Number(e.target.value))}
                                                                            className="h-8 w-24"
                                                                            min="0"
                                                                            max={ratioTaskForm.totalTargetCount}
                                                                        />
                                                                        <span className="text-xs text-gray-500">条</span>
                                                                    </div>
                                                                    <Progress
                                                                        value={(currentQuantity / ratioTaskForm.totalTargetCount) * 100}
                                                                        className="h-2"
                                                                    />
                                                                </div>
                                                            ) : (
                                                                <div className="space-y-2">
                                                                    {dataset.labels?.map((label, index) => {
                                                                        const labelConfig = ratioTaskForm.ratioConfigs.find(
                                                                            (c) => c.source === `${datasetId}_${label}`,
                                                                        )
                                                                        const labelQuantity = labelConfig?.quantity || 0

                                                                        return (
                                                                            <div key={index} className="flex items-center gap-2">
                                                                                <Badge variant="secondary" className="text-xs min-w-16">
                                                                                    {label}
                                                                                </Badge>
                                                                                <Input
                                                                                    type="number"
                                                                                    value={labelQuantity}
                                                                                    onChange={(e) =>
                                                                                        updateRatioConfig(`${datasetId}_${label}`, Number(e.target.value))
                                                                                    }
                                                                                    className="h-7 w-20"
                                                                                    min="0"
                                                                                />
                                                                                <span className="text-xs text-gray-500">条</span>
                                                                                <div className="flex-1">
                                                                                    <Progress
                                                                                        value={(labelQuantity / ratioTaskForm.totalTargetCount) * 100}
                                                                                        className="h-1"
                                                                                    />
                                                                                </div>
                                                                                <span className="text-xs text-gray-500 min-w-8">
                                                                                    {Math.round((labelQuantity / ratioTaskForm.totalTargetCount) * 100)}%
                                                                                </span>
                                                                            </div>
                                                                        )
                                                                    })}
                                                                </div>
                                                            )}
                                                        </div>
                                                    )
                                                })}
                                            </div>
                                        </ScrollArea>
                                    )}
                                </div>

                                {/* 配比预览 */}
                                {ratioTaskForm.ratioConfigs.length > 0 && (
                                    <div className="space-y-3">
                                        <Label className="text-sm font-medium">配比预览</Label>
                                        <div className="p-3 bg-gray-50 rounded-lg">
                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div>
                                                    <span className="text-gray-500">总配比数量:</span>
                                                    <span className="ml-2 font-medium">
                                                        {ratioTaskForm.ratioConfigs
                                                            .reduce((sum, config) => sum + config.quantity, 0)
                                                            .toLocaleString()}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">目标数量:</span>
                                                    <span className="ml-2 font-medium">{ratioTaskForm.totalTargetCount.toLocaleString()}</span>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">配比项目:</span>
                                                    <span className="ml-2 font-medium">{ratioTaskForm.ratioConfigs.length}个</span>
                                                </div>
                                                <div>
                                                    <span className="text-gray-500">预计时间:</span>
                                                    <span className="ml-2 font-medium">约 20 分钟</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div className="flex items-center justify-between p-3 border rounded-lg">
                                    <div>
                                        <Label className="text-sm font-medium">创建后自动开始</Label>
                                        <p className="text-xs text-gray-500 mt-1">任务创建完成后立即开始执行</p>
                                    </div>
                                    <Switch
                                        checked={ratioTaskForm.autoStart}
                                        onCheckedChange={(checked) => setRatioTaskForm({ ...ratioTaskForm, autoStart: checked })}
                                    />
                                </div>

                                <div className="flex justify-end gap-2">
                                    <Button variant="outline" onClick={() => setShowCreateTask(false)}>
                                        取消
                                    </Button>
                                    <Button
                                        onClick={handleCreateRatioTask}
                                        disabled={!ratioTaskForm.name || ratioTaskForm.ratioConfigs.length === 0}
                                        className="min-w-24 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                                    >
                                        <Play className="w-4 h-4 mr-2" />
                                        创建任务
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        )
    }

    const renderTableView = () => {
        return (
            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[200px]">任务名称</TableHead>
                                <TableHead>状态</TableHead>
                                <TableHead>配比方式</TableHead>
                                <TableHead>进度</TableHead>
                                <TableHead>目标数量</TableHead>
                                <TableHead>已生成</TableHead>
                                <TableHead>数据源</TableHead>
                                <TableHead>创建时间</TableHead>
                                <TableHead className="text-right">操作</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredAndSortedTasks.map((task) => {
                                const statusConfig = getStatusBadge(task.status)
                                const StatusIcon = statusConfig.icon

                                return (
                                    <TableRow key={task.id} className="hover:bg-gray-50">
                                        <TableCell className="font-medium">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                                                    <BarChart3 className="w-4 h-4 text-white" />
                                                </div>
                                                <span className="truncate">{task.name}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge className={`${statusConfig.color} flex items-center gap-1 w-fit`}>
                                                <StatusIcon className="w-3 h-3" />
                                                {statusConfig.label}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{task.ratioType === "dataset" ? "按数据集" : "按标签"}</Badge>
                                        </TableCell>
                                        <TableCell>
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <Progress value={task.progress} className="h-2 w-20" />
                                                    <span className="text-sm text-gray-500">{Math.round(task.progress)}%</span>
                                                </div>
                                                {task.status === "running" && task.estimatedTime && (
                                                    <div className="text-xs text-gray-500">{task.estimatedTime}</div>
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell>{task.targetCount.toLocaleString()}</TableCell>
                                        <TableCell>{task.generatedCount.toLocaleString()}</TableCell>
                                        <TableCell>
                                            <div className="text-sm">{task.sourceDatasets.length}个数据集</div>
                                        </TableCell>
                                        <TableCell>{task.createdAt}</TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex items-center gap-1 justify-end">
                                                {task.status === "running" && (
                                                    <Button variant="outline" size="sm" onClick={() => handleTaskAction(task.id, "pause")}>
                                                        <Pause className="w-4 h-4" />
                                                    </Button>
                                                )}
                                                {task.status === "paused" && (
                                                    <Button variant="outline" size="sm" onClick={() => handleTaskAction(task.id, "resume")}>
                                                        <Play className="w-4 h-4" />
                                                    </Button>
                                                )}
                                                <Button variant="outline" size="sm">
                                                    <Eye className="w-4 h-4" />
                                                </Button>
                                                <Button variant="outline" size="sm">
                                                    <DownloadIcon className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                )
                            })}
                        </TableBody>
                    </Table>

                    {filteredAndSortedTasks.length === 0 && (
                        <div className="text-center py-8">
                            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无配比任务</h3>
                            <p className="text-gray-500 mb-4">
                                {searchQuery || filterStatus !== "all" || filterType !== "all"
                                    ? "没有找到匹配的任务"
                                    : "开始创建您的第一个配比任务"}
                            </p>
                            {!searchQuery && filterStatus === "all" && filterType === "all" && (
                                <Button
                                    onClick={() => setShowCreateTask(true)}
                                    className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    创建配比任务
                                </Button>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
        )
    }

    const renderCardView = () => {
        return (
            <div className="grid gap-4">
                {filteredAndSortedTasks.map((task) => {
                    const statusConfig = getStatusBadge(task.status)
                    const StatusIcon = statusConfig.icon

                    return (
                        <Card key={task.id} className="hover:shadow-md transition-shadow">
                            <CardContent className="pt-6">
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                                                <BarChart3 className="w-5 h-5 text-white" />
                                            </div>
                                            <div>
                                                <h4 className="font-medium text-lg">{task.name}</h4>
                                                <p className="text-sm text-gray-600">
                                                    数据源: {task.sourceDatasets.length}个数据集 •{" "}
                                                    {task.ratioType === "dataset" ? "按数据集" : "按标签"}配比
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Badge className={`${statusConfig.color} flex items-center gap-1`}>
                                                <StatusIcon className="w-3 h-3" />
                                                {statusConfig.label}
                                            </Badge>
                                            {task.status === "running" && (
                                                <Button variant="outline" size="sm" onClick={() => handleTaskAction(task.id, "pause")}>
                                                    <Pause className="w-4 h-4" />
                                                </Button>
                                            )}
                                            {task.status === "paused" && (
                                                <Button variant="outline" size="sm" onClick={() => handleTaskAction(task.id, "resume")}>
                                                    <Play className="w-4 h-4" />
                                                </Button>
                                            )}
                                            <Button variant="outline" size="sm">
                                                <Eye className="w-4 h-4" />
                                            </Button>
                                            <Button variant="outline" size="sm">
                                                <DownloadIcon className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>

                                    {task.status === "running" && (
                                        <div className="space-y-2">
                                            <div className="flex justify-between text-sm">
                                                <span>配比进度</span>
                                                <span>
                                                    {task.generatedCount.toLocaleString()} / {task.targetCount.toLocaleString()}
                                                </span>
                                            </div>
                                            <Progress value={task.progress} className="h-2" />
                                            <div className="flex justify-between text-xs text-gray-500">
                                                <span>{Math.round(task.progress)}% 完成</span>
                                                <span>{task.estimatedTime}</span>
                                            </div>
                                        </div>
                                    )}

                                    {task.status === "failed" && task.errorMessage && (
                                        <Alert className="border-red-200 bg-red-50">
                                            <AlertCircle className="h-4 w-4 text-red-600" />
                                            <AlertDescription className="text-red-800">{task.errorMessage}</AlertDescription>
                                        </Alert>
                                    )}

                                    {/* 配比详情 */}
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium">配比详情</span>
                                            <span className="text-xs text-gray-500">{task.ratioConfigs.length}个配比项</span>
                                        </div>
                                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                            {task.ratioConfigs.map((config, index) => (
                                                <div key={index} className="p-2 bg-gray-50 rounded text-xs">
                                                    <div className="font-medium truncate">{config.name}</div>
                                                    <div className="text-gray-500 mt-1">
                                                        {config.quantity.toLocaleString()}条 ({config.percentage}%)
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-500">配比方式:</span>
                                            <span className="ml-2 font-medium">{task.ratioType === "dataset" ? "按数据集" : "按标签"}</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">已生成:</span>
                                            <span className="ml-2 font-medium">{task.generatedCount.toLocaleString()}</span>
                                        </div>
                                        {task.quality && (
                                            <div>
                                                <span className="text-gray-500">质量评分:</span>
                                                <span className="ml-2 font-medium text-green-600">{task.quality}%</span>
                                            </div>
                                        )}
                                        <div>
                                            <span className="text-gray-500">创建时间:</span>
                                            <span className="ml-2 font-medium">{task.createdAt}</span>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )
                })}

                {filteredAndSortedTasks.length === 0 && (
                    <Card>
                        <CardContent className="pt-6">
                            <div className="text-center py-8">
                                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-gray-900 mb-2">暂无配比任务</h3>
                                <p className="text-gray-500 mb-4">
                                    {searchQuery || filterStatus !== "all" || filterType !== "all"
                                        ? "没有找到匹配的任务"
                                        : "开始创建您的第一个配比任务"}
                                </p>
                                {!searchQuery && filterStatus === "all" && filterType === "all" && (
                                    <Button
                                        onClick={() => setShowCreateTask(true)}
                                        className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                                    >
                                        <Plus className="w-4 h-4 mr-2" />
                                        创建配比任务
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        )
    }

    if (showCreateTask) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold">创建配比任务</h2>
                </div>
                {renderCreateTaskPage()}
            </div>
        )
    }

    return (
        <TooltipProvider>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold">配比任务</h2>
                        <p className="text-gray-600 mt-2">多数据集配比和标签配比管理平台</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            onClick={() => setShowCreateTask(true)}
                            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            创建配比任务
                        </Button>
                    </div>
                </div>

                <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsContent value="tasks" className="space-y-4">
                        {/* 搜索、筛选和视图控制 */}
                        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                            <div className="flex-1 relative">
                                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                <Input
                                    placeholder="搜索任务名称"
                                    className="pl-10"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>

                            <Select value={filterStatus} onValueChange={setFilterStatus}>
                                <SelectTrigger className="w-32">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">全部状态</SelectItem>
                                    <SelectItem value="pending">等待中</SelectItem>
                                    <SelectItem value="running">运行中</SelectItem>
                                    <SelectItem value="completed">已完成</SelectItem>
                                    <SelectItem value="failed">失败</SelectItem>
                                    <SelectItem value="paused">已暂停</SelectItem>
                                </SelectContent>
                            </Select>

                            <Select value={filterType} onValueChange={setFilterType}>
                                <SelectTrigger className="w-32">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">全部类型</SelectItem>
                                    <SelectItem value="dataset">按数据集</SelectItem>
                                    <SelectItem value="label">按标签</SelectItem>
                                </SelectContent>
                            </Select>

                            <Select value={sortBy} onValueChange={setSortBy}>
                                <SelectTrigger className="w-32">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="createdAt">创建时间</SelectItem>
                                    <SelectItem value="name">任务名称</SelectItem>
                                    <SelectItem value="targetCount">目标数量</SelectItem>
                                    <SelectItem value="generatedCount">已生成</SelectItem>
                                    <SelectItem value="progress">进度</SelectItem>
                                </SelectContent>
                            </Select>

                            <Button variant="outline" size="sm" onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}>
                                <ArrowUpDown className="w-4 h-4" />
                                {sortOrder === "asc" ? "升序" : "降序"}
                            </Button>

                            <div className="flex items-center border rounded-lg">
                                <Button
                                    variant={viewMode === "card" ? "default" : "ghost"}
                                    size="sm"
                                    onClick={() => setViewMode("card")}
                                    className={viewMode === "card" ? "bg-blue-600 hover:bg-blue-700" : ""}
                                >
                                    <Grid3X3 className="w-4 h-4" />
                                </Button>
                                <Button
                                    variant={viewMode === "table" ? "default" : "ghost"}
                                    size="sm"
                                    onClick={() => setViewMode("table")}
                                    className={viewMode === "table" ? "bg-blue-600 hover:bg-blue-700" : ""}
                                >
                                    <List className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>

                        {/* 任务列表 */}
                        {viewMode === "table" ? renderTableView() : renderCardView()}
                    </TabsContent>
                </Tabs>
            </div>
        </TooltipProvider>
    )
}
