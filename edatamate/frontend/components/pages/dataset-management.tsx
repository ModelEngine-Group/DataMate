"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Plus,
  Search,
  Download,
  Upload,
  Eye,
  Edit,
  FileImage,
  Database,
  Calendar,
  Users,
  BarChart3,
  Activity,
  Microscope,
  Stethoscope,
  Brain,
  Heart,
  GitBranch,
  CheckCircle,
  AlertTriangle,
  Clock,
  Target,
  X,
  Trash2,
} from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Label } from "@/components/ui/label"

interface Dataset {
  id: number
  name: string
  description: string
  type: "image" | "text" | "audio" | "video" | "multimodal"
  category: string
  size: string
  itemCount: number
  createdAt: string
  lastModified: string
  status: "active" | "processing" | "archived"
  tags: string[]
  quality: number
  annotations?: {
    total: number
    completed: number
    accuracy: number
  }
  lineage?: {
    source: string
    processing: string[]
    training?: {
      model: string
      accuracy: number
      f1Score: number
    }
  }
}

const mockDatasets: Dataset[] = [
  {
    id: 1,
    name: "肺癌WSI病理图像数据集",
    description: "来自三甲医院的肺癌全切片病理图像，包含详细的病理标签和分级信息",
    type: "image",
    category: "医学影像",
    size: "1.2TB",
    itemCount: 1247,
    createdAt: "2024-01-15",
    lastModified: "2024-01-23",
    status: "active",
    tags: ["WSI", "病理", "肺癌", "分类", "分级"],
    quality: 94.2,
    annotations: {
      total: 1247,
      completed: 1205,
      accuracy: 96.8,
    },
    lineage: {
      source: "三甲医院病理科",
      processing: ["质量检查", "格式标准化", "数据增强", "标签验证"],
      training: {
        model: "ResNet-50",
        accuracy: 92.4,
        f1Score: 91.8,
      },
    },
  },
  {
    id: 2,
    name: "乳腺癌组织病理数据集",
    description: "乳腺癌组织切片图像，包含良性和恶性分类标签",
    type: "image",
    category: "医学影像",
    size: "856GB",
    itemCount: 892,
    createdAt: "2024-01-10",
    lastModified: "2024-01-20",
    status: "processing",
    tags: ["组织病理", "乳腺癌", "二分类"],
    quality: 91.5,
    annotations: {
      total: 892,
      completed: 756,
      accuracy: 94.2,
    },
    lineage: {
      source: "多中心医院联合",
      processing: ["图像预处理", "质量筛选", "标准化"],
    },
  },
  {
    id: 3,
    name: "皮肤镜图像数据集",
    description: "皮肤病变筛查图像，用于皮肤癌早期检测",
    type: "image",
    category: "医学影像",
    size: "234GB",
    itemCount: 2156,
    createdAt: "2024-01-08",
    lastModified: "2024-01-18",
    status: "active",
    tags: ["皮肤镜", "皮肤癌", "筛查"],
    quality: 88.7,
    annotations: {
      total: 2156,
      completed: 2156,
      accuracy: 92.1,
    },
    lineage: {
      source: "皮肤科专科医院",
      processing: ["图像增强", "噪声去除", "标准化"],
      training: {
        model: "EfficientNet-B4",
        accuracy: 89.3,
        f1Score: 87.6,
      },
    },
  },
  {
    id: 4,
    name: "CT影像数据集",
    description: "胸部CT影像，用于肺部疾病诊断和分析",
    type: "image",
    category: "放射影像",
    size: "1.8TB",
    itemCount: 3421,
    createdAt: "2024-01-05",
    lastModified: "2024-01-22",
    status: "active",
    tags: ["CT", "胸部", "肺部疾病"],
    quality: 96.1,
    annotations: {
      total: 3421,
      completed: 3421,
      accuracy: 98.2,
    },
    lineage: {
      source: "放射科影像中心",
      processing: ["DICOM转换", "窗宽窗位调整", "分割标注"],
      training: {
        model: "3D U-Net",
        accuracy: 94.7,
        f1Score: 93.2,
      },
    },
  },
  {
    id: 5,
    name: "内镜图像数据集",
    description: "消化道内镜检查图像，用于消化道疾病诊断",
    type: "image",
    category: "内镜影像",
    size: "445GB",
    itemCount: 1876,
    createdAt: "2024-01-12",
    lastModified: "2024-01-21",
    status: "processing",
    tags: ["内镜", "消化道", "病变检测"],
    quality: 87.3,
    annotations: {
      total: 1876,
      completed: 1234,
      accuracy: 91.5,
    },
    lineage: {
      source: "消化内科",
      processing: ["图像分割", "病变标注", "质量评估"],
    },
  },
]

