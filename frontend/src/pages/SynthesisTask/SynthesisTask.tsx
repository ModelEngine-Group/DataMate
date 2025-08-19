"use client"

import { useState } from "react"
import { Steps } from "antd"
import {
    Plus,
    Eye,
    Trash2,
    Settings,
    Sparkles,
    Clock,
    ArrowLeft,
    ArrowRight,
    Play,
    Edit,
    Copy,
    Save,
    RefreshCw,
    ChevronDown,
    ChevronRight,
    Search,
    CheckCircle,
    AlertCircle,
    Pause,
    FileText,
    Brain,
    MessageSquare,
    Code,
    Layers,
    X,
    DownloadIcon,
    MoreHorizontal,
    Activity,
    ArrowUp,
    ArrowDown,
    Router,
} from "lucide-react"
import DataAnnotation from "../DataAnnotation/components/TextAnnotation"

interface SynthesisTask {
    id: number
    name: string
    type: "qa" | "distillation" | "text" | "multimodal"
    status: "pending" | "running" | "completed" | "failed" | "paused"
    progress: number
    sourceDataset: string
    targetCount: number
    generatedCount: number
    createdAt: string
    template: string
    estimatedTime?: string
    quality?: number
    errorMessage?: string
}

interface Template {
    id: number
    name: string
    type: "preset" | "custom"
    category: string
    prompt: string
    variables: string[]
    description: string
    usageCount: number
    lastUsed?: string
    quality?: number
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

// Add mock files data
const mockFiles = [
    { id: "file1", name: "dataset_part_001.jsonl", size: "2.5MB", type: "JSONL" },
    { id: "file2", name: "dataset_part_002.jsonl", size: "2.3MB", type: "JSONL" },
    { id: "file3", name: "dataset_part_003.jsonl", size: "2.7MB", type: "JSONL" },
    { id: "file4", name: "training_data.txt", size: "1.8MB", type: "TXT" },
    { id: "file5", name: "validation_set.csv", size: "856KB", type: "CSV" },
    { id: "file6", name: "test_samples.json", size: "1.2MB", type: "JSON" },
    { id: "file7", name: "raw_text_001.txt", size: "3.1MB", type: "TXT" },
    { id: "file8", name: "raw_text_002.txt", size: "2.9MB", type: "TXT" },
]

const mockSynthesisTasks: SynthesisTask[] = [
    {
        id: 1,
        name: "文字生成问答对_判断题",
        type: "qa",
        status: "completed",
        progress: 100,
        sourceDataset: "orig_20250724_64082",
        targetCount: 1000,
        generatedCount: 1000,
        createdAt: "2025-01-20",
        template: "判断题生成模板",
        estimatedTime: "已完成",
        quality: 95,
    },
    {
        id: 2,
        name: "知识蒸馏数据集",
        type: "distillation",
        status: "running",
        progress: 65,
        sourceDataset: "teacher_model_outputs",
        targetCount: 5000,
        generatedCount: 3250,
        createdAt: "2025-01-22",
        template: "蒸馏模板v2",
        estimatedTime: "剩余 15 分钟",
        quality: 88,
    },
    {
        id: 3,
        name: "多模态对话生成",
        type: "multimodal",
        status: "failed",
        progress: 25,
        sourceDataset: "image_text_pairs",
        targetCount: 2000,
        generatedCount: 500,
        createdAt: "2025-01-23",
        template: "多模态对话模板",
        errorMessage: "模型API调用失败，请检查配置",
    },
    {
        id: 4,
        name: "金融问答数据生成",
        type: "qa",
        status: "pending",
        progress: 0,
        sourceDataset: "financial_qa_dataset",
        targetCount: 800,
        generatedCount: 0,
        createdAt: "2025-01-24",
        template: "金融问答模板",
        estimatedTime: "等待开始",
        quality: 0,
    },
    {
        id: 5,
        name: "医疗文本蒸馏",
        type: "distillation",
        status: "paused",
        progress: 45,
        sourceDataset: "medical_corpus",
        targetCount: 3000,
        generatedCount: 1350,
        createdAt: "2025-01-21",
        template: "医疗蒸馏模板",
        estimatedTime: "已暂停",
        quality: 92,
    },
]

const mockTemplates: Template[] = [
    {
        id: 1,
        name: "判断题生成模板",
        type: "preset",
        category: "问答对生成",
        prompt: `根据给定的文本内容，生成一个判断题。

文本内容：{text}

请按照以下格式生成：
1. 判断题：[基于文本内容的判断题]
2. 答案：[对/错]
3. 解释：[简要解释为什么这个答案是正确的]

要求：
- 判断题应该基于文本的核心内容
- 答案必须明确且有依据
- 解释要简洁清晰`,
        variables: ["text"],
        description: "根据文本内容生成判断题，适用于教育和培训场景",
        usageCount: 156,
        lastUsed: "2025-01-20",
        quality: 95,
    },
    {
        id: 2,
        name: "选择题生成模板",
        type: "preset",
        category: "问答对生成",
        prompt: `基于以下文本，创建一个多选题：

{text}

请按照以下格式生成：
问题：[基于文本的问题]
A. [选项A]
B. [选项B] 
C. [选项C]
D. [选项D]
正确答案：[A/B/C/D]
解析：[详细解释]

要求：
- 问题要有一定难度
- 选项要有迷惑性
- 正确答案要有充分依据`,
        variables: ["text"],
        description: "生成多选题的标准模板，适用于考试和评估",
        usageCount: 89,
        lastUsed: "2025-01-19",
        quality: 92,
    },
    {
        id: 3,
        name: "知识蒸馏模板",
        type: "preset",
        category: "蒸馏数据集",
        prompt: `作为学生模型，学习教师模型的输出：

输入：{input}
教师输出：{teacher_output}

请模仿教师模型的推理过程和输出格式，生成相似质量的回答。

要求：
- 保持教师模型的推理逻辑
- 输出格式要一致
- 质量要接近教师模型水平`,
        variables: ["input", "teacher_output"],
        description: "用于知识蒸馏的模板，帮助小模型学习大模型的能力",
        usageCount: 234,
        lastUsed: "2025-01-22",
        quality: 88,
    },
    {
        id: 4,
        name: "金融问答模板",
        type: "custom",
        category: "问答对生成",
        prompt: `基于金融领域知识，生成专业问答对：

参考内容：{content}

生成格式：
问题：[专业的金融问题]
答案：[准确的专业回答]
关键词：[相关金融术语]

要求：
- 问题具有实用性
- 答案准确专业
- 符合金融行业标准`,
        variables: ["content"],
        description: "专门用于金融领域的问答对生成",
        usageCount: 45,
        lastUsed: "2025-01-18",
        quality: 89,
    },
    {
        id: 5,
        name: "医疗蒸馏模板",
        type: "custom",
        category: "蒸馏数据集",
        prompt: `医疗知识蒸馏模板：

原始医疗文本：{medical_text}
专家标注：{expert_annotation}

生成医疗知识点：
1. 核心概念：[提取关键医疗概念]
2. 临床意义：[说明临床应用价值]
3. 注意事项：[重要提醒和禁忌]

要求：
- 确保医疗信息准确性
- 遵循医疗伦理规范
- 适合医学教育使用`,
        variables: ["medical_text", "expert_annotation"],
        description: "医疗领域专用的知识蒸馏模板",
        usageCount: 67,
        lastUsed: "2025-01-21",
        quality: 94,
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

export default function DataSynthesisPage() {
    // Add these state variables
    const [selectedFiles, setSelectedFiles] = useState<string[]>([])

    const [activeTab, setActiveTab] = useState("tasks")
    const [showCreateTask, setShowCreateTask] = useState(false)
    const [showTemplateEditor, setShowTemplateEditor] = useState(false)
    const [showAnnotatePage, setShowAnnotatePage] = useState(false)
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
    const [createStep, setCreateStep] = useState(1)
    const [selectedSynthesisTypes, setSelectedSynthesisTypes] = useState<string[]>(["qa_judge"])
    const [expandedTypes, setExpandedTypes] = useState<string[]>(["qa", "distillation"])
    const [searchQuery, setSearchQuery] = useState("")
    const [filterStatus, setFilterStatus] = useState("all")
    const [filterTemplateType, setFilterTemplateType] = useState("all")
    const [sortBy, setSortBy] = useState<"createdAt" | "name">("createdAt")
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")

    // Add a new state variable for showing the debug card:
    const [showDebugCard, setShowDebugCard] = useState(false)
    const [debugStepId, setDebugStepId] = useState<string | null>(null)

    // Update the taskForm state to include new fields
    const [taskForm, setTaskForm] = useState({
        name: "",
        sourceDataset: "",
        targetCount: 1000,
        description: "",
        mergeOriginalDataset: false,
        autoStart: true,
        executionMode: "immediate",
        scheduleStrategy: "",
        outputPath: "",
        enableQualityCheck: false,
        enableNotification: false,
        orchestrationSteps: [
            {
                id: 1,
                name: "开始",
                type: "start",
                position: { x: 100, y: 100 },
            },
            {
                id: 2,
                name: "文字生成问答对_判断题",
                type: "synthesis",
                template: "判断题生成模板",
                config: {
                    model: "gpt-4",
                    temperature: 0.7,
                    maxTokens: 1000,
                    instructions: "该任务为从用户提供的参考文本中抽取出一个判断题，同时输出正确答案。",
                    inputVars: ["text"],
                    outputVars: ["answer", "question"],
                },
                position: { x: 300, y: 100 },
            },
            {
                id: 3,
                name: "结束",
                type: "end",
                position: { x: 500, y: 100 },
            },
        ],
    })

    // 模板编辑状态
    const [templateForm, setTemplateForm] = useState({
        name: "",
        category: "",
        prompt: "",
        variables: [] as string[],
        description: "",
        testInput: "",
        testOutput: "",
    })

    const [tasks, setTasks] = useState<SynthesisTask[]>(mockSynthesisTasks)
    const [templates, setTemplates] = useState<Template[]>(mockTemplates)
    const [datasets] = useState<Dataset[]>(mockDatasets)
    const [isTestingTemplate, setIsTestingTemplate] = useState(false)

    const synthesisTypes = [
        {
            id: "qa",
            name: "生成问答对",
            icon: MessageSquare,
            count: 14,
            expanded: true,
            description: "基于文本生成各类问答对",
            children: [
                {
                    id: "qa_judge",
                    name: "文字生成问答对_判断题",
                    count: 1,
                    description: "生成判断题形式的问答对",
                },
                {
                    id: "qa_choice",
                    name: "文字生成问答对_选择题",
                    count: 0,
                    description: "生成多选题形式的问答对",
                },
                {
                    id: "qa_fill",
                    name: "文字生成问答对_填空题",
                    count: 0,
                    description: "生成填空题形式的问答对",
                },
                {
                    id: "qa_short",
                    name: "相关文本描述问答对_金融领域",
                    count: 0,
                    description: "金融领域的专业问答对",
                },
            ],
        },
        {
            id: "distillation",
            name: "生成蒸馏",
            icon: Brain,
            count: 6,
            expanded: true,
            description: "知识蒸馏数据生成",
            children: [
                {
                    id: "dist_text",
                    name: "相关文本生成蒸馏",
                    count: 0,
                    description: "基于文本的知识蒸馏",
                },
                {
                    id: "dist_qa",
                    name: "问答数据",
                    count: 0,
                    description: "问答形式的蒸馏数据",
                },
                {
                    id: "dist_instruct",
                    name: "相关指令生成蒸馏问题_few-shot",
                    count: 0,
                    description: "Few-shot指令蒸馏",
                },
                {
                    id: "dist_summary",
                    name: "问答数据为基础蒸馏",
                    count: 0,
                    description: "基于问答数据的蒸馏",
                },
                {
                    id: "dist_reasoning",
                    name: "问答数据为基础高质量",
                    count: 0,
                    description: "高质量推理数据蒸馏",
                },
            ],
        },
    ]

    // 过滤任务
    const filteredTasks = tasks.filter((task) => {
        const matchesSearch =
            task.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            task.template.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesStatus = filterStatus === "all" || task.status === filterStatus
        return matchesSearch && matchesStatus
    })

    // 排序任务
    const sortedTasks = [...filteredTasks].sort((a, b) => {
        if (sortBy === "createdAt") {
            const dateA = new Date(a.createdAt).getTime()
            const dateB = new Date(b.createdAt).getTime()
            return sortOrder === "asc" ? dateA - dateB : dateB - dateA
        } else if (sortBy === "name") {
            return sortOrder === "asc" ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name)
        }
        return 0
    })

    // 过滤模板
    const filteredTemplates = templates.filter((template) => {
        const matchesSearch =
            template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            template.description.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesType = filterTemplateType === "all" || template.type === filterTemplateType
        return matchesSearch && matchesType
    })

    const handleCreateTask = () => {
        if (
            !taskForm.name ||
            !taskForm.sourceDataset ||
            selectedFiles.length === 0 ||
            selectedSynthesisTypes.length === 0 ||
            !taskForm.outputPath ||
            !taskForm.targetCount ||
            (taskForm.executionMode === "scheduled" && !taskForm.scheduleStrategy)
        ) {
            return
        }

        const newTask: SynthesisTask = {
            id: Date.now(),
            name: taskForm.name,
            type: selectedSynthesisTypes[0].includes("qa") ? "qa" : "distillation",
            status: taskForm.executionMode === "immediate" ? "pending" : "paused",
            progress: 0,
            sourceDataset: taskForm.sourceDataset,
            targetCount: taskForm.targetCount,
            generatedCount: 0,
            createdAt: new Date().toISOString().split("T")[0],
            template: "自动生成模板",
            estimatedTime: "预计 30 分钟",
        }

        setTasks([newTask, ...tasks])
        setShowCreateTask(false)
        setCreateStep(1)

        // Reset form
        setTaskForm({
            name: "",
            sourceDataset: "",
            targetCount: 1000,
            description: "",
            mergeOriginalDataset: false,
            autoStart: true,
            executionMode: "immediate",
            scheduleStrategy: "",
            outputPath: "",
            enableQualityCheck: false,
            enableNotification: false,
            orchestrationSteps: taskForm.orchestrationSteps,
        })
        setSelectedFiles([])

        // Auto-start simulation if immediate execution
        if (taskForm.executionMode === "immediate") {
            setTimeout(() => {
                setTasks((prev) => prev.map((task) => (task.id === newTask.id ? { ...task, status: "running" } : task)))

                const interval = setInterval(() => {
                    setTasks((prev) =>
                        prev.map((task) => {
                            if (task.id === newTask.id && task.status === "running") {
                                const newProgress = Math.min(task.progress + Math.random() * 8 + 2, 100)
                                const isCompleted = newProgress >= 100
                                return {
                                    ...task,
                                    progress: newProgress,
                                    generatedCount: Math.floor((newProgress / 100) * task.targetCount),
                                    status: isCompleted ? "completed" : "running",
                                    estimatedTime: isCompleted ? "已完成" : `剩余 ${Math.ceil((100 - newProgress) / 10)} 分钟`,
                                }
                            }
                            return task
                        }),
                    )
                }, 1000)

                setTimeout(() => clearInterval(interval), 12000)
            }, 1000)
        }
    }

    const handleSaveTemplate = () => {
        if (!templateForm.name || !templateForm.prompt) {
            return
        }

        if (selectedTemplate) {
            // 编辑现有模板
            setTemplates((prev) =>
                prev.map((t) =>
                    t.id === selectedTemplate.id
                        ? {
                            ...t,
                            ...templateForm,
                            type: "custom" as const,
                            usageCount: t.usageCount,
                            lastUsed: new Date().toISOString().split("T")[0],
                        }
                        : t,
                ),
            )
        } else {
            // 创建新模板
            const newTemplate: Template = {
                id: Date.now(),
                ...templateForm,
                type: "custom",
                usageCount: 0,
                quality: 85,
            }
            setTemplates([newTemplate, ...templates])
        }

        setShowTemplateEditor(false)
        setSelectedTemplate(null)
        resetTemplateForm()
    }

    const resetTemplateForm = () => {
        setTemplateForm({
            name: "",
            category: "",
            prompt: "",
            variables: [],
            description: "",
            testInput: "",
            testOutput: "",
        })
    }

    const handleTestTemplate = async () => {
        if (!templateForm.prompt || !templateForm.testInput) {
            return
        }

        setIsTestingTemplate(true)

        // 模拟API调用
        setTimeout(() => {
            const mockOutput = `基于输入"${templateForm.testInput}"生成的测试结果：

这是一个模拟的输出结果，展示了模板的工作效果。在实际使用中，这里会显示AI模型根据您的模板和输入生成的真实结果。

模板变量已正确替换，输出格式符合预期。`

            setTemplateForm((prev) => ({ ...prev, testOutput: mockOutput }))
            setIsTestingTemplate(false)
        }, 2000)
    }

    const toggleTypeExpansion = (typeId: string) => {
        setExpandedTypes((prev) => (prev.includes(typeId) ? prev.filter((id) => id !== typeId) : [...prev, typeId]))
    }

    const handleSynthesisTypeSelect = (typeId: string) => {
        setSelectedSynthesisTypes((prev) => {
            if (prev.includes(typeId)) {
                return prev.filter((id) => id !== typeId)
            } else {
                return [...prev, typeId]
            }
        })
    }

    const getStatusBadge = (status: string) => {
        const statusConfig = {
            pending: { label: "等待中", color: "bg-yellow-50 text-yellow-700 border-yellow-200", icon: Clock },
            running: { label: "运行中", color: "bg-blue-50 text-blue-700 border-blue-200", icon: Play },
            completed: { label: "已完成", color: "bg-green-50 text-green-700 border-green-200", icon: CheckCircle },
            failed: { label: "失败", color: "bg-red-50 text-red-700 border-red-200", icon: AlertCircle },
            paused: { label: "已暂停", color: "bg-gray-50 text-gray-700 border-gray-200", icon: Pause },
        }
        return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    }

    const getTypeIcon = (type: string) => {
        const iconMap = {
            qa: MessageSquare,
            distillation: Brain,
            text: FileText,
            multimodal: Layers,
        }
        return iconMap[type as keyof typeof iconMap] || FileText
    }

    const getQualityColor = (quality: number) => {
        if (quality >= 90) return "text-green-600 bg-green-50 border-green-200"
        if (quality >= 80) return "text-blue-600 bg-blue-50 border-blue-200"
        if (quality >= 70) return "text-yellow-600 bg-yellow-50 border-yellow-200"
        return "text-red-600 bg-red-50 border-red-200"
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

    const handleSelectAllFiles = () => {
        const filteredFiles = mockFiles.filter((file) => file.name.toLowerCase().includes(searchQuery.toLowerCase()))
        if (selectedFiles.length === filteredFiles.length) {
            setSelectedFiles([])
        } else {
            setSelectedFiles(filteredFiles.map((file) => file.id))
        }
    }

    const handleRemoveSelectedFile = (fileId: string) => {
        setSelectedFiles(selectedFiles.filter((id) => id !== fileId))
    }

    const handleSort = (column: "createdAt" | "name") => {
        if (sortBy === column) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc")
        } else {
            setSortBy(column)
            setSortOrder("desc")
        }
    }

    const renderCreateTaskPage = () => {
        if (createStep === 1) {
            return (
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center justify-between w-full">
                            <div className="flex items-center gap-6">
                                <Button variant="ghost" size="sm" onClick={() => setShowCreateTask(false)} className="hover:bg-white/70">
                                    <ArrowRight className="w-4 h-4 rotate-180 mr-2" />
                                </Button>
                                <h1 className="text-2xl font-bold">创建合成任务</h1>
                            </div>
                            <Steps
                                current={createStep - 1}
                                items={[
                                    {
                                        title: "基本信息",
                                    },
                                    {
                                        title: "算子编排",
                                    },
                                ]}
                                className="mb-4 w-[50%]"
                            />
                        </div>
                    </div>

                    <Card className="shadow-sm border-0 bg-white">
                        <CardContent className="p-6 space-y-6">
                            <h3>基本信息</h3>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold text-gray-700">任务名称 *</Label>
                                        <Input
                                            value={taskForm.name}
                                            onChange={(e) => setTaskForm({ ...taskForm, name: e.target.value })}
                                            placeholder="输入任务名称"
                                            className="h-9 text-sm border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold text-gray-700">目标生成数量 *</Label>
                                        <Input
                                            type="number"
                                            value={taskForm.targetCount}
                                            onChange={(e) => setTaskForm({ ...taskForm, targetCount: Number.parseInt(e.target.value) || 0 })}
                                            placeholder="输入目标生成数量"
                                            min="1"
                                            className="h-9 text-sm border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold text-gray-700">任务描述</Label>
                                        <Textarea
                                            value={taskForm.description}
                                            onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                                            placeholder="描述任务的目的和要求（可选）"
                                            rows={3}
                                            className="resize-none text-sm border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold text-gray-700">源数据集 *</Label>
                                        <Select
                                            value={taskForm.sourceDataset}
                                            onValueChange={(value) => setTaskForm({ ...taskForm, sourceDataset: value })}
                                        >
                                            <SelectTrigger className="h-9 text-sm">
                                                <SelectValue placeholder="选择数据集" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {datasets.map((dataset) => (
                                                    <SelectItem key={dataset.id} value={dataset.id}>
                                                        <div className="flex flex-col py-1">
                                                            <span className="font-medium text-sm">{dataset.name}</span>
                                                            <span className="text-xs text-gray-500">
                                                                {dataset.type} • {dataset.records.toLocaleString()}条 • {dataset.size}
                                                            </span>
                                                        </div>
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    {taskForm.sourceDataset && (
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold text-gray-700">选择文件 *</Label>
                                            <div className="grid grid-cols-2 gap-4">
                                                {/* 文件选择区域 */}
                                                <Card className="border-gray-200">
                                                    <CardContent className="p-3">
                                                        <div className="space-y-3">
                                                            <div className="flex items-center justify-between">
                                                                <div className="relative flex-1">
                                                                    <Search className="w-3 h-3 absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                                                    <Input
                                                                        placeholder="搜索文件..."
                                                                        className="pl-7 h-8 text-sm"
                                                                        value={searchQuery}
                                                                        onChange={(e) => setSearchQuery(e.target.value)}
                                                                    />
                                                                </div>
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    onClick={handleSelectAllFiles}
                                                                    className="ml-2 text-xs bg-transparent"
                                                                >
                                                                    {selectedFiles.length ===
                                                                        mockFiles.filter((file) =>
                                                                            file.name.toLowerCase().includes(searchQuery.toLowerCase()),
                                                                        ).length
                                                                        ? "取消全选"
                                                                        : "全选"}
                                                                </Button>
                                                            </div>
                                                            <ScrollArea className="h-32">
                                                                <div className="space-y-1">
                                                                    {mockFiles
                                                                        .filter((file) => file.name.toLowerCase().includes(searchQuery.toLowerCase()))
                                                                        .map((file) => (
                                                                            <div
                                                                                key={file.id}
                                                                                className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded"
                                                                            >
                                                                                <Checkbox
                                                                                    id={file.id}
                                                                                    checked={selectedFiles.includes(file.id)}
                                                                                    onCheckedChange={(checked) => {
                                                                                        if (checked) {
                                                                                            setSelectedFiles([...selectedFiles, file.id])
                                                                                        } else {
                                                                                            setSelectedFiles(selectedFiles.filter((id) => id !== file.id))
                                                                                        }
                                                                                    }}
                                                                                />
                                                                                <div className="flex-1 min-w-0">
                                                                                    <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                                                                                    <p className="text-xs text-gray-500">
                                                                                        {file.size} • {file.type}
                                                                                    </p>
                                                                                </div>
                                                                            </div>
                                                                        ))}
                                                                </div>
                                                            </ScrollArea>
                                                        </div>
                                                    </CardContent>
                                                </Card>

                                                {/* 已选文件列表 */}
                                                <Card className="border-gray-200">
                                                    <CardHeader className="pb-2">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-sm font-medium">已选文件</span>
                                                            <Badge variant="secondary" className="text-xs">
                                                                {selectedFiles.length}
                                                            </Badge>
                                                        </div>
                                                    </CardHeader>
                                                    <CardContent className="p-3 pt-0">
                                                        <ScrollArea className="h-32">
                                                            <div className="space-y-1">
                                                                {selectedFiles.length === 0 ? (
                                                                    <div className="text-center py-4 text-xs text-gray-500">暂未选择文件</div>
                                                                ) : (
                                                                    selectedFiles.map((fileId) => {
                                                                        const file = mockFiles.find((f) => f.id === fileId)
                                                                        if (!file) return null
                                                                        return (
                                                                            <div
                                                                                key={fileId}
                                                                                className="flex items-center justify-between p-2 bg-blue-50 rounded border border-blue-200"
                                                                            >
                                                                                <div className="flex-1 min-w-0">
                                                                                    <p className="text-sm font-medium text-blue-900 truncate">{file.name}</p>
                                                                                    <p className="text-xs text-blue-600">
                                                                                        {file.size} • {file.type}
                                                                                    </p>
                                                                                </div>
                                                                                <Button
                                                                                    variant="ghost"
                                                                                    size="sm"
                                                                                    onClick={() => handleRemoveSelectedFile(fileId)}
                                                                                    className="p-1 h-6 w-6 hover:bg-blue-100"
                                                                                >
                                                                                    <X className="w-3 h-3" />
                                                                                </Button>
                                                                            </div>
                                                                        )
                                                                    })
                                                                )}
                                                            </div>
                                                        </ScrollArea>
                                                    </CardContent>
                                                </Card>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                            <h3>任务配置</h3>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <div className="space-y-3">
                                        <Label className="text-sm font-semibold text-gray-700">执行方式 *</Label>
                                        <RadioGroup
                                            value={taskForm.executionMode || "immediate"}
                                            onValueChange={(value) => setTaskForm({ ...taskForm, executionMode: value })}
                                            className="space-y-2"
                                        >
                                            <div className="flex items-center space-x-2 p-3 border rounded-xl hover:bg-gray-50 transition-colors">
                                                <RadioGroupItem value="immediate" id="immediate" />
                                                <div className="flex-1">
                                                    <Label htmlFor="immediate" className="text-sm font-medium cursor-pointer">
                                                        立即执行
                                                    </Label>
                                                    <p className="text-xs text-gray-500 mt-1">任务创建后立即开始执行</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center space-x-2 p-3 border rounded-xl hover:bg-gray-50 transition-colors">
                                                <RadioGroupItem value="scheduled" id="scheduled" />
                                                <div className="flex-1">
                                                    <Label htmlFor="scheduled" className="text-sm font-medium cursor-pointer">
                                                        周期执行
                                                    </Label>
                                                    <p className="text-xs text-gray-500 mt-1">按照设定的周期定时执行任务</p>
                                                </div>
                                            </div>
                                        </RadioGroup>
                                    </div>

                                    {taskForm.executionMode === "scheduled" && (
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold text-gray-700">执行策略 *</Label>
                                            <Select
                                                value={taskForm.scheduleStrategy}
                                                onValueChange={(value) => setTaskForm({ ...taskForm, scheduleStrategy: value })}
                                            >
                                                <SelectTrigger className="h-9 text-sm">
                                                    <SelectValue placeholder="选择执行策略" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="daily">每日执行</SelectItem>
                                                    <SelectItem value="weekly">每周执行</SelectItem>
                                                    <SelectItem value="monthly">每月执行</SelectItem>
                                                    <SelectItem value="custom">自定义周期</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold text-gray-700">存放路径 *</Label>
                                        <Input
                                            value={taskForm.outputPath || ""}
                                            onChange={(e) => setTaskForm({ ...taskForm, outputPath: e.target.value })}
                                            placeholder="输入结果存放路径，如：/data/synthesis/output"
                                            className="h-9 text-sm border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                                        />
                                        <p className="text-xs text-gray-500">指定合成结果的存储位置，支持本地路径和云存储路径</p>
                                    </div>

                                    <div className="space-y-3">
                                        <Label className="text-sm font-semibold text-gray-700">高级选项</Label>
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between p-3 border rounded-xl bg-gray-50">
                                                <div>
                                                    <Label className="text-sm font-semibold text-gray-700">启用质量检查</Label>
                                                    <p className="text-xs text-gray-500 mt-1">对合成结果进行自动质量评估</p>
                                                </div>
                                                <Switch
                                                    checked={taskForm.enableQualityCheck || false}
                                                    onCheckedChange={(checked) => setTaskForm({ ...taskForm, enableQualityCheck: checked })}
                                                />
                                            </div>

                                            <div className="flex items-center justify-between p-3 border rounded-xl bg-blue-50">
                                                <div>
                                                    <Label className="text-sm font-semibold text-gray-700">发送完成通知</Label>
                                                    <p className="text-xs text-gray-500 mt-1">任务完成后发送邮件或消息通知</p>
                                                </div>
                                                <Switch
                                                    checked={taskForm.enableNotification || false}
                                                    onCheckedChange={(checked) => setTaskForm({ ...taskForm, enableNotification: checked })}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-end pt-4 border-t">
                                <Button
                                    onClick={() => setCreateStep(2)}
                                    disabled={
                                        !taskForm.name || !taskForm.sourceDataset || selectedFiles.length === 0 || !taskForm.targetCount
                                    }
                                    className="px-6 py-2 text-sm font-semibold bg-blue-600 hover:bg-blue-700 shadow-lg"
                                >
                                    下一步
                                    <ArrowRight className="w-4 h-4 ml-2" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )
        }

        if (createStep === 2) {
            return (
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center justify-between w-full">
                            <div className="flex items-center gap-6">
                                <Button variant="ghost" size="sm" onClick={() => setCreateStep(1)} className="hover:bg-white/70">
                                    <ArrowRight className="w-4 h-4 rotate-180 mr-2" />
                                </Button>
                                <h1 className="text-2xl font-bold">创建合成任务</h1>
                            </div>
                            <Steps
                                current={createStep - 1}
                                items={[
                                    {
                                        title: "基本信息",
                                    },
                                    {
                                        title: "算子编排",
                                    },
                                ]}
                                className="mb-4 w-[50%]"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-12 gap-6 min-h-[500px]">
                        {/* 左侧合成指令 */}
                        <div className="col-span-4 space-y-4">
                            <Card className="shadow-sm border-0 bg-white">
                                <CardHeader>
                                    <CardTitle className="text-base">合成指令</CardTitle>
                                </CardHeader>
                                <CardContent className="p-4">
                                    <div className="space-y-3 mb-4">
                                        <div className="relative">
                                            <Search className="w-3 h-3 absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                            <Input placeholder="搜索名称、分类搜索" className="pl-7 text-xs h-8" />
                                        </div>
                                    </div>
                                    <ScrollArea className="h-400">
                                        <div className="space-y-2">
                                            {synthesisTypes.map((type) => {
                                                const IconComponent = type.icon
                                                return (
                                                    <div key={type.id} className="space-y-1">
                                                        <div
                                                            className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                                                            onClick={() => toggleTypeExpansion(type.id)}
                                                        >
                                                            <div className="w-5 h-5 bg-green-500 rounded-lg flex items-center justify-center shadow-sm">
                                                                {expandedTypes.includes(type.id) ? (
                                                                    <ChevronDown className="w-3 h-3 text-white" />
                                                                ) : (
                                                                    <ChevronRight className="w-3 h-3 text-white" />
                                                                )}
                                                            </div>
                                                            <span className="font-medium text-xs">
                                                                {type.name}({type.count})
                                                            </span>
                                                        </div>

                                                        {expandedTypes.includes(type.id) && (
                                                            <div className="ml-7 space-y-1">
                                                                {type.children.map((child) => (
                                                                    <div
                                                                        key={child.id}
                                                                        className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer text-xs transition-colors ${selectedSynthesisTypes.includes(child.id)
                                                                            ? "bg-blue-50 text-blue-700 border border-blue-200"
                                                                            : "hover:bg-gray-50"
                                                                            }`}
                                                                        onClick={() => handleSynthesisTypeSelect(child.id)}
                                                                    >
                                                                        <Checkbox
                                                                            checked={selectedSynthesisTypes.includes(child.id)}
                                                                            onChange={() => handleSynthesisTypeSelect(child.id)}
                                                                        />
                                                                        <span className="flex-1">{child.name}</span>
                                                                        <span className="text-gray-400">({child.count})</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </ScrollArea>
                                </CardContent>
                            </Card>
                        </div>

                        {/* 右侧合成编排 */}
                        <div className="col-span-8">
                            <Card className="h-full shadow-sm border-0 bg-white">
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        {" "}
                                        <CardTitle>合成步骤编排({selectedSynthesisTypes.length})</CardTitle>
                                        <div className="flex items-center gap-2">
                                            <Button variant="outline" size="sm" className="hover:bg-white bg-transparent text-xs">
                                                <RefreshCw className="w-3 h-3 mr-1" />
                                                选择合成模板
                                            </Button>
                                            <Button variant="outline" size="sm" className="hover:bg-white bg-transparent text-xs">
                                                <Eye className="w-3 h-3 mr-1" />
                                                启用调测
                                            </Button>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-4">
                                    <ScrollArea className="h-400">
                                        <div className="space-y-4">
                                            {/* 开始节点 */}
                                            <div className="relative">
                                                <Card className="border-green-200 bg-green-50 shadow-sm">
                                                    <CardContent className="p-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-medium shadow-lg">
                                                                开
                                                            </div>
                                                            <span className="font-medium text-sm">开始</span>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            </div>

                                            {/* 合成步骤 */}
                                            {selectedSynthesisTypes.map((typeId, index) => {
                                                const typeInfo = synthesisTypes.flatMap((t) => t.children).find((c) => c.id === typeId)
                                                if (!typeInfo) return null

                                                return (
                                                    <div key={typeId} className="relative">
                                                        <div className="absolute -top-4 left-4 w-px h-4 bg-gray-300"></div>
                                                        <Card className="border-blue-200 bg-blue-50 shadow-sm">
                                                            <CardContent className="p-4">
                                                                <div className="flex items-start gap-3">
                                                                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-medium shadow-lg">
                                                                        {index + 1}
                                                                    </div>
                                                                    <div className="flex-1 space-y-3">
                                                                        <div className="flex items-center justify-between">
                                                                            <span className="font-medium text-sm">{typeInfo.name}</span>
                                                                            <div className="flex items-center gap-1">
                                                                                <Button
                                                                                    variant="outline"
                                                                                    size="sm"
                                                                                    className="hover:bg-white bg-transparent p-1"
                                                                                >
                                                                                    <Copy className="w-3 h-3" />
                                                                                </Button>
                                                                                <Button
                                                                                    variant="outline"
                                                                                    size="sm"
                                                                                    className="hover:bg-white bg-transparent p-1"
                                                                                >
                                                                                    <Edit className="w-3 h-3" />
                                                                                </Button>
                                                                                <Button
                                                                                    variant="outline"
                                                                                    size="sm"
                                                                                    className="hover:bg-white bg-transparent p-1"
                                                                                >
                                                                                    <Trash2 className="w-3 h-3" />
                                                                                </Button>
                                                                                <Button
                                                                                    variant="outline"
                                                                                    size="sm"
                                                                                    className="hover:bg-white bg-transparent p-1"
                                                                                >
                                                                                    <MoreHorizontal className="w-3 h-3" />
                                                                                </Button>
                                                                            </div>
                                                                        </div>

                                                                        <div className="text-xs text-gray-600 bg-white p-2 rounded-lg border">
                                                                            该任务为从用户提供的参考文本中抽取出一个判断题，同时输出正确答案。
                                                                        </div>

                                                                        <div className="grid grid-cols-2 gap-3">
                                                                            <div>
                                                                                <Label className="text-xs font-medium text-gray-600">模型</Label>
                                                                                <Select defaultValue="未选择">
                                                                                    <SelectTrigger className="h-7 mt-1 text-xs">
                                                                                        <SelectValue />
                                                                                    </SelectTrigger>
                                                                                    <SelectContent>
                                                                                        <SelectItem value="未选择">未选择</SelectItem>
                                                                                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                                                                                        <SelectItem value="gpt-3.5">GPT-3.5</SelectItem>
                                                                                    </SelectContent>
                                                                                </Select>
                                                                            </div>
                                                                            <div>
                                                                                <Label className="text-xs font-medium text-gray-600">配置参数</Label>
                                                                                <Button
                                                                                    variant="outline"
                                                                                    size="sm"
                                                                                    className="h-7 w-full mt-1 bg-white hover:bg-gray-50 text-xs"
                                                                                    onClick={() => {
                                                                                        setDebugStepId(typeId)
                                                                                        setShowDebugCard(true)
                                                                                    }}
                                                                                >
                                                                                    配置参数
                                                                                </Button>
                                                                            </div>
                                                                        </div>

                                                                        <div>
                                                                            <Label className="text-xs font-medium text-gray-600">指令</Label>
                                                                            <div className="text-xs text-gray-500 mt-1 bg-white p-2 rounded border">
                                                                                该任务为从用户提供的参考文本中抽取出一个判断题，同时输出正确答案。
                                                                            </div>
                                                                        </div>

                                                                        <div className="grid grid-cols-2 gap-3">
                                                                            <div>
                                                                                <Label className="text-xs font-medium text-gray-600">输入变量</Label>
                                                                                <div className="flex items-center gap-1 mt-1">
                                                                                    <Badge variant="outline" className="text-xs bg-white">
                                                                                        text 参考文本
                                                                                    </Badge>
                                                                                </div>
                                                                            </div>
                                                                            <div>
                                                                                <Label className="text-xs font-medium text-gray-600">输出变量</Label>
                                                                                <div className="flex items-center gap-1 mt-1">
                                                                                    <Badge className="text-xs bg-blue-100 text-blue-800">answer 回答</Badge>
                                                                                    <Badge className="text-xs bg-blue-100 text-blue-800">question 问题</Badge>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </CardContent>
                                                        </Card>
                                                    </div>
                                                )
                                            })}

                                            {/* 结束节点 */}
                                            <div className="relative">
                                                <div className="absolute -top-4 left-4 w-px h-4 bg-gray-300"></div>
                                                <Card className="border-gray-200 bg-gray-50 shadow-sm">
                                                    <CardContent className="p-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-8 h-8 bg-gray-500 text-white rounded-full flex items-center justify-center text-xs font-medium shadow-lg">
                                                                结
                                                            </div>
                                                            <span className="font-medium text-sm">结束</span>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            </div>
                                        </div>
                                    </ScrollArea>

                                    <div className="flex justify-between pt-4 border-t">
                                        <Button variant="outline" onClick={() => setCreateStep(1)} className="px-4 py-2 text-sm">
                                            <ArrowLeft className="w-4 h-4 mr-2" />
                                            上一步
                                        </Button>
                                        <Button
                                            onClick={handleCreateTask}
                                            disabled={
                                                !taskForm.name ||
                                                !taskForm.sourceDataset ||
                                                selectedFiles.length === 0 ||
                                                selectedSynthesisTypes.length === 0 ||
                                                !taskForm.outputPath ||
                                                !taskForm.targetCount ||
                                                (taskForm.executionMode === "scheduled" && !taskForm.scheduleStrategy)
                                            }
                                            className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                                        >
                                            <Play className="w-4 h-4 mr-2" />
                                            创建任务
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>

                    {/* Debug Card */}
                    {showDebugCard &&
                        debugStepId &&
                        (
                            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                                <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl">
                                    <CardHeader className="bg-orange-50 border-b">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <CardTitle className="flex items-center gap-2 text-lg">
                                                    <Settings className="w-4 h-4" />
                                                    流程调测 - {synthesisTypes.flatMap((t) => t.children).find((c) => c.id === debugStepId)?.name}
                                                </CardTitle>
                                            </div>
                                            <Button
                                                variant="outline"
                                                onClick={() => {
                                                    setShowDebugCard(false)
                                                    setDebugStepId(null)
                                                }}
                                                className="hover:bg-white"
                                            >
                                                <X className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="p-0">
                                        <div className="grid grid-cols-2 h-[70vh]">
                                            {/* Left Panel - Configuration */}
                                            <div className="border-r bg-gray-50 p-4 overflow-y-auto">
                                                <div className="space-y-4">
                                                    <div>
                                                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                                                            <Settings className="w-4 h-4" />
                                                            参数配置
                                                        </h4>

                                                        <div className="space-y-3">
                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">模型选择</Label>
                                                                <Select defaultValue="gpt-4">
                                                                    <SelectTrigger className="h-8 text-sm">
                                                                        <SelectValue />
                                                                    </SelectTrigger>
                                                                    <SelectContent>
                                                                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                                                                        <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                                                                        <SelectItem value="claude-3">Claude-3</SelectItem>
                                                                        <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                                                                    </SelectContent>
                                                                </Select>
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">Temperature</Label>
                                                                <div className="flex items-center gap-2">
                                                                    <Input
                                                                        type="number"
                                                                        defaultValue="0.7"
                                                                        min="0"
                                                                        max="2"
                                                                        step="0.1"
                                                                        className="h-8 text-sm"
                                                                    />
                                                                    <span className="text-xs text-gray-500">0.0-2.0</span>
                                                                </div>
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">Max Tokens</Label>
                                                                <Input type="number" defaultValue="1000" min="1" max="4000" className="h-8 text-sm" />
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">Top P</Label>
                                                                <div className="flex items-center gap-2">
                                                                    <Input
                                                                        type="number"
                                                                        defaultValue="1.0"
                                                                        min="0"
                                                                        max="1"
                                                                        step="0.1"
                                                                        className="h-8 text-sm"
                                                                    />
                                                                    <span className="text-xs text-gray-500">0.0-1.0</span>
                                                                </div>
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">Frequency Penalty</Label>
                                                                <div className="flex items-center gap-2">
                                                                    <Input
                                                                        type="number"
                                                                        defaultValue="0.0"
                                                                        min="-2"
                                                                        max="2"
                                                                        step="0.1"
                                                                        className="h-8 text-sm"
                                                                    />
                                                                    <span className="text-xs text-gray-500">-2.0-2.0</span>
                                                                </div>
                                                            </div>
                                                            \
                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">Presence Penalty</Label>
                                                                <div className="flex items-center gap-2">
                                                                    <Input
                                                                        type="number"
                                                                        defaultValue="0.0"
                                                                        min="-2"
                                                                        max="2"
                                                                        step="0.1"
                                                                        className="h-8 text-sm"
                                                                    />
                                                                    <span className="text-xs text-gray-500">-2.0-2.0</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <Separator />

                                                    <div>
                                                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                                                            <Code className="w-4 h-4" />
                                                            指令模板
                                                        </h4>

                                                        <div className="space-y-3">
                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">系统指令</Label>
                                                                <Textarea
                                                                    defaultValue="你是一个专业的数据合成助手，请根据给定的文本内容生成高质量的判断题。"
                                                                    rows={2}
                                                                    className="resize-none text-xs"
                                                                />
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">用户指令模板</Label>
                                                                <Textarea
                                                                    defaultValue={`根据给定的文本内容，生成一个判断题。

文本内容：{text}

请按照以下格式生成：
1. 判断题：[基于文本内容的判断题]
2. 答案：[对/错]
3. 解释：[简要解释为什么这个答案是正确的]

要求：
- 判断题应该基于文本的核心内容
- 答案必须明确且有依据
- 解释要简洁清晰`}
                                                                    rows={8}
                                                                    className="resize-none text-xs font-mono"
                                                                />
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">输入变量</Label>
                                                                <div className="flex flex-wrap gap-1">
                                                                    <Badge variant="outline" className="bg-blue-50 text-blue-700 text-xs">
                                                                        text
                                                                    </Badge>
                                                                </div>
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">输出变量</Label>
                                                                <div className="flex flex-wrap gap-1">
                                                                    <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                                                        question
                                                                    </Badge>
                                                                    <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                                                        answer
                                                                    </Badge>
                                                                    <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                                                        explanation
                                                                    </Badge>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Right Panel - Testing */}
                                            <div className="p-4 overflow-y-auto">
                                                <div className="space-y-4">
                                                    <div>
                                                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                                                            <Play className="w-4 h-4" />
                                                            调测验证
                                                        </h4>

                                                        <div className="space-y-3">
                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">测试输入</Label>
                                                                <Textarea
                                                                    placeholder="输入测试文本内容..."
                                                                    defaultValue="人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。"
                                                                    rows={4}
                                                                    className="resize-none text-xs"
                                                                />
                                                            </div>

                                                            <div className="flex gap-2">
                                                                <Button className="flex-1 bg-orange-500 hover:bg-orange-600 text-sm">
                                                                    <Play className="w-3 h-3 mr-1" />
                                                                    开始调测
                                                                </Button>
                                                                <Button variant="outline" className="text-sm bg-transparent">
                                                                    <RefreshCw className="w-3 h-3 mr-1" />
                                                                    重置
                                                                </Button>
                                                            </div>

                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">调测输出</Label>
                                                                <div className="bg-gray-50 border rounded-lg p-3 min-h-[150px]">
                                                                    <div className="space-y-2 text-xs">
                                                                        <div>
                                                                            <span className="font-medium text-gray-700">判断题：</span>
                                                                            <span className="text-gray-900">人工智能是计算机科学的一个分支。</span>
                                                                        </div>
                                                                        <div>
                                                                            <span className="font-medium text-gray-700">答案：</span>
                                                                            <Badge className="ml-1 bg-green-100 text-green-800 text-xs">对</Badge>
                                                                        </div>
                                                                        <div>
                                                                            <span className="font-medium text-gray-700">解释：</span>
                                                                            <span className="text-gray-900">
                                                                                根据文本内容，人工智能确实是计算机科学的一个分支，这是文本中明确提到的信息。
                                                                            </span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            <div className="grid grid-cols-2 gap-3 text-xs">
                                                                <div className="space-y-1">
                                                                    <span className="text-gray-500">响应时间</span>
                                                                    <span className="font-semibold">1.2秒</span>
                                                                </div>
                                                                <div className="space-y-1">
                                                                    <span className="text-gray-500">Token消耗</span>
                                                                    <span className="font-semibold">156 tokens</span>
                                                                </div>
                                                                <div className="space-y-1">
                                                                    <span className="text-gray-500">成功率</span>
                                                                    <span className="font-semibold text-green-600">100%</span>
                                                                </div>
                                                                <div className="space-y-1">
                                                                    <span className="text-gray-500">质量评分</span>
                                                                    <span className="font-semibold text-blue-600">95分</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <Separator />

                                                    <div>
                                                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                                                            <Activity className="w-4 h-4" />
                                                            批量测试
                                                        </h4>

                                                        <div className="space-y-3">
                                                            <div className="space-y-1">
                                                                <Label className="text-xs font-medium">测试样本数量</Label>
                                                                <Select defaultValue="10">
                                                                    <SelectTrigger className="h-8 text-sm">
                                                                        <SelectValue />
                                                                    </SelectTrigger>
                                                                    <SelectContent>
                                                                        <SelectItem value="5">5个样本</SelectItem>
                                                                        <SelectItem value="10">10个样本</SelectItem>
                                                                        <SelectItem value="20">20个样本</SelectItem>
                                                                        <SelectItem value="50">50个样本</SelectItem>
                                                                    </SelectContent>
                                                                </Select>
                                                            </div>

                                                            <Button variant="outline" className="w-full bg-transparent text-sm">
                                                                <Activity className="w-3 h-3 mr-1" />
                                                                开始批量测试
                                                            </Button>

                                                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                                                <div className="flex items-center gap-2 mb-2">
                                                                    <CheckCircle className="w-3 h-3 text-blue-600" />
                                                                    <span className="text-xs font-medium text-blue-800">批量测试结果</span>
                                                                </div>
                                                                <div className="grid grid-cols-2 gap-3 text-xs">
                                                                    <div>
                                                                        <span className="text-blue-600">成功样本：</span>
                                                                        <span className="font-semibold text-blue-800">9/10</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="text-blue-600">平均质量：</span>
                                                                        <span className="font-semibold text-blue-800">92分</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="text-blue-600">平均耗时：</span>
                                                                        <span className="font-semibold text-blue-800">1.4秒</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="text-blue-600">总消耗：</span>
                                                                        <span className="font-semibold text-blue-800">1,420 tokens</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                    <div className="border-t p-4 bg-gray-50">
                                        <div className="flex justify-between">
                                            <Button variant="outline" className="text-sm bg-transparent">
                                                <Save className="w-3 h-3 mr-1" />
                                                保存配置
                                            </Button>
                                            <div className="flex gap-2">
                                                <Button
                                                    variant="outline"
                                                    onClick={() => {
                                                        setShowDebugCard(false)
                                                        setDebugStepId(null)
                                                    }}
                                                    className="text-sm"
                                                >
                                                    取消
                                                </Button>
                                                <Button className="bg-orange-500 hover:bg-orange-600 text-sm">
                                                    <CheckCircle className="w-3 h-3 mr-1" />
                                                    应用配置
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            </div>
                        )
                    }
                </div >
            )
        }
    }

    const renderTemplateEditor = () => (
        <Card className="shadow-sm border-0 bg-white">
            <CardHeader className="bg-purple-50 border-b">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <FileText className="w-4 h-4" />
                            {selectedTemplate ? "编辑模板" : "创建新模板"}
                        </CardTitle>
                    </div>
                    <Button variant="outline" onClick={() => setShowTemplateEditor(false)} className="hover:bg-white">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        返回
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">s
                        <Label className="text-sm font-semibold text-gray-700">模板名称 *</Label>
                        <Input
                            value={templateForm.name}
                            onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                            placeholder="输入模板名称"
                            className="h-9 text-sm border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label className="text-sm font-semibold text-gray-700">分类 *</Label>
                        <Select
                            value={templateForm.category}
                            onValueChange={(value) => setTemplateForm({ ...templateForm, category: value })}
                        >
                            <SelectTrigger className="h-9 text-sm">
                                <SelectValue placeholder="选择分类" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="问答对生成">问答对生成</SelectItem>
                                <SelectItem value="蒸馏数据集">蒸馏数据集</SelectItem>
                                <SelectItem value="文本生成">文本生成</SelectItem>
                                <SelectItem value="多模态生成">多模态生成</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="space-y-2">
                    <Label className="text-sm font-semibold text-gray-700">模板描述</Label>
                    <Input
                        value={templateForm.description}
                        onChange={(e) => setTemplateForm({ ...templateForm, description: e.target.value })}
                        placeholder="简要描述模板的用途和特点"
                        className="h-9 text-sm border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                    />
                </div>

                <div className="space-y-2">
                    <Label className="text-sm font-semibold text-gray-700">Prompt内容 *</Label>
                    <Textarea
                        value={templateForm.prompt}
                        onChange={(e) => setTemplateForm({ ...templateForm, prompt: e.target.value })}
                        placeholder="输入prompt内容，使用 {变量名} 格式定义变量"
                        rows={10}
                        className="font-mono text-xs resize-none border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                    />
                    <p className="text-xs text-gray-500">
                        提示：使用 {"{变量名}"} 格式定义变量，例如 {"{text}"} 或 {"{input}"}
                    </p>
                </div>

                <div className="space-y-3">
                    <Label className="text-sm font-semibold text-gray-700">变量管理</Label>
                    <div className="flex flex-wrap gap-2 min-h-[50px] p-3 border rounded-xl bg-gray-50">
                        {templateForm.variables.map((variable, index) => (
                            <Badge key={index} variant="outline" className="flex items-center gap-1 bg-white px-2 py-1 text-xs">
                                <Code className="w-3 h-3" />
                                {variable}
                                <button
                                    onClick={() =>
                                        setTemplateForm({
                                            ...templateForm,
                                            variables: templateForm.variables.filter((_, i) => i !== index),
                                        })
                                    }
                                    className="text-gray-500 hover:text-gray-700 ml-1"
                                >
                                    <X className="w-3 h-3" />
                                </button>
                            </Badge>
                        ))}
                        {templateForm.variables.length === 0 && (
                            <span className="text-xs text-gray-400">暂无变量，在Prompt中使用 {"{变量名}"} 格式定义</span>
                        )}
                    </div>
                    <div className="flex gap-2">
                        <Input
                            placeholder="添加变量名（如：text, input, question）"
                            className="h-8 text-sm"
                            onKeyPress={(e) => {
                                if (e.key === "Enter") {
                                    const value = (e.target as HTMLInputElement).value.trim()
                                    if (value && !templateForm.variables.includes(value)) {
                                        setTemplateForm({
                                            ...templateForm,
                                            variables: [...templateForm.variables, value],
                                        })
                                            ; (e.target as HTMLInputElement).value = ""
                                    }
                                }
                            }}
                        />
                        <Button
                            variant="outline"
                            onClick={() => {
                                const input = document.querySelector('input[placeholder*="添加变量名"]') as HTMLInputElement
                                const value = input?.value.trim()
                                if (value && !templateForm.variables.includes(value)) {
                                    setTemplateForm({
                                        ...templateForm,
                                        variables: [...templateForm.variables, value],
                                    })
                                    input.value = ""
                                }
                            }}
                            className="px-4 text-sm"
                        >
                            <Plus className="w-3 h-3 mr-1" />
                            添加
                        </Button>
                    </div>
                </div>

                {/* 模板测试 */}
                <Separator />
                <div className="space-y-4">
                    <h4 className="font-semibold text-base flex items-center gap-2">
                        <Play className="w-4 h-4" />
                        模板测试
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label className="text-sm font-semibold text-gray-700">测试输入</Label>
                            <Textarea
                                value={templateForm.testInput}
                                onChange={(e) => setTemplateForm({ ...templateForm, testInput: e.target.value })}
                                placeholder="输入测试数据"
                                rows={5}
                                className="resize-none text-sm border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-semibold text-gray-700">测试输出</Label>
                            <Textarea
                                value={templateForm.testOutput}
                                readOnly
                                placeholder="点击测试按钮查看输出结果"
                                rows={5}
                                className="resize-none bg-gray-50 text-sm"
                            />
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        onClick={handleTestTemplate}
                        disabled={!templateForm.prompt || !templateForm.testInput || isTestingTemplate}
                        className="px-4 py-2 text-sm bg-transparent"
                    >
                        {isTestingTemplate ? (
                            <>
                                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                                测试中...
                            </>
                        ) : (
                            <>
                                <Play className="w-3 h-3 mr-1" />
                                测试模板
                            </>
                        )}
                    </Button>
                </div>

                <div className="flex gap-2 pt-4 border-t">
                    <Button
                        onClick={handleSaveTemplate}
                        disabled={!templateForm.name || !templateForm.prompt || !templateForm.category}
                        className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                    >
                        <Save className="w-3 h-3 mr-1" />
                        保存模板
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => {
                            setShowTemplateEditor(false)
                            setSelectedTemplate(null)
                            resetTemplateForm()
                        }}
                        className="px-4 py-2 text-sm"
                    >
                        取消
                    </Button>
                </div>
            </CardContent>
        </Card>
    )

    if (showCreateTask) {
        return (
            <div className="min-h-screen bg-gray-50">
                <div className="space-y-6 p-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-gray-900">创建合成任务</h2>
                    </div>
                    {renderCreateTaskPage()}
                </div>
            </div>
        )
    }

    if (showTemplateEditor) {
        return (
            <div className="min-h-screen bg-gray-50">
                <div className="space-y-6 p-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-gray-900">指令模板管理</h2>
                    </div>
                    {renderTemplateEditor()}
                </div>
            </div>
        )
    }
    if (showAnnotatePage) {
        return <div>
            <div className="flex">
                <Button variant="ghost" size="sm" onClick={() => setShowAnnotatePage(false)} className="hover:bg-white/70">
                    <ArrowRight className="w-4 h-4 rotate-180 mr-2" />
                </Button>
            </div>
            <DataAnnotation task={undefined} currentFileIndex={0} onSaveAndNext={function (): void {
                throw new Error("Function not implemented.")
            }} onSkipAndNext={function (): void {
                throw new Error("Function not implemented.")
            }} />
        </div>
    }

    return (
        <TooltipProvider>
            <div className="min-h-screen bg-gray-50">
                <div className="space-y-6 p-6">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <h2 className="text-xl font-bold text-gray-900">数据合成</h2>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                onClick={() => setShowCreateTask(true)}
                            >
                                <Plus className="w-3 h-3 mr-1" />
                                创建合成任务
                            </Button>
                        </div>
                    </div>

                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                        {/* Updated TabsList with image-style design */}
                        <div className="mb-6">
                            <div className="flex items-center border-b border-gray-200 bg-white rounded-t-lg">
                                <button
                                    onClick={() => setActiveTab("tasks")}
                                    className={`relative px-6 py-3 text-sm font-medium transition-all duration-200 ${activeTab === "tasks"
                                        ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
                                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                        }`}
                                >
                                    <div className="flex items-center gap-2">
                                        <span>合成任务</span>
                                        <Badge variant="secondary" className="ml-1 text-xs">
                                            {sortedTasks.length}
                                        </Badge>
                                    </div>
                                </button>

                                <button
                                    onClick={() => setActiveTab("templates")}
                                    className={`relative px-6 py-3 text-sm font-medium transition-all duration-200 ${activeTab === "templates"
                                        ? "text-purple-600 border-b-2 border-purple-600 bg-purple-50"
                                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                        }`}
                                >
                                    <div className="flex items-center gap-2">
                                        <span>指令模板</span>
                                        <Badge variant="secondary" className="ml-1 text-xs">
                                            {filteredTemplates.length}
                                        </Badge>
                                    </div>
                                </button>
                            </div>
                        </div>

                        <TabsContent value="tasks" className="space-y-6">
                            {/* 搜索和筛选 */}
                            <Card className="shadow-sm border-0 bg-white/80 backdrop-blur-sm">
                                <CardContent className="p-4">
                                    <div className="flex flex-col md:flex-row gap-3">
                                        <div className="relative flex-1">
                                            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                            <Input
                                                placeholder="搜索任务名称或模板..."
                                                className="pl-9 h-9 text-sm border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 bg-white"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                            />
                                        </div>
                                        <Select value={filterStatus} onValueChange={setFilterStatus}>
                                            <SelectTrigger className="w-full md:w-40 h-9 text-sm bg-white">
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
                                    </div>
                                </CardContent>
                            </Card>

                            {/* 任务表格 */}
                            <Card className="shadow-sm border-0 bg-white">
                                <CardContent className="p-0">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="border-b border-gray-200">
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-6">
                                                    <Button
                                                        variant="ghost"
                                                        onClick={() => handleSort("name")}
                                                        className="h-auto p-0 font-semibold text-gray-700 hover:bg-transparent"
                                                    >
                                                        任务名称
                                                        {sortBy === "name" &&
                                                            (sortOrder === "asc" ? (
                                                                <ArrowUp className="w-3 h-3 ml-1" />
                                                            ) : (
                                                                <ArrowDown className="w-3 h-3 ml-1" />
                                                            ))}
                                                    </Button>
                                                </TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">类型</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">状态</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">进度</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">源数据集</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">生成数量</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">质量评分</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">
                                                    <Button
                                                        variant="ghost"
                                                        onClick={() => handleSort("createdAt")}
                                                        className="h-auto p-0 font-semibold text-gray-700 hover:bg-transparent"
                                                    >
                                                        创建时间
                                                        {sortBy === "createdAt" &&
                                                            (sortOrder === "asc" ? (
                                                                <ArrowUp className="w-3 h-3 ml-1" />
                                                            ) : (
                                                                <ArrowDown className="w-3 h-3 ml-1" />
                                                            ))}
                                                    </Button>
                                                </TableHead>
                                                <TableHead className="text-center font-semibold text-gray-700 py-4 px-4">操作</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {sortedTasks.map((task) => {
                                                const statusConfig = getStatusBadge(task.status)
                                                const StatusIcon = statusConfig.icon
                                                const TypeIcon = getTypeIcon(task.type)

                                                return (
                                                    <TableRow
                                                        key={task.id}
                                                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                                                    >
                                                        <TableCell className="py-4 px-6">
                                                            <div className="flex items-center gap-3">
                                                                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shadow-sm">
                                                                    <TypeIcon className="w-4 h-4 text-white" />
                                                                </div>
                                                                <div>
                                                                    <div className="font-medium text-gray-900 text-sm">{task.name}</div>
                                                                    <div className="text-xs text-gray-500">{task.template}</div>
                                                                </div>
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                                                                {task.type.toUpperCase()}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            <Badge className={`${statusConfig.color} flex items-center gap-1 w-fit text-xs`}>
                                                                <StatusIcon className="w-3 h-3" />
                                                                {statusConfig.label}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            {task.status === "running" ? (
                                                                <div className="space-y-1">
                                                                    <Progress value={task.progress} className="h-2 w-20" />
                                                                    <div className="text-xs text-gray-500">{Math.round(task.progress)}%</div>
                                                                </div>
                                                            ) : (
                                                                <div className="text-sm text-gray-600">
                                                                    {task.status === "completed"
                                                                        ? "100%"
                                                                        : task.status === "failed"
                                                                            ? `${Math.round(task.progress)}%`
                                                                            : "-"}
                                                                </div>
                                                            )}
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            <div className="text-sm text-gray-900">{task.sourceDataset}</div>
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            <div className="text-sm font-medium text-gray-900">
                                                                {task.generatedCount.toLocaleString()} / {task.targetCount.toLocaleString()}
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            {task.quality ? (
                                                                <Badge className={`font-medium text-xs ${getQualityColor(task.quality)}`}>
                                                                    {task.quality}%
                                                                </Badge>
                                                            ) : (
                                                                <span className="text-sm text-gray-400">-</span>
                                                            )}
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            <div className="text-sm text-gray-600">{task.createdAt}</div>
                                                        </TableCell>
                                                        <TableCell className="py-4 px-4">
                                                            <div className="flex items-center justify-center gap-1">
                                                                {task.status === "running" && (
                                                                    <Button
                                                                        variant="outline"
                                                                        size="sm"
                                                                        onClick={() => handleTaskAction(task.id, "pause")}
                                                                        className="hover:bg-orange-50 p-1 h-7 w-7"
                                                                    >
                                                                        <Pause className="w-3 h-3" />
                                                                    </Button>
                                                                )}
                                                                {task.status === "paused" && (
                                                                    <Button
                                                                        variant="outline"
                                                                        size="sm"
                                                                        onClick={() => handleTaskAction(task.id, "resume")}
                                                                        className="hover:bg-green-50 p-1 h-7 w-7"
                                                                    >
                                                                        <Play className="w-3 h-3" />
                                                                    </Button>
                                                                )}
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="hover:bg-blue-50 p-2 h-7 w-7 bg-transparent"
                                                                    onClick={() => setShowAnnotatePage(true)}
                                                                >
                                                                    审核
                                                                </Button>
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="hover:bg-green-50 p-1 h-7 w-7 bg-transparent"
                                                                >
                                                                    <DownloadIcon className="w-3 h-3" />
                                                                </Button>

                                                            </div>
                                                        </TableCell>
                                                    </TableRow>
                                                )
                                            })}
                                        </TableBody>
                                    </Table>

                                    {sortedTasks.length === 0 && (
                                        <div className="text-center py-12">
                                            <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                            <h3 className="text-base font-semibold text-gray-900 mb-2">暂无合成任务</h3>
                                            <p className="text-gray-500 mb-4 text-sm">
                                                {searchQuery ? "没有找到匹配的任务" : "开始创建您的第一个合成任务"}
                                            </p>
                                            {!searchQuery && filterStatus === "all" && (
                                                <Button
                                                    onClick={() => setShowCreateTask(true)}
                                                    className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 shadow-lg"
                                                >
                                                    <Plus className="w-3 h-3 mr-1" />
                                                    创建合成任务
                                                </Button>
                                            )}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="templates" className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="relative">
                                        <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                        <Input
                                            placeholder="搜索模板名称或描述..."
                                            className="pl-9 w-80 h-9 text-sm border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 bg-white"
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                        />
                                    </div>
                                    <Select value={filterTemplateType} onValueChange={setFilterTemplateType}>
                                        <SelectTrigger className="w-40 h-9 text-sm bg-white">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">全部类型</SelectItem>
                                            <SelectItem value="preset">预置模板</SelectItem>
                                            <SelectItem value="custom">自定义模板</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button
                                    onClick={() => {
                                        setSelectedTemplate(null)
                                        resetTemplateForm()
                                        setShowTemplateEditor(true)
                                    }}
                                    className="px-4 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg hover:shadow-xl transition-all duration-200"
                                >
                                    <Plus className="w-3 h-3 mr-1" />
                                    创建模板
                                </Button>
                            </div>

                            {/* 模板表格 */}
                            <Card className="shadow-sm border-0 bg-white">
                                <CardContent className="p-0">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="border-b border-gray-200">
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-6">模板名称</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">类型</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">分类</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">变量数量</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">使用次数</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">质量评分</TableHead>
                                                <TableHead className="text-left font-semibold text-gray-700 py-4 px-4">最后使用</TableHead>
                                                <TableHead className="text-center font-semibold text-gray-700 py-4 px-4">操作</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {filteredTemplates.map((template) => (
                                                <TableRow
                                                    key={template.id}
                                                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                                                >
                                                    <TableCell className="py-4 px-6">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center shadow-sm">
                                                                <FileText className="w-4 h-4 text-white" />
                                                            </div>
                                                            <div>
                                                                <div className="font-medium text-gray-900 text-sm">{template.name}</div>
                                                                <div className="text-xs text-gray-500 line-clamp-1">{template.description}</div>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        <Badge variant={template.type === "preset" ? "default" : "secondary"} className="text-xs">
                                                            {template.type === "preset" ? "预置" : "自定义"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200 text-xs">
                                                            {template.category}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        <div className="text-sm font-medium text-gray-900">{template.variables.length}</div>
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        <div className="text-sm font-medium text-gray-900">{template.usageCount}</div>
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        {template.quality ? (
                                                            <Badge className={`font-medium text-xs ${getQualityColor(template.quality)}`}>
                                                                {template.quality}%
                                                            </Badge>
                                                        ) : (
                                                            <span className="text-sm text-gray-400">-</span>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        <div className="text-sm text-gray-600">{template.lastUsed || "-"}</div>
                                                    </TableCell>
                                                    <TableCell className="py-4 px-4">
                                                        <div className="flex items-center justify-center gap-1">
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                onClick={() => {
                                                                    setSelectedTemplate(template)
                                                                    setTemplateForm({
                                                                        name: template.name,
                                                                        category: template.category,
                                                                        prompt: template.prompt,
                                                                        variables: template.variables,
                                                                        description: template.description,
                                                                        testInput: "",
                                                                        testOutput: "",
                                                                    })
                                                                    setShowTemplateEditor(true)
                                                                }}
                                                                className="hover:bg-blue-50 p-1 h-7 w-7"
                                                            >
                                                                <Edit className="w-3 h-3" />
                                                            </Button>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                className="hover:bg-green-50 p-1 h-7 w-7 bg-transparent"
                                                            >
                                                                <Copy className="w-3 h-3" />
                                                            </Button>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                className="hover:bg-red-50 p-1 h-7 w-7 bg-transparent"
                                                            >
                                                                <Trash2 className="w-3 h-3" />
                                                            </Button>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                className="hover:bg-gray-50 p-1 h-7 w-7 bg-transparent"
                                                            >
                                                                <MoreHorizontal className="w-3 h-3" />
                                                            </Button>
                                                        </div>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>

                                    {filteredTemplates.length === 0 && (
                                        <div className="text-center py-12">
                                            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                            <h3 className="text-base font-semibold text-gray-900 mb-2">暂无指令模板</h3>
                                            <p className="text-gray-500 mb-4 text-sm">
                                                {searchQuery ? "没有找到匹配的模板" : "开始创建您的第一个指令模板"}
                                            </p>
                                            {!searchQuery && (
                                                <Button
                                                    onClick={() => {
                                                        setSelectedTemplate(null)
                                                        resetTemplateForm()
                                                        setShowTemplateEditor(true)
                                                    }}
                                                    className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                                                >
                                                    <Plus className="w-3 h-3 mr-1" />
                                                    创建模板
                                                </Button>
                                            )}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </TooltipProvider>
    )
}
