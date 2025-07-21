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
  Tag,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  Edit,
  Upload,
  Play,
  Pause,
} from "lucide-react"

export default function DataAnnotationPage() {
  const [activeTab, setActiveTab] = useState("tasks")

  const annotationTasks = [
    {
      id: 1,
      name: "肺癌病理图像标注",
      dataset: "肺癌WSI病理图像数据集",
      type: "图像分类",
      status: "进行中",
      progress: 85,
      assignees: ["张医生", "李医生", "王医生"],
      deadline: "2024-02-15",
      priority: "高",
      description: "对肺癌病理切片进行癌症分级标注",
    },
    {
      id: 2,
      name: "皮肤病变检测标注",
      dataset: "皮肤镜图像数据集",
      type: "目标检测",
      status: "已完成",
      progress: 100,
      assignees: ["赵医生", "钱医生"],
      deadline: "2024-01-30",
      priority: "中",
      description: "标注皮肤病变区域和类型",
    },
    {
      id: 3,
      name: "CT影像分割标注",
      dataset: "CT影像数据集",
      type: "图像分割",
      status: "待开始",
      progress: 0,
      assignees: ["孙医生"],
      deadline: "2024-03-01",
      priority: "中",
      description: "对肺部CT影像进行器官和病变分割",
    },
  ]

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      进行中: { color: "bg-blue-100 text-blue-800", icon: Clock },
      已完成: { color: "bg-green-100 text-green-800", icon: CheckCircle },
      待开始: { color: "bg-gray-100 text-gray-800", icon: AlertCircle },
      已暂停: { color: "bg-yellow-100 text-yellow-800", icon: Pause },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.待开始
  }

  const getPriorityBadge = (priority: string) => {
    const priorityConfig = {
      高: "bg-red-100 text-red-800",
      中: "bg-yellow-100 text-yellow-800",
      低: "bg-green-100 text-green-800",
    }
    return priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.中
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">数据标注</h1>
          <p className="text-gray-600 mt-2">管理和执行数据标注任务</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            导入标注
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            新建标注任务
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="tasks">标注任务</TabsTrigger>
          <TabsTrigger value="tools">标注工具</TabsTrigger>
          <TabsTrigger value="quality">质量控制</TabsTrigger>
          <TabsTrigger value="analytics">统计分析</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="space-y-6">
          {/* Search and Filter */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input placeholder="搜索标注任务..." className="pl-10" />
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
            {annotationTasks.map((task) => (
              <Card key={task.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{task.name}</h3>
                          <Badge className={getStatusBadge(task.status).color}>{task.status}</Badge>
                          <Badge className={getPriorityBadge(task.priority)}>{task.priority}优先级</Badge>
                        </div>
                        <p className="text-gray-600 text-sm mb-2">{task.description}</p>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>数据集: {task.dataset}</span>
                          <span>类型: {task.type}</span>
                          <span>截止: {task.deadline}</span>
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
                        {task.status === "进行中" ? (
                          <Button variant="outline" size="sm">
                            <Pause className="w-4 h-4 mr-1" />
                            暂停
                          </Button>
                        ) : task.status === "待开始" ? (
                          <Button size="sm">
                            <Play className="w-4 h-4 mr-1" />
                            开始
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    {/* Progress */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>完成进度</span>
                        <span>{task.progress}%</span>
                      </div>
                      <Progress value={task.progress} className="h-2" />
                    </div>

                    {/* Assignees */}
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-600">标注人员:</span>
                      <div className="flex gap-1">
                        {task.assignees.map((assignee, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {assignee}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="tools" className="space-y-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="w-5 h-5" />
                  图像分类标注
                </CardTitle>
                <CardDescription>为图像数据添加分类标签</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">启动工具</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="w-5 h-5" />
                  目标检测标注
                </CardTitle>
                <CardDescription>标注图像中的目标位置和类别</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">启动工具</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="w-5 h-5" />
                  图像分割标注
                </CardTitle>
                <CardDescription>像素级别的图像分割标注</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">启动工具</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="quality" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>标注质量统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>平均准确率</span>
                    <span className="font-bold text-green-600">94.2%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>一致性检查通过率</span>
                    <span className="font-bold text-blue-600">91.8%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>返工率</span>
                    <span className="font-bold text-yellow-600">5.3%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>质量控制措施</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">双人标注验证</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">专家审核机制</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">自动质量检测</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">156</div>
                  <div className="text-sm text-gray-500">总任务数</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">89</div>
                  <div className="text-sm text-gray-500">已完成</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">45</div>
                  <div className="text-sm text-gray-500">进行中</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-600">22</div>
                  <div className="text-sm text-gray-500">待开始</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
