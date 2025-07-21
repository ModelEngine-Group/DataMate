"use client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  FolderOpen,
  Tag,
  Settings,
  ArrowRight,
  Sparkles,
  Target,
  Zap,
  Shield,
  BookOpen,
  Shuffle,
  Database,
  MessageSquare,
  GitBranch,
} from "lucide-react"

const menuItems = [
  {
    id: "management",
    title: "数据管理",
    icon: FolderOpen,
    description: "创建、导入和管理数据集",
    color: "bg-blue-500",
  },
  {
    id: "processing",
    title: "数据处理",
    icon: Settings,
    description: "数据清洗和预处理",
    color: "bg-purple-500",
  },
  {
    id: "annotation",
    title: "数据标注",
    icon: Tag,
    description: "对数据进行标注和标记",
    color: "bg-green-500",
  },
  {
    id: "synthesis",
    title: "数据合成",
    icon: Shuffle,
    description: "智能数据合成和配比",
    color: "bg-pink-500",
  },
  {
    id: "evaluation",
    title: "数据评估",
    icon: Target,
    description: "质量分析、性能评估和偏见检测",
    color: "bg-indigo-500",
  },
  {
    id: "knowledge",
    title: "知识生成",
    icon: BookOpen,
    description: "面向RAG的知识库构建",
    color: "bg-teal-500",
  },
]

const features = [
  {
    icon: GitBranch,
    title: "智能编排",
    description: "可视化数据处理流程编排，拖拽式设计复杂的数据处理管道",
  },
  {
    icon: MessageSquare,
    title: "对话助手",
    description: "通过自然语言对话完成复杂的数据集操作和业务流程",
  },
  {
    icon: Target,
    title: "全面评估",
    description: "多维度数据质量评估，包含统计分析、性能测试和偏见检测",
  },
  {
    icon: Zap,
    title: "高效处理",
    description: "完整的数据处理流水线，从原始数据到可用数据集",
  },
  {
    icon: Shield,
    title: "知识管理",
    description: "构建面向RAG的知识库，支持智能问答和检索",
  },
]

interface WelcomePageProps {
  onItemSelect: (itemId: string) => void
}

export default function WelcomePage({ onItemSelect }: WelcomePageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            ML数据集准备工具
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            构建高质量
            <span className="text-blue-600"> ML数据集</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            从数据管理到知识生成，一站式解决机器学习数据准备的所有需求。
            支持对话式操作、智能编排、数据合成、智能标注、全面评估和RAG知识库构建。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg"
              onClick={() => onItemSelect("management")}
            >
              <Database className="mr-2 w-4 h-4" />
              开始使用
            </Button>
            <Button
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg"
              onClick={() => onItemSelect("agent")}
            >
              <MessageSquare className="mr-2 w-4 h-4" />
              对话助手
            </Button>
            <Button size="lg" variant="outline" onClick={() => onItemSelect("orchestration")}>
              数据智能编排
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6 mb-16">
          {features.map((feature, index) => (
            <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center pb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Menu Items Grid */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">功能模块</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map((item, index) => (
              <Card
                key={item.id}
                className="cursor-pointer hover:shadow-lg transition-all duration-200 border-0 shadow-md relative overflow-hidden group"
                onClick={() => onItemSelect(item.id)}
              >
                <CardHeader className="text-center relative">
                  <div
                    className={`w-16 h-16 ${item.color} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform duration-200`}
                  >
                    <item.icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    
                  </div>
                  <CardTitle className="text-xl group-hover:text-blue-600 transition-colors">{item.title}</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <CardDescription className="text-sm group-hover:text-gray-700 transition-colors">
                    {item.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Data Orchestration Highlight */}
        <div className="mb-16">
          <Card className="bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200 shadow-lg">
            <CardContent className="p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-amber-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <GitBranch className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-orange-900 mb-2">数据智能编排 - 可视化流程设计</h3>
                <p className="text-orange-700">拖拽式设计复杂数据处理管道，让数据流转更加直观高效</p>
              </div>

              <div className="grid md:grid-cols-2 gap-8 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-900">🎯 核心功能：</h4>
                  <div className="space-y-2">
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">可视化流程设计器</div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">丰富的数据处理组件库</div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">实时流程执行监控</div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-900">⚡ 智能特性：</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Zap className="w-4 h-4 text-orange-500" />
                      自动优化数据流转路径
                    </div>
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Target className="w-4 h-4 text-orange-500" />
                      智能错误检测和修复建议
                    </div>
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Sparkles className="w-4 h-4 text-orange-500" />
                      模板化流程快速复用
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white shadow-lg"
                  onClick={() => onItemSelect("orchestration")}
                >
                  <GitBranch className="mr-2 w-4 h-4" />
                  开始编排
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Data Agent Highlight */}
        <div className="mb-16">
          <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200 shadow-lg">
            <CardContent className="p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-purple-900 mb-2">Data Agent - 对话式业务操作</h3>
                <p className="text-purple-700">告别复杂界面，用自然语言完成所有数据集相关业务</p>
              </div>

              <div className="grid md:grid-cols-2 gap-8 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-purple-900">💬 对话示例：</h4>
                  <div className="space-y-2">
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "帮我创建一个图像分类数据集"
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "分析一下数据质量，生成报告"
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "启动合成任务，目标1000条数据"
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-purple-900">🚀 智能特性：</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Zap className="w-4 h-4 text-purple-500" />
                      理解复杂需求，自动执行
                    </div>
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Target className="w-4 h-4 text-purple-500" />
                      提供专业建议和优化方案
                    </div>
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Sparkles className="w-4 h-4 text-purple-500" />
                      学习使用习惯，个性化服务
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg"
                  onClick={() => onItemSelect("agent")}
                >
                  <MessageSquare className="mr-2 w-4 h-4" />
                  开始对话
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Workflow Showcase */}
        <div className="mb-16">
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 shadow-lg">
            <CardContent className="p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-blue-900 mb-2">完整的数据处理工作流</h3>
                <p className="text-blue-700">从原始数据到高质量数据集的全流程解决方案</p>
              </div>

              <div className="grid md:grid-cols-4 gap-6 mb-8">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <FolderOpen className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">数据收集</h4>
                  <p className="text-sm text-blue-700">支持多种数据源导入，包括本地文件、数据库、API等</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <GitBranch className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">智能编排</h4>
                  <p className="text-sm text-blue-700">可视化设计数据处理流程，自动化执行复杂任务</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Settings className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">智能处理</h4>
                  <p className="text-sm text-blue-700">自动化的数据清洗、标注和质量评估流程</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Target className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">质量保证</h4>
                  <p className="text-sm text-blue-700">全面的质量评估和偏见检测，确保数据集可靠性</p>
                </div>
              </div>

              <div className="text-center">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg"
                  onClick={() => onItemSelect("management")}
                >
                  <Sparkles className="mr-2 w-4 h-4" />
                  开始构建数据集
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">平台统计</h3>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">1,234</div>
              <div className="text-gray-600 text-sm">数据集总数</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">45,678</div>
              <div className="text-gray-600 text-sm">已标注数据</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600 mb-2">567</div>
              <div className="text-gray-600 text-sm">编排流程</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">892</div>
              <div className="text-gray-600 text-sm">合成任务</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-teal-600 mb-2">156</div>
              <div className="text-gray-600 text-sm">知识库</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-pink-600 mb-2">2,456</div>
              <div className="text-gray-600 text-sm">AI对话次数</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
