"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Shuffle, Scale, Plus, Eye, Download, Trash2, Settings, Sparkles, Target, BarChart3, Clock } from "lucide-react"

interface SynthesisTask {
  id: number
  name: string
  type: "text" | "image" | "qa" | "multimodal"
  status: "pending" | "running" | "completed" | "failed"
  progress: number
  sourceDataset: string
  targetCount: number
  generatedCount: number
  createdAt: string
  config: any
}

interface RatioTask {
  id: number
  name: string
  datasets: Array<{
    name: string
    ratio: number
    count: number
  }>
  status: "pending" | "running" | "completed" | "failed"
  progress: number
  totalTarget: number
  createdAt: string
}

const mockSynthesisTasks: SynthesisTask[] = [
  {
    id: 1,
    name: "图像分类数据增强",
    type: "image",
    status: "completed",
    progress: 100,
    sourceDataset: "原始图像数据集",
    targetCount: 5000,
    generatedCount: 5000,
    createdAt: "2024-01-20",
    config: {
      augmentation: ["rotation", "flip", "brightness"],
      quality: "high",
    },
  },
  {
    id: 2,
    name: "问答对生成任务",
    type: "qa",
    status: "running",
    progress: 65,
    sourceDataset: "知识库文档",
    targetCount: 10000,
    generatedCount: 6500,
    createdAt: "2024-01-22",
    config: {
      model: "gpt-4",
      temperature: 0.7,
    },
  },
  {
    id: 3,
    name: "多模态数据合成",
    type: "multimodal",
    status: "pending",
    progress: 0,
    sourceDataset: "图文对数据集",
    targetCount: 3000,
    generatedCount: 0,
    createdAt: "2024-01-23",
    config: {
      imageStyle: "realistic",
      textLength: "medium",
    },
  },
]

const mockRatioTasks: RatioTask[] = [
  {
    id: 1,
    name: "训练集配比任务",
    datasets: [
      { name: "图像分类A", ratio: 40, count: 4000 },
      { name: "图像分类B", ratio: 35, count: 3500 },
      { name: "图像分类C", ratio: 25, count: 2500 },
    ],
    status: "completed",
    progress: 100,
    totalTarget: 10000,
    createdAt: "2024-01-21",
  },
  {
    id: 2,
    name: "多领域QA配比",
    datasets: [
      { name: "技术问答", ratio: 50, count: 5000 },
      { name: "常识问答", ratio: 30, count: 3000 },
      { name: "专业问答", ratio: 20, count: 2000 },
    ],
    status: "running",
    progress: 75,
    totalTarget: 10000,
    createdAt: "2024-01-22",
  },
]

interface DataSynthesisPageProps {
  activeTab?: string
}

