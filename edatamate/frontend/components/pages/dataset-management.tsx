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
} from "lucide-react"

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
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            创建数据集
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
    </div>
  )
}
