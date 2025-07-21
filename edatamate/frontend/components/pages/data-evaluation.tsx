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
import {
  Target,
  Eye,
  Download,
  Plus,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Award,
  Zap,
  BarChart3,
  RefreshCw,
} from "lucide-react"

interface DatasetAnalytics {
  id: number
  name: string
  type: string
  totalItems: number
  annotatedItems: number
  qualityScore: number
  completionRate: number
  lastAnalyzed: string
  issues: Array<{
    type: "warning" | "error" | "info"
    message: string
    count: number
  }>
  distribution: Array<{
    category: string
    count: number
    percentage: number
  }>
  qualityMetrics: {
    duplicates: number
    missingLabels: number
    lowQuality: number
    inconsistent: number
  }
  performanceMetrics?: {
    accuracy?: number
    precision?: number
    recall?: number
    f1Score?: number
  }
  biasMetrics?: {
    genderBias?: number
    ageBias?: number
    racialBias?: number
  }
}

interface EvaluationTask {
  id: number
  name: string
  dataset: string
  type: "quality" | "performance" | "bias" | "comprehensive"
  status: "pending" | "running" | "completed" | "failed"
  progress: number
  score: number
  createdAt: string
  completedAt?: string
}

const mockAnalytics: DatasetAnalytics[] = [
  {
    id: 1,
    name: "图像分类数据集",
    type: "image_text",
    totalItems: 12500,
    annotatedItems: 12500,
    qualityScore: 92,
    completionRate: 100,
    lastAnalyzed: "2024-01-22 14:30",
    issues: [
      { type: "warning", message: "发现重复图像", count: 23 },
      { type: "info", message: "标签分布不均", count: 1 },
    ],
    distribution: [
      { category: "动物", count: 3200, percentage: 25.6 },
      { category: "风景", count: 2800, percentage: 22.4 },
      { category: "建筑", count: 2500, percentage: 20.0 },
      { category: "人物", count: 2000, percentage: 16.0 },
      { category: "其他", count: 2000, percentage: 16.0 },
    ],
    qualityMetrics: {
      duplicates: 23,
      missingLabels: 0,
      lowQuality: 45,
      inconsistent: 12,
    },
    performanceMetrics: {
      accuracy: 94,
      precision: 91,
      recall: 89,
      f1Score: 90,
    },
  },
  {
    id: 2,
    name: "问答对数据集",
    type: "qa",
    totalItems: 34000,
    annotatedItems: 28000,
    qualityScore: 87,
    completionRate: 82,
    lastAnalyzed: "2024-01-22 10:15",
    issues: [
      { type: "error", message: "问题格式不正确", count: 156 },
      { type: "warning", message: "答案过短", count: 89 },
      { type: "warning", message: "重复问答对", count: 34 },
    ],
    distribution: [
      { category: "技术问答", count: 12000, percentage: 35.3 },
      { category: "常识问答", count: 10000, percentage: 29.4 },
      { category: "事实问答", count: 8000, percentage: 23.5 },
      { category: "推理问答", count: 4000, percentage: 11.8 },
    ],
    qualityMetrics: {
      duplicates: 34,
      missingLabels: 6000,
      lowQuality: 156,
      inconsistent: 89,
    },
    biasMetrics: {
      genderBias: 15,
      ageBias: 8,
      racialBias: 12,
    },
  },
  {
    id: 3,
    name: "多模态数据集",
    type: "image_text",
    totalItems: 8900,
    annotatedItems: 5600,
    qualityScore: 78,
    completionRate: 63,
    lastAnalyzed: "2024-01-21 16:45",
    issues: [
      { type: "error", message: "图文不匹配", count: 78 },
      { type: "warning", message: "文本描述过简", count: 234 },
      { type: "info", message: "需要更多标注", count: 3300 },
    ],
    distribution: [
      { category: "已标注", count: 5600, percentage: 62.9 },
      { category: "待标注", count: 3300, percentage: 37.1 },
    ],
    qualityMetrics: {
      duplicates: 12,
      missingLabels: 3300,
      lowQuality: 78,
      inconsistent: 234,
    },
    biasMetrics: {
      genderBias: 22,
      ageBias: 18,
      racialBias: 25,
    },
  },
]

const mockEvaluationTasks: EvaluationTask[] = [
  {
    id: 1,
    name: "图像分类综合评估",
    dataset: "图像分类数据集",
    type: "comprehensive",
    status: "completed",
    progress: 100,
    score: 92,
    createdAt: "2024-01-20",
    completedAt: "2024-01-20",
  },
  {
    id: 2,
    name: "问答对偏见检测",
    dataset: "问答对数据集",
    type: "bias",
    status: "running",
    progress: 75,
    score: 0,
    createdAt: "2024-01-22",
  },
]