export default function DatasetManagementPage() {
  const [datasets, setDatasets] = useState<Dataset[]>(mockDatasets)
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState("all")
  const [filterStatus, setFilterStatus] = useState("all")

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showTaskPanel, setShowTaskPanel] = useState(false)
  const [creationTasks, setCreationTasks] = useState<any[]>([])
  const [createForm, setCreateForm] = useState({
    name: "",
    description: "",
    source: "local-upload", // local-upload, database, nas, obs
    target: "local-folder", // local-folder, database
    sourceConfig: {},
    targetConfig: {},
    syncStrategy: "immediate", // immediate, scheduled
    cronExpression: "",
    uploadedFiles: [] as File[],
    scheduleConfig: {
      type: "cron", // cron, simple
      frequency: "daily", // daily, weekly, monthly
      time: "02:00",
      dayOfWeek: "1", // 1-7 (Monday-Sunday)
      dayOfMonth: "1", // 1-31
      endDate: "", // 任务结束日期
      maxExecutions: 0, // 最大执行次数，0表示无限制
    },
  })

  const [showCronPanel, setShowCronPanel] = useState(false)

  const filteredDatasets = datasets.filter((dataset) => {
    const matchesSearch =
      dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dataset.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dataset.tags.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesType = filterType === "all" || dataset.type === filterType
    const matchesStatus = filterStatus === "all" || dataset.status === filterStatus
    return matchesSearch && matchesType && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { label: "活跃", color: "bg-green-100 text-green-800", icon: CheckCircle },
      processing: { label: "处理中", color: "bg-blue-100 text-blue-800", icon: Clock },
      archived: { label: "已归档", color: "bg-gray-100 text-gray-800", icon: Database },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.active
  }

  const getTypeIcon = (type: string) => {
    const iconMap = {
      image: FileImage,
      text: Database,
      audio: Activity,
      video: Eye,
      multimodal: BarChart3,
    }
    const IconComponent = iconMap[type as keyof typeof iconMap] || FileImage
    return <IconComponent className="w-4 h-4" />
  }

  const getCategoryIcon = (category: string) => {
    const iconMap = {
      医学影像: Microscope,
      放射影像: Brain,
      内镜影像: Stethoscope,
      心电图: Heart,
    }
    const IconComponent = iconMap[category as keyof typeof iconMap] || Microscope
    return <IconComponent className="w-4 h-4" />
  }

  const renderLineageFlow = (lineage: Dataset["lineage"]) => {
    if (!lineage) return null

    const steps = [
      { name: "数据源", value: lineage.source, icon: Database },
      ...lineage.processing.map((step, index) => ({
        name: `处理${index + 1}`,
        value: step,
        icon: GitBranch,
      })),
    ]

    if (lineage.training) {
      steps.push({
        name: "模型训练",
        value: `${lineage.training.model} (准确率: ${lineage.training.accuracy}%)`,
        icon: Target,
      })
    }

    return (
      <div className="space-y-4">
        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
          <GitBranch className="w-4 h-4" />
          数据血缘追踪
        </h4>
        <div className="relative">
          {steps.map((step, index) => (
            <div key={index} className="flex items-start gap-4 pb-6 last:pb-0">
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <step.icon className="w-5 h-5 text-blue-600" />
                </div>
                {index < steps.length - 1 && <div className="w-0.5 h-8 bg-blue-200 mt-2"></div>}
              </div>
              <div className="flex-1 pt-2">
                <h5 className="font-medium text-gray-900">{step.name}</h5>
                <p className="text-sm text-gray-600 mt-1">{step.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const handleCreateDataset = async () => {
    const newDataset: Dataset = {
      id: Date.now(),
      name: createForm.name,
      description: createForm.description,
      type: "image",
      category: "自定义",
      size: "0 MB",
      itemCount: 0,
      createdAt: new Date().toISOString().split("T")[0],
      lastModified: new Date().toISOString().split("T")[0],
      status: "processing",
      tags: [],
      quality: 0,
    }

    const newTask = {
      id: Date.now(),
      datasetId: newDataset.id,
      name: `导入 ${createForm.name}`,
      source: createForm.source,
      target: createForm.target,
      status: createForm.syncStrategy === "immediate" ? "importing" : "waiting",
      progress: 0,
      syncStrategy: createForm.syncStrategy,
      cronExpression: createForm.cronExpression,
      scheduleConfig: createForm.scheduleConfig,
      createdAt: new Date().toISOString(),
      nextExecutionTime: createForm.syncStrategy === "scheduled" ? getNextExecutionTime(createForm) : null,
      executionCount: 0,
      maxExecutions: createForm.scheduleConfig.maxExecutions,
      endDate: createForm.scheduleConfig.endDate,
    }

    setDatasets([newDataset, ...datasets])
    setCreationTasks([newTask, ...creationTasks])

    // Reset form and close modal
    setCreateForm({
      name: "",
      description: "",
      source: "local-upload",
      target: "local-folder",
      sourceConfig: {},
      targetConfig: {},
      syncStrategy: "immediate",
      cronExpression: "",
      uploadedFiles: [],
      scheduleConfig: {
        type: "cron", // cron, simple
        frequency: "daily", // daily, weekly, monthly
        time: "02:00",
        dayOfWeek: "1", // 1-7 (Monday-Sunday)
        dayOfMonth: "1", // 1-31
        endDate: "", // 任务结束日期
        maxExecutions: 0, // 最大执行次数，0表示无限制
      },
    })
    setShowCreateForm(false)

    // Simulate async import process
    setTimeout(() => {
      const interval = setInterval(() => {
        setCreationTasks((prev) =>
          prev.map((task) => {
            if (task.id === newTask.id) {
              const newProgress = Math.min(task.progress + Math.random() * 15, 100)
              if (newProgress >= 100) {
                // 检查是否需要继续定时执行
                const shouldComplete = checkTaskCompletion(task)
                return {
                  ...task,
                  progress: 100,
                  status: shouldComplete ? "completed" : "waiting",
                  nextExecutionTime: shouldComplete ? null : getNextExecutionTime(createForm),
                }
              }
              return {
                ...task,
                progress: newProgress,
                status: newProgress >= 100 ? "completed" : "importing",
              }
            }
            return task
          }),
        )

        setDatasets((prev) =>
          prev.map((ds) => {
            if (ds.id === newDataset.id) {
              const task = creationTasks.find((t) => t.datasetId === ds.id)
              if (task?.status === "completed") {
                return {
                  ...ds,
                  status: "active",
                  itemCount: Math.floor(Math.random() * 1000 + 100),
                  size: `${(Math.random() * 500 + 50).toFixed(0)}MB`,
                  quality: Math.floor(Math.random() * 20 + 80),
                }
              }
            }
            return ds
          }),
        )
      }, 500)

      setTimeout(() => clearInterval(interval), 8000)
    }, 1000)
  }

  const getSourceTargetOptions = () => {
    const sourceOptions = [
      { value: "local-upload", label: "本地上传" },
      { value: "database", label: "数据库导入" },
      { value: "nas", label: "NAS 导入" },
      { value: "obs", label: "OBS 导入" },
    ]

    let targetOptions = []
    if (["local-upload", "nas", "obs"].includes(createForm.source)) {
      targetOptions = [{ value: "local-folder", label: "本地文件夹" }]
    } else if (createForm.source === "database") {
      targetOptions = [{ value: "database", label: "数据库" }]
    }

    return { sourceOptions, targetOptions }
  }

  const deleteTask = (taskId: number) => {
    setCreationTasks((prev) => prev.filter((task) => task.id !== taskId))
  }

  const deleteDataset = (datasetId: number) => {
    setDatasets((prev) => prev.filter((ds) => ds.id !== datasetId))
    setCreationTasks((prev) => prev.filter((task) => task.datasetId !== datasetId))
  }

  const getNextExecutionTime = (form: any) => {
    if (form.scheduleConfig.type === "cron") {
      // 基于 cron 表达式计算下次执行时间
      return calculateNextCronExecution(form.cronExpression)
    } else {
      // 基于简单配置计算下次执行时间
      return calculateNextSimpleExecution(form.scheduleConfig)
    }
  }

  const calculateNextCronExecution = (cronExpression: string) => {
    // 简化的 cron 计算逻辑
    const now = new Date()
    const tomorrow = new Date(now)
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(2, 0, 0, 0) // 默认凌晨2点
    return tomorrow.toISOString()
  }

  const calculateNextSimpleExecution = (config: any) => {
    const now = new Date()
    const next = new Date(now)

    switch (config.frequency) {
      case "daily":
        next.setDate(next.getDate() + 1)
        break
      case "weekly":
        next.setDate(next.getDate() + 7)
        break
      case "monthly":
        next.setMonth(next.getMonth() + 1)
        break
    }

    const [hours, minutes] = config.time.split(":")
    next.setHours(Number.parseInt(hours), Number.parseInt(minutes), 0, 0)
    return next.toISOString()
  }

  const generateCronFromSimpleConfig = (config: any) => {
    const [hours, minutes] = config.time.split(":")

    switch (config.frequency) {
      case "daily":
        return `0 ${minutes} ${hours} * * ?`
      case "weekly":
        return `0 ${minutes} ${hours} ? * ${config.dayOfWeek}`
      case "monthly":
        return `0 ${minutes} ${hours} ${config.dayOfMonth} * ?`
      default:
        return `0 ${minutes} ${hours} * * ?`
    }
  }

  const executeTaskImmediately = (taskId: number) => {
    setCreationTasks((prev) =>
      prev.map((task) => {
        if (task.id === taskId) {
          return {
            ...task,
            status: "importing",
            progress: 0,
            executionCount: task.executionCount + 1,
            lastExecutionTime: new Date().toISOString(),
          }
        }
        return task
      }),
    )

    // 模拟执行过程
    setTimeout(() => {
      const interval = setInterval(() => {
        setCreationTasks((prev) =>
          prev.map((task) => {
            if (task.id === taskId && task.status === "importing") {
              const newProgress = Math.min(task.progress + Math.random() * 15, 100)
              if (newProgress >= 100) {
                // 检查是否需要继续定时执行
                const shouldComplete = checkTaskCompletion(task)
                return {
                  ...task,
                  progress: 100,
                  status: shouldComplete ? "completed" : "waiting",
                  nextExecutionTime: shouldComplete ? null : getNextExecutionTime(createForm),
                }
              }
              return { ...task, progress: newProgress }
            }
            return task
          }),
        )
      }, 500)

      setTimeout(() => clearInterval(interval), 8000)
    }, 1000)
  }

  const checkTaskCompletion = (task: any) => {
    // 检查是否达到最大执行次数
    if (task.maxExecutions > 0 && task.executionCount >= task.maxExecutions) {
      return true
    }

    // 检查是否超过结束日期
    if (task.endDate && new Date() > new Date(task.endDate)) {
      return true
    }

    return false
  }

  const getSourceLabel = (source: string) => {
    switch (source) {
      case "local-upload":
        return "本地上传"
      case "database":
        return "数据库"
      case "nas":
        return "NAS"
      case "obs":
        return "OBS"
      default:
        return "未知"
    }
  }

  const getTargetLabel = (target: string) => {
    switch (target) {
      case "local-folder":
        return "本地文件夹"
      case "database":
        return "数据库"
      default:
        return "未知"
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">数据集管理</h1>
          <p className="text-gray-600 mt-2">管理和组织您的机器学习数据集</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            导入数据集
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建数据集
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowTaskPanel(!showTaskPanel)}
            className={showTaskPanel ? "bg-blue-50 border-blue-300" : ""}
          >
            <Activity className="w-4 h-4 mr-2" />
            任务 {creationTasks.length > 0 && `(${creationTasks.length})`}
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="搜索数据集名称、描述或标签..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有类型</SelectItem>
                  <SelectItem value="image">图像</SelectItem>
                  <SelectItem value="text">文本</SelectItem>
                  <SelectItem value="audio">音频</SelectItem>
                  <SelectItem value="video">视频</SelectItem>
                  <SelectItem value="multimodal">多模态</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  <SelectItem value="active">活跃</SelectItem>
                  <SelectItem value="processing">处理中</SelectItem>
                  <SelectItem value="archived">已归档</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Creation Form - 移动到搜索框下方 */}
      {showCreateForm && (
        <Card className="border-2 border-blue-200">
          <CardHeader>
            <CardTitle>创建数据集</CardTitle>
            <CardDescription>配置数据集基本信息和导入设置</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>数据集名称</Label>
                <Input
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="输入数据集名称"
                />
              </div>
              <div className="space-y-2">
                <Label>描述</Label>
                <Input
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="输入数据集描述"
                />
              </div>
            </div>

            {/* Source → Target Pipeline */}
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-medium text-gray-900">数据导入链路</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>数据源</Label>
                  <Select
                    value={createForm.source}
                    onValueChange={(value) => {
                      const { targetOptions } = getSourceTargetOptions()
                      const newTargetOptions =
                        value === "database"
                          ? [{ value: "database", label: "数据库" }]
                          : [{ value: "local-folder", label: "本地文件夹" }]
                      setCreateForm({
                        ...createForm,
                        source: value,
                        target: newTargetOptions[0]?.value || "local-folder",
                        sourceConfig: {},
                        targetConfig: {},
                      })
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getSourceTargetOptions().sourceOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>数据目标</Label>
                  <Select
                    value={createForm.target}
                    onValueChange={(value) => setCreateForm({ ...createForm, target: value, targetConfig: {} })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getSourceTargetOptions().targetOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Source Configuration */}
            {createForm.source !== "local-upload" && (
              <div className="space-y-4 bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-900">数据源配置</h5>
                {createForm.source === "database" && (
                  <div className="space-y-4">
                    <Input placeholder="JDBC URL (如: jdbc:mysql://localhost:3306/dbname)" />
                    <div className="grid grid-cols-2 gap-4">
                      <Input placeholder="用户名" />
                      <Input type="password" placeholder="密码" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <Input placeholder="表名" />
                      <Input placeholder="列名称列表 (逗号分隔)" />
                    </div>
                  </div>
                )}
                {createForm.source === "nas" && (
                  <div className="grid grid-cols-2 gap-4">
                    <Input placeholder="NAS地址" />
                    <Input placeholder="共享路径" />
                  </div>
                )}
                {createForm.source === "obs" && (
                  <div className="grid grid-cols-2 gap-4">
                    <Input placeholder="Endpoint" />
                    <Input placeholder="Bucket名称" />
                    <Input placeholder="Access Key (AK)" />
                    <Input placeholder="Secret Key (SK)" />
                  </div>
                )}
              </div>
            )}

            {/* File Upload (only for local-upload source) */}
            {createForm.source === "local-upload" && (
              <div className="space-y-4">
                <h5 className="font-medium text-gray-900">文件上传</h5>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600 mb-2">拖拽文件到此处或点击上传</p>
                  <p className="text-sm text-gray-500">支持 JPG, PNG, DICOM, CSV 等格式</p>
                  <Input
                    type="file"
                    multiple
                    className="hidden"
                    id="file-upload"
                    onChange={(e) => {
                      const files = Array.from(e.target.files || [])
                      setCreateForm({ ...createForm, uploadedFiles: files })
                    }}
                  />
                  <Button
                    variant="outline"
                    className="mt-4 bg-transparent"
                    onClick={() => document.getElementById("file-upload")?.click()}
                  >
                    选择文件
                  </Button>
                </div>
                {createForm.uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">已选择 {createForm.uploadedFiles.length} 个文件</p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {createForm.uploadedFiles.map((file, index) => (
                        <div key={index} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                          {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Target Configuration */}
            {createForm.target === "local-folder" && (
              <div className="space-y-4 bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-900">数据目标配置</h5>
              </div>
            )}

            {createForm.target === "database" && (
              <div className="space-y-4 bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-900">数据目标配置</h5>
                <Input placeholder="JDBC URL (如: jdbc:mysql://localhost:3306/dbname)" />
                <div className="grid grid-cols-2 gap-4">
                  <Input placeholder="用户名" />
                  <Input type="password" placeholder="密码" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Input placeholder="表名" />
                  <Input placeholder="列名称列表 (逗号分隔)" />
                </div>
                <div className="space-y-2">
                  <Label>Pre SQL (导入前执行)</Label>
                  <Input placeholder="CREATE TABLE IF NOT EXISTS..." />
                </div>
                <div className="space-y-2">
                  <Label>Post SQL (导入后执行)</Label>
                  <Input placeholder="UPDATE table SET..." />
                </div>
              </div>
            )}

            {/* Sync Strategy */}
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-medium text-gray-900">同步策略</h4>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="syncStrategy"
                      value="immediate"
                      checked={createForm.syncStrategy === "immediate"}
                      onChange={(e) => setCreateForm({ ...createForm, syncStrategy: e.target.value })}
                    />
                    <span>立即同步</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="syncStrategy"
                      value="scheduled"
                      checked={createForm.syncStrategy === "scheduled"}
                      onChange={(e) => setCreateForm({ ...createForm, syncStrategy: e.target.value })}
                    />
                    <span>定时同步</span>
                  </label>
                </div>

                {createForm.syncStrategy === "scheduled" && (
                  <div className="space-y-2">
                    <Label>Cron 表达式</Label>
                    <div className="flex gap-2">
                      <Input
                        value={createForm.cronExpression}
                        onChange={(e) => setCreateForm({ ...createForm, cronExpression: e.target.value })}
                        placeholder="0 0 2 * * ? (每天凌晨2点)"
                      />
                      <Button variant="outline" size="sm" onClick={() => setShowCronPanel(true)}>
                        可视化配置
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500">示例: 0 0 2 * * ? (每天凌晨2点), 0 0 * * * ? (每小时)</p>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4 border-t">
              <Button onClick={handleCreateDataset} disabled={!createForm.name || !createForm.description}>
                创建数据集
              </Button>
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                取消
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Dataset Grid */}
      <div className="grid gap-6">
        {filteredDatasets.map((dataset) => (
          <Card key={dataset.id} className="hover:shadow-lg transition-shadow">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      {getCategoryIcon(dataset.category)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{dataset.name}</h3>
                        <Badge className={getStatusBadge(dataset.status).color}>
                          {getStatusBadge(dataset.status).label}
                        </Badge>
                      </div>
                      <p className="text-gray-600 text-sm mb-3">{dataset.description}</p>
                      <div className="flex flex-wrap gap-2">
                        {dataset.tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => setSelectedDataset(dataset)}>
                      <Eye className="w-4 h-4 mr-1" />
                      查看
                    </Button>
                    <Button variant="outline" size="sm">
                      <Edit className="w-4 h-4 mr-1" />
                      编辑
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-1" />
                      下载
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => deleteDataset(dataset.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Dataset Stats */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 pt-4 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{dataset.itemCount.toLocaleString()}</div>
                    <div className="text-xs text-gray-500">数据项</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{dataset.size}</div>
                    <div className="text-xs text-gray-500">数据大小</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{dataset.quality}%</div>
                    <div className="text-xs text-gray-500">质量分数</div>
                  </div>
                  {dataset.annotations && (
                    <>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">
                          {Math.round((dataset.annotations.completed / dataset.annotations.total) * 100)}%
                        </div>
                        <div className="text-xs text-gray-500">标注进度</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-pink-600">{dataset.annotations.accuracy}%</div>
                        <div className="text-xs text-gray-500">标注准确率</div>
                      </div>
                    </>
                  )}
                </div>

                {/* Progress Bars */}
                {dataset.annotations && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>标注进度</span>
                      <span>
                        {dataset.annotations.completed} / {dataset.annotations.total}
                      </span>
                    </div>
                    <Progress
                      value={(dataset.annotations.completed / dataset.annotations.total) * 100}
                      className="h-2"
                    />
                  </div>
                )}

                {/* Training Results */}
                {dataset.lineage?.training && (
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-4 h-4 text-green-600" />
                      <span className="font-medium text-green-800">模型训练结果</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">模型:</span>
                        <div className="font-medium">{dataset.lineage.training.model}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">准确率:</span>
                        <div className="font-medium text-green-600">{dataset.lineage.training.accuracy}%</div>
                      </div>
                      <div>
                        <span className="text-gray-600">F1分数:</span>
                        <div className="font-medium text-green-600">{dataset.lineage.training.f1Score}%</div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-between text-xs text-gray-500 pt-2 border-t">
                  <span>创建: {dataset.createdAt}</span>
                  <span>更新: {dataset.lastModified}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Dataset Detail Modal */}
      {selectedDataset && (
        <Card className="border-2 border-blue-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  {getCategoryIcon(selectedDataset.category)}
                </div>
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {selectedDataset.name}
                    <Badge className={getStatusBadge(selectedDataset.status).color}>
                      {getStatusBadge(selectedDataset.status).label}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{selectedDataset.description}</CardDescription>
                </div>
              </div>
              <Button variant="outline" onClick={() => setSelectedDataset(null)}>
                关闭
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="overview">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">概览</TabsTrigger>
                <TabsTrigger value="annotations">标注详情</TabsTrigger>
                <TabsTrigger value="lineage">数据血缘</TabsTrigger>
                <TabsTrigger value="quality">质量分析</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <FileImage className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                    <div className="text-2xl font-bold text-blue-600">{selectedDataset.itemCount.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">数据项总数</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Database className="w-8 h-8 mx-auto mb-2 text-green-500" />
                    <div className="text-2xl font-bold text-green-600">{selectedDataset.size}</div>
                    <div className="text-sm text-gray-600">数据大小</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <BarChart3 className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                    <div className="text-2xl font-bold text-purple-600">{selectedDataset.quality}%</div>
                    <div className="text-sm text-gray-600">质量分数</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <Calendar className="w-8 h-8 mx-auto mb-2 text-orange-500" />
                    <div className="text-2xl font-bold text-orange-600">{selectedDataset.createdAt}</div>
                    <div className="text-sm text-gray-600">创建日期</div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-semibold">数据集标签</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedDataset.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="annotations" className="space-y-6">
                {selectedDataset.annotations && (
                  <>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <Users className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                        <div className="text-2xl font-bold text-blue-600">{selectedDataset.annotations.total}</div>
                        <div className="text-sm text-gray-600">总标注数</div>
                      </div>
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                        <div className="text-2xl font-bold text-green-600">{selectedDataset.annotations.completed}</div>
                        <div className="text-sm text-gray-600">已完成</div>
                      </div>
                      <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <Target className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                        <div className="text-2xl font-bold text-purple-600">
                          {selectedDataset.annotations.accuracy}%
                        </div>
                        <div className="text-sm text-gray-600">准确率</div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h4 className="font-semibold">专业病理标签分布</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="flex justify-between text-sm">
                            <span>有癌 (阳性)</span>
                            <span>687例 (55.1%)</span>
                          </div>
                          <Progress value={55.1} className="h-2" />
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between text-sm">
                            <span>无癌 (阴性)</span>
                            <span>560例 (44.9%)</span>
                          </div>
                          <Progress value={44.9} className="h-2" />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-3">
                          <h5 className="font-medium">病理分类</h5>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>腺癌</span>
                              <span>312例 (45.4%)</span>
                            </div>
                            <Progress value={45.4} className="h-1" />
                            <div className="flex justify-between text-sm">
                              <span>鳞状细胞癌</span>
                              <span>234例 (34.1%)</span>
                            </div>
                            <Progress value={34.1} className="h-1" />
                            <div className="flex justify-between text-sm">
                              <span>小细胞肺癌</span>
                              <span>141例 (20.5%)</span>
                            </div>
                            <Progress value={20.5} className="h-1" />
                          </div>
                        </div>
                        <div className="space-y-3">
                          <h5 className="font-medium">分化程度</h5>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>高分化 (G1)</span>
                              <span>156例 (22.7%)</span>
                            </div>
                            <Progress value={22.7} className="h-1" />
                            <div className="flex justify-between text-sm">
                              <span>中分化 (G2)</span>
                              <span>298例 (43.4%)</span>
                            </div>
                            <Progress value={43.4} className="h-1" />
                            <div className="flex justify-between text-sm">
                              <span>低分化 (G3)</span>
                              <span>233例 (33.9%)</span>
                            </div>
                            <Progress value={33.9} className="h-1" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </TabsContent>

              <TabsContent value="lineage" className="space-y-6">
                {renderLineageFlow(selectedDataset.lineage)}
              </TabsContent>

              <TabsContent value="quality" className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-semibold">图像质量指标</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span>图像清晰度</span>
                        <span className="font-medium">96.2%</span>
                      </div>
                      <Progress value={96.2} className="h-2" />
                      <div className="flex justify-between text-sm">
                        <span>色彩一致性</span>
                        <span className="font-medium">94.8%</span>
                      </div>
                      <Progress value={94.8} className="h-2" />
                      <div className="flex justify-between text-sm">
                        <span>标注完整性</span>
                        <span className="font-medium">98.1%</span>
                      </div>
                      <Progress value={98.1} className="h-2" />
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-semibold">数据完整性</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span>文件完整性</span>
                        <span className="font-medium">99.7%</span>
                      </div>
                      <Progress value={99.7} className="h-2" />
                      <div className="flex justify-between text-sm">
                        <span>元数据完整性</span>
                        <span className="font-medium">97.3%</span>
                      </div>
                      <Progress value={97.3} className="h-2" />
                      <div className="flex justify-between text-sm">
                        <span>标签一致性</span>
                        <span className="font-medium">95.6%</span>
                      </div>
                      <Progress value={95.6} className="h-2" />
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                      <h5 className="font-medium text-yellow-800">质量建议</h5>
                      <ul className="text-sm text-yellow-700 mt-2 space-y-1">
                        <li>• 建议对42张图像进行重新标注以提高准确性</li>
                        <li>• 检查并补充缺失的病理分级信息</li>
                        <li>• 考虑增加更多低分化样本以平衡数据分布</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{datasets.length}</p>
                <p className="text-sm text-gray-500">数据集总数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <FileImage className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">
                  {datasets.reduce((sum, ds) => sum + ds.itemCount, 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">数据项总数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{datasets.filter((ds) => ds.status === "active").length}</p>
                <p className="text-sm text-gray-500">活跃数据集</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">
                  {Math.round(datasets.reduce((sum, ds) => sum + ds.quality, 0) / datasets.length)}%
                </p>
                <p className="text-sm text-gray-500">平均质量分</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cron Configuration Panel */}
      {showCronPanel && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50" onClick={() => setShowCronPanel(false)}>
          <div
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 w-[500px] max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">定时任务配置</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowCronPanel(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <Tabs defaultValue="simple">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="simple">简单配置</TabsTrigger>
                <TabsTrigger value="advanced">高级配置</TabsTrigger>
              </TabsList>

              <TabsContent value="simple" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>执行频率</Label>
                    <Select
                      value={createForm.scheduleConfig.frequency}
                      onValueChange={(value) =>
                        setCreateForm({
                          ...createForm,
                          scheduleConfig: { ...createForm.scheduleConfig, frequency: value },
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">每天</SelectItem>
                        <SelectItem value="weekly">每周</SelectItem>
                        <SelectItem value="monthly">每月</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>执行时间</Label>
                    <Input
                      type="time"
                      value={createForm.scheduleConfig.time}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          scheduleConfig: { ...createForm.scheduleConfig, time: e.target.value },
                        })
                      }
                    />
                  </div>
                </div>

                {createForm.scheduleConfig.frequency === "weekly" && (
                  <div>
                    <Label>星期几</Label>
                    <Select
                      value={createForm.scheduleConfig.dayOfWeek}
                      onValueChange={(value) =>
                        setCreateForm({
                          ...createForm,
                          scheduleConfig: { ...createForm.scheduleConfig, dayOfWeek: value },
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">周一</SelectItem>
                        <SelectItem value="2">周二</SelectItem>
                        <SelectItem value="3">周三</SelectItem>
                        <SelectItem value="4">周四</SelectItem>
                        <SelectItem value="5">周五</SelectItem>
                        <SelectItem value="6">周六</SelectItem>
                        <SelectItem value="0">周日</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {createForm.scheduleConfig.frequency === "monthly" && (
                  <div>
                    <Label>每月第几天</Label>
                    <Input
                      type="number"
                      min="1"
                      max="31"
                      value={createForm.scheduleConfig.dayOfMonth}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          scheduleConfig: { ...createForm.scheduleConfig, dayOfMonth: e.target.value },
                        })
                      }
                    />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>结束日期 (可选)</Label>
                    <Input
                      type="date"
                      value={createForm.scheduleConfig.endDate}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          scheduleConfig: { ...createForm.scheduleConfig, endDate: e.target.value },
                        })
                      }
                    />
                  </div>
                  <div>
                    <Label>最大执行次数 (0=无限制)</Label>
                    <Input
                      type="number"
                      min="0"
                      value={createForm.scheduleConfig.maxExecutions}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          scheduleConfig: {
                            ...createForm.scheduleConfig,
                            maxExecutions: Number.parseInt(e.target.value),
                          },
                        })
                      }
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <div>
                  <Label>Cron 表达式</Label>
                  <Input
                    value={createForm.cronExpression}
                    onChange={(e) => setCreateForm({ ...createForm, cronExpression: e.target.value })}
                    placeholder="0 0 2 * * ? (每天凌晨2点)"
                  />
                  <p className="text-xs text-gray-500 mt-1">格式: 秒 分 时 日 月 周 年(可选)</p>
                </div>

                <div className="bg-gray-50 p-3 rounded">
                  <Label className="text-sm">常用表达式:</Label>
                  <div className="mt-2 space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span>每天凌晨2点:</span>
                      <Button
                        variant="link"
                        size="sm"
                        className="h-auto p-0 text-xs"
                        onClick={() => setCreateForm({ ...createForm, cronExpression: "0 0 2 * * ?" })}
                      >
                        0 0 2 * * ?
                      </Button>
                    </div>
                    <div className="flex justify-between">
                      <span>每小时:</span>
                      <Button
                        variant="link"
                        size="sm"
                        className="h-auto p-0 text-xs"
                        onClick={() => setCreateForm({ ...createForm, cronExpression: "0 0 * * * ?" })}
                      >
                        0 0 * * * ?
                      </Button>
                    </div>
                    <div className="flex justify-between">
                      <span>每周一上午9点:</span>
                      <Button
                        variant="link"
                        size="sm"
                        className="h-auto p-0 text-xs"
                        onClick={() => setCreateForm({ ...createForm, cronExpression: "0 0 9 ? * MON" })}
                      >
                        0 0 9 ? * MON
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex gap-2 mt-6">
              <Button
                onClick={() => {
                  // 根据简单配置生成 cron 表达式
                  if (createForm.scheduleConfig.type === "simple") {
                    const cronExpr = generateCronFromSimpleConfig(createForm.scheduleConfig)
                    setCreateForm({ ...createForm, cronExpression: cronExpr })
                  }
                  setShowCronPanel(false)
                }}
              >
                确认
              </Button>
              <Button variant="outline" onClick={() => setShowCronPanel(false)}>
                取消
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Task Panel */}
      {showTaskPanel && (
        <div className="fixed inset-0 z-50" onClick={() => setShowTaskPanel(false)}>
          <div
            className="absolute right-0 top-0 h-full w-96 bg-white shadow-xl border-l"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">导入任务</h3>
                <Button variant="ghost" size="sm" onClick={() => setShowTaskPanel(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <ScrollArea className="h-full pb-16">
              <div className="p-4 space-y-4">
                {creationTasks.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>暂无导入任务</p>
                  </div>
                ) : (
                  creationTasks.map((task) => (
                    <Card key={task.id} className="border">
                      <CardContent className="pt-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-sm">{task.name}</h4>
                            <div className="flex items-center gap-1">
                              <Badge
                                className={
                                  task.status === "importing"
                                    ? "bg-blue-100 text-blue-800"
                                    : task.status === "completed"
                                      ? "bg-green-100 text-green-800"
                                      : task.status === "waiting"
                                        ? "bg-yellow-100 text-yellow-800"
                                        : "bg-gray-100 text-gray-800"
                                }
                              >
                                {task.status === "importing"
                                  ? "导入中"
                                  : task.status === "completed"
                                    ? "已完成"
                                    : task.status === "waiting"
                                      ? "等待中"
                                      : "未知"}
                              </Badge>
                              <Button variant="ghost" size="sm" onClick={() => deleteTask(task.id)}>
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>

                          <div className="text-xs text-gray-500">
                            <div>源: {getSourceLabel(task.source)}</div>
                            <div>目标: {getTargetLabel(task.target)}</div>
                            <div>策略: {task.syncStrategy === "immediate" ? "立即同步" : "定时同步"}</div>
                            {task.cronExpression && <div>Cron: {task.cronExpression}</div>}
                            {task.nextExecutionTime && (
                              <div>下次执行: {new Date(task.nextExecutionTime).toLocaleString()}</div>
                            )}
                            {task.executionCount > 0 && <div>已执行: {task.executionCount} 次</div>}
                            {task.maxExecutions > 0 && <div>最大执行: {task.maxExecutions} 次</div>}
                          </div>

                          {task.status === "importing" && (
                            <div className="space-y-1">
                              <div className="flex justify-between text-xs">
                                <span>进度</span>
                                <span>{Math.round(task.progress)}%</span>
                              </div>
                              <Progress value={task.progress} className="h-1" />
                            </div>
                          )}

                          {task.syncStrategy === "scheduled" && task.status === "waiting" && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full bg-transparent"
                              onClick={() => executeTaskImmediately(task.id)}
                            >
                              立即执行一次
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      )}
    </div>
  )
}
