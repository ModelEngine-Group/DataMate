"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BarChart3, PieChart, TrendingUp, Activity, Users, Database, Download, Share } from "lucide-react"

export default function DataAnalyticsPage() {
  const [activeTab, setActiveTab] = useState("overview")

  const analyticsData = {
    totalDatasets: 156,
    totalSamples: 2456789,
    activeUsers: 89,
    completedTasks: 1234,
    qualityScore: 94.2,
    growthRate: 12.5,
  }

  const datasetStats = [
    { name: "医学影像", count: 45, percentage: 28.8, color: "bg-blue-500" },
    { name: "病理图像", count: 38, percentage: 24.4, color: "bg-green-500" },
    { name: "放射影像", count: 32, percentage: 20.5, color: "bg-purple-500" },
    { name: "内镜影像", count: 25, percentage: 16.0, color: "bg-orange-500" },
    { name: "其他", count: 16, percentage: 10.3, color: "bg-gray-500" },
  ]

  const qualityMetrics = [
    { metric: "数据完整性", value: 96.8, target: 95, status: "excellent" },
    { metric: "标注准确率", value: 94.2, target: 90, status: "good" },
    { metric: "数据一致性", value: 91.5, target: 85, status: "good" },
    { metric: "处理效率", value: 88.3, target: 80, status: "good" },
  ]

  const getStatusColor = (status: string) => {
    const colors = {
      excellent: "text-green-600",
      good: "text-blue-600",
      warning: "text-yellow-600",
      critical: "text-red-600",
    }
    return colors[status as keyof typeof colors] || colors.good
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">数据分析</h1>
          <p className="text-gray-600 mt-2">数据集统计分析和质量监控</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            导出报告
          </Button>
          <Button variant="outline">
            <Share className="w-4 h-4 mr-2" />
            分享仪表板
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">总览</TabsTrigger>
          <TabsTrigger value="datasets">数据集分析</TabsTrigger>
          <TabsTrigger value="quality">质量分析</TabsTrigger>
          <TabsTrigger value="usage">使用统计</TabsTrigger>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold">{analyticsData.totalDatasets}</p>
                    <p className="text-sm text-gray-500">数据集总数</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">{(analyticsData.totalSamples / 1000000).toFixed(1)}M</p>
                    <p className="text-sm text-gray-500">样本总数</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-purple-500" />
                  <div>
                    <p className="text-2xl font-bold">{analyticsData.activeUsers}</p>
                    <p className="text-sm text-gray-500">活跃用户</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-orange-500" />
                  <div>
                    <p className="text-2xl font-bold">{analyticsData.completedTasks}</p>
                    <p className="text-sm text-gray-500">完成任务</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-teal-500" />
                  <div>
                    <p className="text-2xl font-bold">{analyticsData.qualityScore}%</p>
                    <p className="text-sm text-gray-500">质量分数</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-pink-500" />
                  <div>
                    <p className="text-2xl font-bold">+{analyticsData.growthRate}%</p>
                    <p className="text-sm text-gray-500">月增长率</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5" />
                  数据集类型分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {datasetStats.map((stat, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{stat.name}</span>
                        <span>{stat.count} ({stat.percentage}%)</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`${stat.color} h-2 rounded-full`}
                          style={{ width: `${stat.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  质量指标概览
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {qualityMetrics.map((metric, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{metric.metric}</span>
                        <span className={`font-medium ${getStatusColor(metric.status)}`}>
                          {metric.value}%
                        </span>
                      </div>
                      <Progress value={metric.value} className="h-2" />
                      <div className="text-xs text-gray-500">
                        目标: {metric.target}%
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="datasets" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>数据集详细统计</CardTitle>
              <CardDescription>各类数据集的详细分析数据</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space\