export default function DataEvaluationPage() {
  const [analytics, setAnalytics] = useState<DatasetAnalytics[]>(mockAnalytics)
  const [evaluationTasks, setEvaluationTasks] = useState<EvaluationTask[]>(mockEvaluationTasks)
  const [selectedDataset, setSelectedDataset] = useState<string>("all")
  const [selectedMetric, setSelectedMetric] = useState<string>("quality")
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedAnalytics, setSelectedAnalytics] = useState<DatasetAnalytics | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeTab, setActiveTab] = useState("overview")

  const [evaluationForm, setEvaluationForm] = useState({
    name: "",
    dataset: "",
    type: "comprehensive",
  })

  const handleCreateEvaluation = () => {
    const newTask: EvaluationTask = {
      id: Date.now(),
      name: evaluationForm.name,
      dataset: evaluationForm.dataset,
      type: evaluationForm.type as any,
      status: "pending",
      progress: 0,
      score: 0,
      createdAt: new Date().toISOString().split("T")[0],
    }

    setEvaluationTasks([newTask, ...evaluationTasks])
    setEvaluationForm({
      name: "",
      dataset: "",
      type: "comprehensive",
    })
    setShowCreateForm(false)
    setActiveTab("tasks")

    // 模拟评估执行
    setTimeout(() => {
      const interval = setInterval(() => {
        setEvaluationTasks((prev) =>
          prev.map((task) => {
            if (task.id === newTask.id) {
              const newProgress = Math.min(task.progress + Math.random() * 15, 100)
              if (newProgress >= 100) {
                return {
                  ...task,
                  status: "completed",
                  progress: 100,
                  score: Math.floor(Math.random() * 30 + 70),
                  completedAt: new Date().toISOString().split("T")[0],
                }
              }
              return { ...task, status: "running", progress: newProgress }
            }
            return task
          }),
        )
      }, 500)

      setTimeout(() => clearInterval(interval), 8000)
    }, 1000)
  }

  const handleRunAnalysis = (datasetId?: number) => {
    setIsAnalyzing(true)

    setTimeout(() => {
      if (datasetId) {
        setAnalytics((prev) =>
          prev.map((item) => (item.id === datasetId ? { ...item, lastAnalyzed: new Date().toLocaleString() } : item)),
        )
      } else {
        setAnalytics((prev) =>
          prev.map((item) => ({
            ...item,
            lastAnalyzed: new Date().toLocaleString(),
          })),
        )
      }
      setIsAnalyzing(false)
    }, 2000)
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: "等待中", variant: "secondary" as const, color: "bg-gray-100 text-gray-800" },
      running: { label: "评估中", variant: "default" as const, color: "bg-blue-100 text-blue-800" },
      completed: { label: "已完成", variant: "default" as const, color: "bg-green-100 text-green-800" },
      failed: { label: "失败", variant: "destructive" as const, color: "bg-red-100 text-red-800" },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
  }

  const getQualityColor = (score: number) => {
    if (score >= 90) return "text-green-600 bg-green-100"
    if (score >= 80) return "text-yellow-600 bg-yellow-100"
    if (score >= 70) return "text-orange-600 bg-orange-100"
    return "text-red-600 bg-red-100"
  }

  const getIssueIcon = (type: string) => {
    switch (type) {
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "info":
        return <Eye className="w-4 h-4 text-blue-500" />
      default:
        return <CheckCircle className="w-4 h-4 text-green-500" />
    }
  }

  const getTypeLabel = (type: string) => {
    const typeLabels = {
      quality: "质量评估",
      performance: "性能评估",
      bias: "偏见检测",
      comprehensive: "综合评估",
    }
    return typeLabels[type as keyof typeof typeLabels] || type
  }

  const filteredAnalytics =
    selectedDataset === "all" ? analytics : analytics.filter((item) => item.id.toString() === selectedDataset)

  const totalItems = analytics.reduce((sum, item) => sum + item.totalItems, 0)
  const totalAnnotated = analytics.reduce((sum, item) => sum + item.annotatedItems, 0)
  const avgQuality = Math.round(analytics.reduce((sum, item) => sum + item.qualityScore, 0) / analytics.length)
  const totalIssues = analytics.reduce(
    (sum, item) => sum + item.issues.reduce((issueSum, issue) => issueSum + issue.count, 0),
    0,
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 mt-2">全面的数据质量分析、性能评估和偏见检测</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => handleRunAnalysis()} disabled={isAnalyzing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isAnalyzing ? "animate-spin" : ""}`} />
            {isAnalyzing ? "分析中..." : "重新分析"}
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建评估任务
          </Button>
        </div>
      </div>

      {/* Create Evaluation Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>创建评估任务</CardTitle>
            <CardDescription>选择数据集和评估类型</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>任务名称</Label>
                <Input
                  value={evaluationForm.name}
                  onChange={(e) => setEvaluationForm({ ...evaluationForm, name: e.target.value })}
                  placeholder="输入评估任务名称"
                />
              </div>
              <div className="space-y-2">
                <Label>评估类型</Label>
                <Select
                  value={evaluationForm.type}
                  onValueChange={(value) => setEvaluationForm({ ...evaluationForm, type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="comprehensive">综合评估</SelectItem>
                    <SelectItem value="quality">质量评估</SelectItem>
                    <SelectItem value="performance">性能评估</SelectItem>
                    <SelectItem value="bias">偏见检测</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>目标数据集</Label>
              <Select
                value={evaluationForm.dataset}
                onValueChange={(value) => setEvaluationForm({ ...evaluationForm, dataset: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择要评估的数据集" />
                </SelectTrigger>
                <SelectContent>
                  {analytics.map((item) => (
                    <SelectItem key={item.id} value={item.name}>
                      {item.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleCreateEvaluation} disabled={!evaluationForm.name || !evaluationForm.dataset}>
                创建评估任务
              </Button>
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                取消
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">数据概览</TabsTrigger>
          <TabsTrigger value="analysis">质量分析</TabsTrigger>
          <TabsTrigger value="tasks">评估任务</TabsTrigger>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Overview Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold">{totalItems.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">数据项总数</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">{totalAnnotated.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">已标注数据</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-500" />
                  <div>
                    <p className="text-2xl font-bold">{avgQuality}%</p>
                    <p className="text-sm text-gray-500">平均质量分</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-500" />
                  <div>
                    <p className="text-2xl font-bold">{totalIssues}</p>
                    <p className="text-sm text-gray-500">待处理问题</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Dataset Cards */}
          <div className="space-y-4">
            {analytics.map((dataset) => (
              <Card key={dataset.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{dataset.name}</h4>
                        <p className="text-sm text-gray-600">最后分析: {dataset.lastAnalyzed}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getQualityColor(dataset.qualityScore)}>质量分: {dataset.qualityScore}%</Badge>
                        <Button variant="outline" size="sm" onClick={() => setSelectedAnalytics(dataset)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>完成进度</span>
                          <span>{dataset.completionRate}%</span>
                        </div>
                        <Progress value={dataset.completionRate} className="h-2" />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>质量评分</span>
                          <span>{dataset.qualityScore}%</span>
                        </div>
                        <Progress value={dataset.qualityScore} className="h-2" />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>问题数量</span>
                          <span>{dataset.issues.reduce((sum, issue) => sum + issue.count, 0)}</span>
                        </div>
                        <Progress
                          value={Math.max(
                            0,
                            100 -
                              (dataset.issues.reduce((sum, issue) => sum + issue.count, 0) / dataset.totalItems) * 100,
                          )}
                          className="h-2"
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择数据集" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有数据集</SelectItem>
                      {analytics.map((item) => (
                        <SelectItem key={item.id} value={item.id.toString()}>
                          {item.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex-1">
                  <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择指标" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quality">质量分析</SelectItem>
                      <SelectItem value="distribution">分布分析</SelectItem>
                      <SelectItem value="performance">性能分析</SelectItem>
                      <SelectItem value="bias">偏见分析</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Analysis */}
          <div className="space-y-6">
            {filteredAnalytics.map((dataset) => (
              <Card key={dataset.id}>
                <CardHeader>
                  <CardTitle>{dataset.name} - 详细分析</CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="quality">
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="quality">质量指标</TabsTrigger>
                      <TabsTrigger value="distribution">分布分析</TabsTrigger>
                      <TabsTrigger value="performance">性能指标</TabsTrigger>
                      <TabsTrigger value="bias">偏见检测</TabsTrigger>
                    </TabsList>

                    <TabsContent value="quality" className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-red-600">{dataset.qualityMetrics.duplicates}</p>
                          <p className="text-xs text-gray-500">重复项</p>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-yellow-600">{dataset.qualityMetrics.missingLabels}</p>
                          <p className="text-xs text-gray-500">缺失标签</p>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-orange-600">{dataset.qualityMetrics.lowQuality}</p>
                          <p className="text-xs text-gray-500">低质量</p>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-600">{dataset.qualityMetrics.inconsistent}</p>
                          <p className="text-xs text-gray-500">不一致</p>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="distribution" className="space-y-4">
                      <div className="space-y-2">
                        {dataset.distribution.map((item, index) => (
                          <div key={index} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span>{item.category}</span>
                              <span>
                                {item.count.toLocaleString()} ({item.percentage}%)
                              </span>
                            </div>
                            <Progress value={item.percentage} className="h-2" />
                          </div>
                        ))}
                      </div>
                    </TabsContent>

                    <TabsContent value="performance" className="space-y-4">
                      {dataset.performanceMetrics ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(dataset.performanceMetrics).map(([key, value]) => (
                            <div key={key} className="text-center p-4 border rounded-lg">
                              <p className="text-2xl font-bold text-blue-600">{value}%</p>
                              <p className="text-sm text-gray-500 capitalize">{key}</p>
                              <Progress value={value} className="h-2 mt-2" />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                          <p>暂无性能评估数据</p>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="bias" className="space-y-4">
                      {dataset.biasMetrics ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {Object.entries(dataset.biasMetrics).map(([key, value]) => (
                            <div key={key} className="text-center p-4 border rounded-lg">
                              <p className={`text-2xl font-bold ${value > 20 ? "text-red-600" : "text-green-600"}`}>
                                {value}%
                              </p>
                              <p className="text-sm text-gray-500 capitalize">{key}</p>
                              <Progress value={value} className="h-2 mt-2" />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                          <p>暂无偏见检测数据</p>
                        </div>
                      )}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <div className="space-y-4">
            {evaluationTasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Target className="w-5 h-5 text-blue-500" />
                        <div>
                          <h4 className="font-medium">{task.name}</h4>
                          <p className="text-sm text-gray-600">
                            {getTypeLabel(task.type)} • {task.dataset}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {task.status === "completed" && (
                          <div className="text-2xl font-bold text-green-600">{task.score}分</div>
                        )}
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
                          <span>评估进度</span>
                          <span>{Math.round(task.progress)}%</span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}

                    <div className="flex items-center justify-between text-xs text-gray-500 border-t pt-2">
                      <span>创建时间: {task.createdAt}</span>
                      {task.completedAt && <span>完成时间: {task.completedAt}</span>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          {/* Trend Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                趋势分析
              </CardTitle>
              <CardDescription>数据集质量和完成度的历史趋势</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">质量趋势</h4>
                    <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center">
                      <p className="text-gray-500 text-sm">质量趋势图表 (模拟)</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">完成度趋势</h4>
                    <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center">
                      <p className="text-gray-500 text-sm">完成度趋势图表 (模拟)</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                改进建议
              </CardTitle>
              <CardDescription>基于分析结果的优化建议</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-900">优化数据分布</p>
                    <p className="text-xs text-blue-700">建议增加数量较少的类别数据，以平衡整体分布</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-900">处理重复数据</p>
                    <p className="text-xs text-yellow-700">发现多个数据集存在重复项，建议进行去重处理</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                  <Target className="w-5 h-5 text-green-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-green-900">减少偏见影响</p>
                    <p className="text-xs text-green-700">检测到性别和年龄偏见，建议增加多样性数据</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dataset Detail Modal */}
      {selectedAnalytics && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{selectedAnalytics.name} - 详细报告</CardTitle>
              <Button variant="outline" onClick={() => setSelectedAnalytics(null)}>
                关闭
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Issues */}
              {selectedAnalytics.issues.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">发现的问题</h4>
                  <div className="space-y-2">
                    {selectedAnalytics.issues.map((issue, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                        {getIssueIcon(issue.type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{issue.message}</p>
                          <p className="text-xs text-gray-500">{issue.count} 个项目受影响</p>
                        </div>
                        <Button variant="outline" size="sm">
                          查看详情
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{evaluationTasks.length}</p>
                <p className="text-sm text-gray-500">评估任务</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{avgQuality}</p>
                <p className="text-sm text-gray-500">平均得分</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">
                  {evaluationTasks.filter((task) => task.status === "running").length}
                </p>
                <p className="text-sm text-gray-500">运行中</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">{totalIssues}</p>
                <p className="text-sm text-gray-500">发现问题</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
