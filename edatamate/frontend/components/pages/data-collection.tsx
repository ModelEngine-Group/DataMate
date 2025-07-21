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
  Download,
  Database,
  Globe,
  HardDrive,
  Cloud,
  Eye,
  Edit,
  CheckCircle,
  Clock,
  AlertCircle,
} from "lucide-react"

export default function DataCollectionPage() {
  const [activeTab, setActiveTab] = useState("sources")

  const dataSources = [
    {
      id: 1,
      name: "医院PACS系统",
      type: "数据库连接",
      status: "已连接",
      description: "三甲医院影像存档系统",
      dataTypes: ["DICOM", "医学影像"],
      lastSync: "2024-01-20 10:30",
      totalRecords: 15420,
    },
    {
      id: 2,
      name: "病理科文件服务器",
      type: "文件系统",
      status: "同步中",
      description: "WSI病理切片图像存储",
      dataTypes: ["WSI", "病理图像"],
      lastSync: "2024-01-20 09:15",
      totalRecords: 8934,
    },
    {
      id: 3,
      name: "公开医学数据集",
      type: "API接口",
      status: "待配置",
      description: "NIH公开医学影像数据库",
      dataTypes: ["CT", "MRI", "X-Ray"],
      lastSync: "未同步",
      totalRecords: 0,
    },
  ]

  const collectionTasks = [
    {
      id: 1,
      name: "肺癌CT影像采集",
      source: "医院PACS系统",
      status: "进行中",
      progress: 75,
      collected: 2847,
      target: 3800,
      startTime: "2024-01-20 08:00",
    },
    {
      id: 2,
      name: "病理切片批量导入",
      source: "病理科文件服务器",
      status: "已完成",
      progress: 100,
      collected: 1250,
      target: 1250,
      startTime: "2024-01-19 14:30",
    },
    {
      id: 3,
      name: "皮肤镜图像收集",
      source: "皮肤科数据库",
      status: "队列中",
      progress: 0,
      collected: 0,
      target: 2000,
      startTime: "待开始",
    },
  ]

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      已连接: { color: "bg-green-100 text-green-800", icon: CheckCircle },
      同步中: { color: "bg-blue-100 text-blue-800", icon: Clock },
      待配置: { color: "bg-yellow-100 text-yellow-800", icon: AlertCircle },
      进行中: { color: "bg-blue-100 text-blue-800", icon: Clock },
      已完成: { color: "bg-green-100 text-green-800", icon: CheckCircle },
      队列中: { color: "bg-gray-100 text-gray-800", icon: Clock },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.待配置
  }

  const getTypeIcon = (type: string) => {
    const iconMap = {
      数据库连接: Database,
      文件系统: HardDrive,
      API接口: Globe,
      云存储: Cloud,
    }
    const IconComponent = iconMap[type as keyof typeof iconMap] || Database
    return <IconComponent className="w-4 h-4" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">数据收集</h1>
          <p className="text-gray-600 mt-2">管理数据源和数据采集任务</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            导出配置
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            添加数据源
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="sources">数据源</TabsTrigger>
          <TabsTrigger value="tasks">采集任务</TabsTrigger>
          <TabsTrigger value="schedule">定时任务</TabsTrigger>
          <TabsTrigger value="monitoring">监控面板</TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="space-y-6">
          {/* Search and Filter */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input placeholder="搜索数据源..." className="pl-10" />
                  </div>
                </div>
                <Button variant="outline">
                  <Filter className="w-4 h-4 mr-2" />
                  筛选
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Data Sources */}
          <div className="grid gap-6">
            {dataSources.map((source) => (
              <Card key={source.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          {getTypeIcon(source.type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900">{source.name}</h3>
                            <Badge className={getStatusBadge(source.status).color}>{source.status}</Badge>
                          </div>
                          <p className="text-gray-600 text-sm mb-2">{source.description}</p>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span>类型: {source.type}</span>
                            <span>最后同步: {source.lastSync}</span>
                            <span>记录数: {source.totalRecords.toLocaleString()}</span>
                          </div>
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
                        <Button variant="outline" size="sm">
                          <Database className="w-4 h-4 mr-1" />
                          同步
                        </Button>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {source.dataTypes.map((type, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {type}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-6">
          <div className="grid gap-6">
            {collectionTasks.map((task) => (
              <Card key={task.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{task.name}</h3>
                          <Badge className={getStatusBadge(task.status).color}>{task.status}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>数据源: {task.source}</span>
                          <span>开始时间: {task.startTime}</span>
                          <span>
                            进度: {task.collected} / {task.target}
                          </span>
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
                      </div>
                    </div>

                    {/* Progress */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>采集进度</span>
                        <span>{task.progress}%</span>
                      </div>
                      <Progress value={task.progress} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="schedule" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>定时采集任务</CardTitle>
              <CardDescription>配置自动化的数据采集计划</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 border rounded-lg">
                  <div>
                    <h4 className="font-medium">每日PACS同步</h4>
                    <p className="text-sm text-gray-600">每天凌晨2:00自动同步新增影像</p>
                  </div>
                  <Badge className="bg-green-100 text-green-800">已启用</Badge>
                </div>
                <div className="flex justify-between items-center p-4 border rounded-lg">
                  <div>
                    <h4 className="font-medium">周度病理数据备份</h4>
                    <p className="text-sm text-gray-600">每周日进行完整数据备份</p>
                  </div>
                  <Badge className="bg-gray-100 text-gray-800">已暂停</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          <div className="grid md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">8</div>
                  <div className="text-sm text-gray-500">活跃数据源</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">156K</div>
                  <div className="text-sm text-gray-500">今日采集</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">3</div>
                  <div className="text-sm text-gray-500">进行中任务</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">2.3TB</div>
                  <div className="text-sm text-gray-500">总数据量</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
</merged_code>
