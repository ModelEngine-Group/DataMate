"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Plus,
  Search,
  Filter,
  Settings,
  Play,
  Pause,
  Upload,
  Eye,
  Edit,
  Clock,
  CheckCircle,
  AlertCircle,
  Zap,
} from "lucide-react"

export default function DataProcessingPage() {
  const [activeTab, setActiveTab] = useState("tasks")

  const processingTasks = [
    {
      id: 1,
      name: "WSI图像预处理",
      dataset: "肺癌WSI病理图像数据集",
      type: "图像处理",
      status: "运行中",
      progress: 68,
      startTime: "2024-01-20 09:30",
      estimatedTime: "2小时15分钟",
      operations: ["格式转换", "尺寸标准化", "质量增强"],
    },
    {
      id: 2,
      name: "CT影像DICOM转换",
      dataset: "CT影像数据集",
      type: "格式转换",
      status: "已完成",
      progress: 100,
      startTime: "2024-01-19 14:20",
      estimatedTime: "已完成",
      operations: ["DICOM解析", "格式转换", "元数据提取"],
    },
    {
      id: 3,
      name: "皮肤镜图像清洗",
      dataset: "皮肤镜图像数据集",
      type: "数据清洗",
      status: "队列中",
      progress: 0,
      startTime: "待开始",
      estimatedTime: "1小时30分钟",
      operations: ["噪声去除", "对比度调整", "异常检测"],
    },
  ]

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      运行中: { color: "bg-blue-100 text-blue-800", icon: Play },
      已完成: { color: "bg-green-100 text-green-800", icon: CheckCircle },
      队列中: { color: "bg-yellow-100 text-yellow-800", icon: Clock },
      已暂停: { color: "bg-gray-100 text-gray-800", icon: Pause },
      失败: { color: "bg-red-100 text-red-800", icon: AlertCircle },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.队列中
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">数据处理</h1>
          <p className="text-gray-600 mt-2">数据清洗、转换和预处理任务管理</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            批量导入
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            新建处理任务
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="tasks">处理任务</TabsTrigger>
          <TabsTrigger value="templates">处理模板</TabsTrigger>
          <TabsTrigger value="monitoring">实时监控</TabsTrigger>
          <TabsTrigger value="history">历史记录</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="space-y-6">
          {/* Search and Filter */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input placeholder="搜索处理任务..." className="pl-10" />
                  </div>
                </div>
                <Button variant="outline">
                  <Filter className="w-4 h-4 mr-2" />
                  筛选
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Task List */}
          <div className="grid gap-6">
            {processingTasks.map((task) => (
              <Card key={task.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{task.name}</h3>
                          <Badge className={getStatusBadge(task.status).color}>{task.status}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                          <span>数据集: {task.dataset}</span>
                          <span>类型: {task.type}</span>
                          <span>开始时间: {task.startTime}</span>
                          <span>预计用时: {task.estimatedTime}</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {task.operations.map((op, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {op}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4 mr-1" />
                          查看
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="w-4 h-4 mr-1" />
                          编辑
                        </Button>
                        {task.status === "运行中" ? (
                          <Button variant="outline" size="sm">
                            <Pause className="w-4 h-4 mr-1" />
                            暂停
                          </Button>
                        ) : task.status === "队列中" ? (
                          <Button size="sm">
                            <Play className="w-4 h-4 mr-1" />
                            开始
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    {/* Progress */}
                    {task.progress > 0 && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>处理进度</span>
                          <span>{task.progress}%</span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  医学影像预处理
                </CardTitle>
                <CardDescription>专用于医学影像的标准化预处理流程</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-4">
                  <Badge variant="outline" className="text-xs">
                    DICOM转换
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    窗宽窗位调整
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    噪声去除
                  </Badge>
                </div>
                <Button className="w-full">使用模板</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  病理图像处理
                </CardTitle>
                <CardDescription>WSI病理切片图像的专业处理流程</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-4">
                  <Badge variant="outline" className="text-xs">
                    格式标准化
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    色彩校正
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    分辨率调整
                  </Badge>
                </div>
                <Button className="w-full">使用模板</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  通用图像清洗
                </CardTitle>
                <CardDescription>适用于各类图像数据的通用清洗流程</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-4">
                  <Badge variant="outline" className="text-xs">
                    质量检查
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    重复检测
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    异常过滤
                  </Badge>
                </div>
                <Button className="w-full">使用模板</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold">3</p>
                    <p className="text-sm text-gray-500">运行中任务</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-yellow-500" />
                  <div>
                    <p className="text-2xl font-bold">7</p>
                    <p className="text-sm text-gray-500">队列中任务</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">45</p>
                    <p className="text-sm text-gray-500">今日完成</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="text-2xl font-bold">2</p>
                    <p className="text-sm text-gray-500">失败任务</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>系统资源使用情况</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>CPU使用率</span>
                    <span>72%</span>
                  </div>
                  <Progress value={72} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>内存使用率</span>
                    <span>58%</span>
                  </div>
                  <Progress value={58} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>磁盘I/O</span>
                    <span>34%</span>
                  </div>
                  <Progress value={34} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>处理历史记录</CardTitle>
              <CardDescription>查看过去30天的数据处理历史</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium">乳腺癌数据预处理</h4>
                    <p className="text-sm text-gray-600">2024-01-18 完成</p>
                  </div>
                  <Badge className="bg-green-100 text-green-800">成功</Badge>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium">内镜图像格式转换</h4>
                    <p className="text-sm text-gray-600">2024-01-17 完成</p>
                  </div>
                  <Badge className="bg-green-100 text-green-800">成功</Badge>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium">CT影像质量检查</h4>
                    <p className="text-sm text-gray-600">2024-01-16 失败</p>
                  </div>
                  <Badge className="bg-red-100 text-red-800">失败</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
