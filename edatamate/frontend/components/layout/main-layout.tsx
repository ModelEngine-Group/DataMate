"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  FolderOpen,
  Tag,
  Settings,
  Sparkles,
  Target,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
  Shuffle,
  Scale,
} from "lucide-react"
import WelcomePage from "@/app/page"
import DatasetManagementPage from "@/components/pages/dataset-management"
import DataAnnotationPage from "@/components/pages/data-annotation"
import DataProcessingPage from "@/components/pages/data-processing"
import DataOrchestrationPage from "@/components/pages/data-orchestration"
import DataSynthesisPage from "@/components/pages/data-synthesis"
import DataEvaluationPage from "@/components/pages/data-evaluation"
import KnowledgeGenerationPage from "@/components/pages/knowledge-generation"
import DataAgentPage from "@/components/pages/data-agent"

interface MenuItem {
  id: string
  title: string
  icon: any
  badge?: number
  children?: MenuItem[]
}

const menuItems: MenuItem[] = [
  {
    id: "management",
    title: "数据管理",
    icon: FolderOpen,
  },
  {
    id: "processing",
    title: "数据处理",
    icon: Settings,
  },
  {
    id: "annotation",
    title: "数据标注",
    icon: Tag,
  },
  {
    id: "synthesis",
    title: "数据合成",
    icon: Shuffle,
    children: [
      {
        id: "synthesis-tasks",
        title: "合成任务",
        icon: Sparkles,
      },
      {
        id: "ratio-tasks",
        title: "配比任务",
        icon: Scale,
      },
    ],
  },
  {
    id: "evaluation",
    title: "数据评估",
    icon: Target,
    badge: 4,
  },
  {
    id: "knowledge",
    title: "知识生成",
    icon: BookOpen,
  },
]

export default function MainLayout() {
  const [activeItem, setActiveItem] = useState<string>("welcome")
  const [expandedItems, setExpandedItems] = useState<string[]>(["synthesis"])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const toggleExpanded = (itemId: string) => {
    setExpandedItems((prev) => (prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]))
  }

  const renderContent = () => {
    switch (activeItem) {
      case "welcome":
        return <WelcomePage onItemSelect={setActiveItem} />
      case "agent":
        return <DataAgentPage />
      case "management":
        return <DatasetManagementPage />
      case "processing":
        return <DataProcessingPage />
      case "annotation":
        return <DataAnnotationPage />
      case "synthesis":
      case "synthesis-tasks":
      case "ratio-tasks":
        return <DataSynthesisPage activeTab={activeItem} />
      case "evaluation":
        return <DataEvaluationPage />
      case "knowledge":
        return <KnowledgeGenerationPage />
      default:
        return <WelcomePage onItemSelect={setActiveItem} />
    }
  }

  const renderMenuItem = (item: MenuItem, level = 0) => {
    const isActive = activeItem === item.id
    const isExpanded = expandedItems.includes(item.id)
    const hasChildren = item.children && item.children.length > 0

    return (
      <div key={item.id}>
        <Button
          variant={isActive ? "secondary" : "ghost"}
          className={`w-full justify-start gap-3 h-10 px-3 relative ${
            level > 0 ? "ml-6 w-[calc(100%-1.5rem)]" : ""
          } ${isActive ? "bg-blue-100 text-blue-700 border-r-2 border-blue-500" : "text-gray-700 hover:bg-gray-100"}`}
          onClick={() => {
            if (hasChildren) {
              toggleExpanded(item.id)
            } else {
              setActiveItem(item.id)
            }
          }}
        >
          <item.icon className="w-4 h-4 flex-shrink-0" />
          <span className="flex-1 text-left text-sm font-medium">{item.title}</span>
          {item.badge && (
            <Badge variant="secondary" className="ml-auto text-xs bg-blue-500 text-white">
              {item.badge}
            </Badge>
          )}
          {hasChildren && (
            <div className="ml-auto">
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </div>
          )}
        </Button>

        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">{item.children!.map((child) => renderMenuItem(child, level + 1))}</div>
        )}
      </div>
    )
  }

  // 如果是Data Agent页面，渲染独立的全屏页面
  if (activeItem === "agent") {
    return <DataAgentPage onBack={() => setActiveItem("welcome")} />
  }

  // 如果是数据智能编排页面，渲染独立的全屏页面
  if (activeItem === "orchestration") {
    return <DataOrchestrationPage onBack={() => setActiveItem("welcome")} />
  }

  if (activeItem === "welcome") {
    return renderContent()
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-64" : "w-16"
        } bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {sidebarOpen && (
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveItem("welcome")}>
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900">ML Dataset Tool</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          <div className="space-y-2">{menuItems.map((item) => renderMenuItem(item))}</div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          {sidebarOpen ? (
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start bg-transparent">
                帮助文档
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start bg-transparent">
                设置
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <Button variant="ghost" size="sm" className="w-full p-2">
                ?
              </Button>
              <Button variant="ghost" size="sm" className="w-full p-2">
                ⚙
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {menuItems.find((item) => item.id === activeItem)?.title ||
                  menuItems
                    .find((item) => item.children?.some((child) => child.id === activeItem))
                    ?.children?.find((child) => child.id === activeItem)?.title ||
                  "欢迎"}
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                导出数据
              </Button>
              <Button size="sm">新建任务</Button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="p-6">{renderContent()}</div>
        </div>
      </div>
    </div>
  )
}