export default function DataSynthesisPage({ activeTab = "synthesis" }: DataSynthesisPageProps) {
  const [synthesisTasks, setSynthesisTasks] = useState<SynthesisTask[]>(mockSynthesisTasks)
  const [ratioTasks, setRatioTasks] = useState<RatioTask[]>(mockRatioTasks)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [currentTab, setCurrentTab] = useState(activeTab === "ratio-tasks" ? "ratio" : "synthesis")

  // Synthesis form state
  const [synthesisForm, setSynthesisForm] = useState({
    name: "",
    type: "text",
    sourceDataset: "",
    targetCount: 1000,
    config: {},
  })

  // Ratio form state
  const [ratioForm, setRatioForm] = useState({
    name: "",
    datasets: [
      { name: "", ratio: 50, count: 0 },
      { name: "", ratio: 50, count: 0 },
    ],
    totalTarget: 10000,
  })

  const handleCreateSynthesisTask = () => {
    const newTask: SynthesisTask = {
      id: Date.now(),
      name: synthesisForm.name,
      type: synthesisForm.type as any,
      status: "pending",
      progress: 0,
      sourceDataset: synthesisForm.sourceDataset,
      targetCount: synthesisForm.targetCount,
      generatedCount: 0,
      createdAt: new Date().toISOString().split("T")[0],
      config: synthesisForm.config,
    }

    setSynthesisTasks([newTask, ...synthesisTasks])
    setSynthesisForm({
      name: "",
      type: "text",
      sourceDataset: "",
      targetCount: 1000,
      config: {},
    })
    setShowCreateForm(false)

    // 模拟任务执行
    setTimeout(() => {
      const interval = setInterval(() => {
        setSynthesisTasks((prev) =>
          prev.map((task) => {
            if (task.id === newTask.id) {
              const newProgress = Math.min(task.progress + Math.random() * 10, 100)
              return {
                ...task,
                status: newProgress >= 100 ? "completed" : "running",
                progress: newProgress,
                generatedCount: Math.floor((newProgress / 100) * task.targetCount),
              }
            }
            return task
          }),
        )
      }, 500)

      setTimeout(() => clearInterval(interval), 10000)
    }, 1000)
  }

  const handleCreateRatioTask = () => {
    const newTask: RatioTask = {
      id: Date.now(),
      name: ratioForm.name,
      datasets: ratioForm.datasets.map((ds) => ({
        ...ds,
        count: Math.floor((ds.ratio / 100) * ratioForm.totalTarget),
      })),
      status: "pending",
      progress: 0,
      totalTarget: ratioForm.totalTarget,
      createdAt: new Date().toISOString().split("T")[0],
    }

    setRatioTasks([newTask, ...ratioTasks])
    setRatioForm({
      name: "",
      datasets: [
        { name: "", ratio: 50, count: 0 },
        { name: "", ratio: 50, count: 0 },
      ],
      totalTarget: 10000,
    })
    setShowCreateForm(false)

    // 模拟任务执行
    setTimeout(() => {
      const interval = setInterval(() => {
        setRatioTasks((prev) =>
          prev.map((task) => {
            if (task.id === newTask.id) {
              const newProgress = Math.min(task.progress + Math.random() * 15, 100)
              return {
                ...task,
                status: newProgress >= 100 ? "completed" : "running",
                progress: newProgress,
              }
            }
            return task
          }),
        )
      }, 300)

      setTimeout(() => clearInterval(interval), 8000)
    }, 1000)
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: "等待中", variant: "secondary" as const, color: "bg-gray-100 text-gray-800" },
      running: { label: "运行中", variant: "default" as const, color: "bg-blue-100 text-blue-800" },
      completed: { label: "已完成", variant: "default" as const, color: "bg-green-100 text-green-800" },
      failed: { label: "失败", variant: "destructive" as const, color: "bg-red-100 text-red-800" },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
  }

  const getTypeIcon = (type: string) => {
    const iconMap = {
      text: Sparkles,
      image: Target,
      qa: BarChart3,
      multimodal: Settings,
    }
    const IconComponent = iconMap[type as keyof typeof iconMap] || Sparkles
    return <IconComponent className="w-4 h-4" />
  }

  const addDatasetToRatio = () => {
    setRatioForm({
      ...ratioForm,
      datasets: [...ratioForm.datasets, { name: "", ratio: 0, count: 0 }],
    })
  }

  const updateDatasetRatio = (index: number, field: string, value: any) => {
    const newDatasets = [...ratioForm.datasets]
    newDatasets[index] = { ...newDatasets[index], [field]: value }

    // 自动计算count
    if (field === "ratio") {
      newDatasets[index].count = Math.floor((value / 100) * ratioForm.totalTarget)
    }

    setRatioForm({ ...ratioForm, datasets: newDatasets })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 mt-2">智能数据合成和配比管理</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          创建任务
        </Button>
      </div>

      {/* Create Task Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>创建新任务</CardTitle>
            <CardDescription>选择任务类型并配置参数</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={currentTab} onValueChange={setCurrentTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="synthesis">合成任务</TabsTrigger>
                <TabsTrigger value="ratio">配比任务</TabsTrigger>
              </TabsList>

              <TabsContent value="synthesis" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>任务名称</Label>
                    <Input
                      value={synthesisForm.name}
                      onChange={(e) => setSynthesisForm({ ...synthesisForm, name: e.target.value })}
                      placeholder="输入任务名称"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>数据类型</Label>
                    <Select
                      value={synthesisForm.type}
                      onValueChange={(value) => setSynthesisForm({ ...synthesisForm, type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="text">文本数据</SelectItem>
                        <SelectItem value="image">图像数据</SelectItem>
                        <SelectItem value="qa">问答对</SelectItem>
                        <SelectItem value="multimodal">多模态</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>源数据集</Label>
                    <Select
                      value={synthesisForm.sourceDataset}
                      onValueChange={(value) => setSynthesisForm({ ...synthesisForm, sourceDataset: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择源数据集" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dataset1">图像分类数据集</SelectItem>
                        <SelectItem value="dataset2">问答对数据集</SelectItem>
                        <SelectItem value="dataset3">多模态数据集</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>目标数量</Label>
                    <Input
                      type="number"
                      value={synthesisForm.targetCount}
                      onChange={(e) => setSynthesisForm({ ...synthesisForm, targetCount: Number(e.target.value) })}
                      placeholder="目标生成数量"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleCreateSynthesisTask}
                    disabled={!synthesisForm.name || !synthesisForm.sourceDataset}
                  >
                    创建合成任务
                  </Button>
                  <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                    取消
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="ratio" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>任务名称</Label>
                    <Input
                      value={ratioForm.name}
                      onChange={(e) => setRatioForm({ ...ratioForm, name: e.target.value })}
                      placeholder="输入任务名称"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>目标总数</Label>
                    <Input
                      type="number"
                      value={ratioForm.totalTarget}
                      onChange={(e) => setRatioForm({ ...ratioForm, totalTarget: Number(e.target.value) })}
                      placeholder="目标总数量"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>数据集配比</Label>
                    <Button variant="outline" size="sm" onClick={addDatasetToRatio}>
                      <Plus className="w-4 h-4 mr-1" />
                      添加数据集
                    </Button>
                  </div>

                  {ratioForm.datasets.map((dataset, index) => (
                    <div key={index} className="grid grid-cols-4 gap-4 p-4 border rounded-lg">
                      <div className="space-y-2">
                        <Label className="text-xs">数据集名称</Label>
                        <Select
                          value={dataset.name}
                          onValueChange={(value) => updateDatasetRatio(index, "name", value)}
                        >
                          <SelectTrigger className="h-8">
                            <SelectValue placeholder="选择数据集" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="dataset1">图像分类A</SelectItem>
                            <SelectItem value="dataset2">图像分类B</SelectItem>
                            <SelectItem value="dataset3">图像分类C</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs">比例 (%)</Label>
                        <Input
                          type="number"
                          className="h-8"
                          value={dataset.ratio}
                          onChange={(e) => updateDatasetRatio(index, "ratio", Number(e.target.value))}
                          min="0"
                          max="100"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs">数量</Label>
                        <Input type="number" className="h-8" value={dataset.count} readOnly />
                      </div>
                      <div className="flex items-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const newDatasets = ratioForm.datasets.filter((_, i) => i !== index)
                            setRatioForm({ ...ratioForm, datasets: newDatasets })
                          }}
                          className="h-8"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleCreateRatioTask}
                    disabled={!ratioForm.name || ratioForm.datasets.some((ds) => !ds.name)}
                  >
                    创建配比任务
                  </Button>
                  <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                    取消
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs value={currentTab} onValueChange={setCurrentTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="synthesis" className="flex items-center gap-2">
            <Shuffle className="w-4 h-4" />
            合成任务 ({synthesisTasks.length})
          </TabsTrigger>
          <TabsTrigger value="ratio" className="flex items-center gap-2">
            <Scale className="w-4 h-4" />
            配比任务 ({ratioTasks.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="synthesis" className="space-y-4">
          <div className="grid gap-4">
            {synthesisTasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getTypeIcon(task.type)}
                        <div>
                          <h4 className="font-medium">{task.name}</h4>
                          <p className="text-sm text-gray-600">源数据集: {task.sourceDataset}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getStatusBadge(task.status).color}>{getStatusBadge(task.status).label}</Badge>
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {task.status === "running" && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>生成进度</span>
                          <span>
                            {task.generatedCount} / {task.targetCount}
                          </span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">类型:</span>
                        <span className="ml-2 font-medium">{task.type}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">目标数量:</span>
                        <span className="ml-2 font-medium">{task.targetCount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">已生成:</span>
                        <span className="ml-2 font-medium">{task.generatedCount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">创建时间:</span>
                        <span className="ml-2 font-medium">{task.createdAt}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="ratio" className="space-y-4">
          <div className="grid gap-4">
            {ratioTasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Scale className="w-5 h-5 text-purple-500" />
                        <div>
                          <h4 className="font-medium">{task.name}</h4>
                          <p className="text-sm text-gray-600">目标总数: {task.totalTarget.toLocaleString()}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getStatusBadge(task.status).color}>{getStatusBadge(task.status).label}</Badge>
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {task.status === "running" && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>配比进度</span>
                          <span>{Math.round(task.progress)}%</span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}

                    <div className="space-y-3">
                      <h5 className="font-medium text-sm">数据集配比</h5>
                      <div className="grid gap-2">
                        {task.datasets.map((dataset, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                              <span className="font-medium">{dataset.name}</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                              <span>{dataset.ratio}%</span>
                              <span className="text-gray-500">{dataset.count.toLocaleString()} 项</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="text-xs text-gray-500 border-t pt-2">创建时间: {task.createdAt}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Shuffle className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{synthesisTasks.length}</p>
                <p className="text-sm text-gray-500">合成任务</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Scale className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{ratioTasks.length}</p>
                <p className="text-sm text-gray-500">配比任务</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">
                  {[...synthesisTasks, ...ratioTasks].filter((task) => task.status === "running").length}
                </p>
                <p className="text-sm text-gray-500">运行中</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">
                  {synthesisTasks.reduce((sum, task) => sum + task.generatedCount, 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">已生成数据</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
