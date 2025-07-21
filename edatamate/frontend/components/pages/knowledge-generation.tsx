"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BookOpen, Plus, Search, Eye, Download, Upload, FileText, Database, Zap } from "lucide-react"

interface KnowledgeBase {
  id: number
  name: string
  description: string
  type: "document" | "qa" | "structured" | "mixed"
  status: "building" | "ready" | "updating" | "error"
  documentCount: number
  chunkCount: number
  vectorCount: number
  size: string
  createdAt: string
  lastUpdated: string
  config: {
    chunkSize: number
    overlap: number
    embeddingModel: string
    indexType: string
  }
}

interface ExtractionTask {
  id: number
  name: string
  sourceType: "pdf" | "web" | "database" | "text"
  targetKnowledgeBase: string
  status: "pending" | "running" | "completed" | "failed"
  progress: number
  extractedCount: number
  totalCount: number
  createdAt: string
}

const mockKnowledgeBases: KnowledgeBase[] = [
  {
    id: 1,
    name: "技术文档知识库",
    description: "包含产品技术文档、API文档和开发指南的知识库",
    type: "document",
    status: "ready",
    documentCount: 1250,
    chunkCount: 15600,
    vectorCount: 15600,
    size: "2.3 GB",
    createdAt: "2024-01-15",
    lastUpdated: "2024-01-22",
    config: {
      chunkSize: 512,
      overlap: 50,
      embeddingModel: "text-embedding-ada-002",
      indexType: "faiss",
    },
  },
  {
    id: 2,
    name: "FAQ问答知识库",
    description: "常见问题和答案的结构化知识库",
    type: "qa",
    status: "building",
    documentCount: 890,
    chunkCount: 2670,
    vectorCount: 2400,
    size: "156 MB",
    createdAt: "2024-01-20",
    lastUpdated: "2024-01-23",
    config: {
      chunkSize: 256,
      overlap: 25,
      embeddingModel: "text-embedding-ada-002",
      indexType: "pinecone",
    },
  },
  {
    id: 3,
    name: "混合知识库",
    description: "包含文档、问答和结构化数据的综合知识库",
    type: "mixed",
    status: "ready",
    documentCount: 3400,
    chunkCount: 45200,
    vectorCount: 45200,
    size: "5.8 GB",
    createdAt: "2024-01-10",
    lastUpdated: "2024-01-21",
    config: {
      chunkSize: 768,
      overlap: 100,
      embeddingModel: "text-embedding-3-large",
      indexType: "weaviate",
    },
  },
]

const mockExtractionTasks: ExtractionTask[] = [
  {
    id: 1,
    name: "PDF文档提取",
    sourceType: "pdf",
    targetKnowledgeBase: "技术文档知识库",
    status: "completed",
    progress: 100,
    extractedCount: 450,
    totalCount: 450,
    createdAt: "2024-01-22",
  },
  {
    id: 2,
    name: "网页内容抓取",
    sourceType: "web",
    targetKnowledgeBase: "FAQ问答知识库",
    status: "running",
    progress: 65,
    extractedCount: 325,
    totalCount: 500,
    createdAt: "2024-01-23",
  },
]

export default function KnowledgeGenerationPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>(mockKnowledgeBases)
  const [extractionTasks, setExtractionTasks] = useState<ExtractionTask[]>(mockExtractionTasks)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null)
  const [activeTab, setActiveTab] = useState("knowledge-bases")

  const [kbForm, setKbForm] = useState({
    name: "",
    description: "",
    type: "document",
    config: {
      chunkSize: 512,
      overlap: 50,
      embeddingModel: "text-embedding-ada-002",
      indexType: "faiss",
    },
  })

  const [extractionForm, setExtractionForm] = useState({
    name: "",
    sourceType: "pdf",
    targetKnowledgeBase: "",
    sourceConfig: {},
  })

  const handleCreateKnowledgeBase = () => {
    const newKB: KnowledgeBase = {
      id: Date.now(),
      name: kbForm.name,
      description: kbForm.description,
      type: kbForm.type as any,
      status: "building",
      documentCount: 0,
      chunkCount: 0,
      vectorCount: 0,
      size: "0 MB",
      createdAt: new Date().toISOString().split("T")[0],
      lastUpdated: new Date().toISOString().split("T")[0],
      config: kbForm.config,
    }

    setKnowledgeBases([newKB, ...knowledgeBases])
    setKbForm({
      name: "",
      description: "",
      type: "document",
      config: {
        chunkSize: 512,
        overlap: 50,
        embeddingModel: "text-embedding-ada-002",
        indexType: "faiss",
      },
    })
    setShowCreateForm(false)

    // 模拟构建过程
    setTimeout(() => {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === newKB.id
            ? {
                ...kb,
                status: "ready",
                documentCount: Math.floor(Math.random() * 500 + 100),
                chunkCount: Math.floor(Math.random() * 5000 + 1000),
                vectorCount: Math.floor(Math.random() * 5000 + 1000),
                size: `${(Math.random() * 2 + 0.5).toFixed(1)} GB`,
              }
            : kb,
        ),
      )
    }, 3000)
  }

  const handleCreateExtractionTask = () => {
    const newTask: ExtractionTask = {
      id: Date.now(),
      name: extractionForm.name,
      sourceType: extractionForm.sourceType as any,
      targetKnowledgeBase: extractionForm.targetKnowledgeBase,
      status: "pending",
      progress: 0,
      extractedCount: 0,
      totalCount: Math.floor(Math.random() * 500 + 100),
      createdAt: new Date().toISOString().split("T")[0],
    }

    setExtractionTasks([newTask, ...extractionTasks])
    setExtractionForm({
      name: "",
      sourceType: "pdf",
      targetKnowledgeBase: "",
      sourceConfig: {},
    })
    setShowCreateForm(false)
    setActiveTab("extraction-tasks")

    // 模拟提取过程
    setTimeout(() => {
      const interval = setInterval(() => {
        setExtractionTasks((prev) =>
          prev.map((task) => {
            if (task.id === newTask.id) {
              const newProgress = Math.min(task.progress + Math.random() * 10, 100)
              return {
                ...task,
                status: newProgress >= 100 ? "completed" : "running",
                progress: newProgress,
                extractedCount: Math.floor((newProgress / 100) * task.totalCount),
              }
            }
            return task
          }),
        )
      }, 500)

      setTimeout(() => clearInterval(interval), 10000)
    }, 1000)
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      building: { label: "构建中", variant: "default" as const, color: "bg-blue-100 text-blue-800" },
      ready: { label: "就绪", variant: "default" as const, color: "bg-green-100 text-green-800" },
      updating: { label: "更新中", variant: "default" as const, color: "bg-yellow-100 text-yellow-800" },
      error: { label: "错误", variant: "destructive" as const, color: "bg-red-100 text-red-800" },
      pending: { label: "等待中", variant: "secondary" as const, color: "bg-gray-100 text-gray-800" },
      running: { label: "运行中", variant: "default" as const, color: "bg-blue-100 text-blue-800" },
      completed: { label: "已完成", variant: "default" as const, color: "bg-green-100 text-green-800" },
      failed: { label: "失败", variant: "destructive" as const, color: "bg-red-100 text-red-800" },
    }
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.ready
  }

  const getTypeLabel = (type: string) => {
    const typeLabels = {
      document: "文档库",
      qa: "问答库",
      structured: "结构化",
      mixed: "混合库",
    }
    return typeLabels[type as keyof typeof typeLabels] || type
  }

  const getSourceTypeLabel = (type: string) => {
    const typeLabels = {
      pdf: "PDF文档",
      web: "网页内容",
      database: "数据库",
      text: "文本文件",
    }
    return typeLabels[type as keyof typeof typeLabels] || type
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 mt-2">构建面向RAG的智能知识库</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          创建知识库
        </Button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>创建知识库</CardTitle>
            <CardDescription>配置知识库参数和提取设置</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="knowledge-base">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="knowledge-base">知识库配置</TabsTrigger>
                <TabsTrigger value="extraction">数据提取</TabsTrigger>
              </TabsList>

              <TabsContent value="knowledge-base" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>知识库名称</Label>
                    <Input
                      value={kbForm.name}
                      onChange={(e) => setKbForm({ ...kbForm, name: e.target.value })}
                      placeholder="输入知识库名称"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>知识库类型</Label>
                    <Select value={kbForm.type} onValueChange={(value) => setKbForm({ ...kbForm, type: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="document">文档库</SelectItem>
                        <SelectItem value="qa">问答库</SelectItem>
                        <SelectItem value="structured">结构化</SelectItem>
                        <SelectItem value="mixed">混合库</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>描述</Label>
                  <Textarea
                    value={kbForm.description}
                    onChange={(e) => setKbForm({ ...kbForm, description: e.target.value })}
                    placeholder="描述知识库的用途和内容"
                    rows={3}
                  />
                </div>

                <div className="space-y-4 border-t pt-4">
                  <h4 className="font-medium">向量化配置</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>分块大小</Label>
                      <Input
                        type="number"
                        value={kbForm.config.chunkSize}
                        onChange={(e) =>
                          setKbForm({
                            ...kbForm,
                            config: { ...kbForm.config, chunkSize: Number(e.target.value) },
                          })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>重叠长度</Label>
                      <Input
                        type="number"
                        value={kbForm.config.overlap}
                        onChange={(e) =>
                          setKbForm({
                            ...kbForm,
                            config: { ...kbForm.config, overlap: Number(e.target.value) },
                          })
                        }
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>嵌入模型</Label>
                      <Select
                        value={kbForm.config.embeddingModel}
                        onValueChange={(value) =>
                          setKbForm({ ...kbForm, config: { ...kbForm.config, embeddingModel: value } })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="text-embedding-ada-002">text-embedding-ada-002</SelectItem>
                          <SelectItem value="text-embedding-3-small">text-embedding-3-small</SelectItem>
                          <SelectItem value="text-embedding-3-large">text-embedding-3-large</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>索引类型</Label>
                      <Select
                        value={kbForm.config.indexType}
                        onValueChange={(value) =>
                          setKbForm({ ...kbForm, config: { ...kbForm.config, indexType: value } })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="faiss">FAISS</SelectItem>
                          <SelectItem value="pinecone">Pinecone</SelectItem>
                          <SelectItem value="weaviate">Weaviate</SelectItem>
                          <SelectItem value="chroma">Chroma</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleCreateKnowledgeBase} disabled={!kbForm.name}>
                    创建知识库
                  </Button>
                  <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                    取消
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="extraction" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>任务名称</Label>
                    <Input
                      value={extractionForm.name}
                      onChange={(e) => setExtractionForm({ ...extractionForm, name: e.target.value })}
                      placeholder="输入提取任务名称"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>数据源类型</Label>
                    <Select
                      value={extractionForm.sourceType}
                      onValueChange={(value) => setExtractionForm({ ...extractionForm, sourceType: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pdf">PDF文档</SelectItem>
                        <SelectItem value="web">网页内容</SelectItem>
                        <SelectItem value="database">数据库</SelectItem>
                        <SelectItem value="text">文本文件</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>目标知识库</Label>
                  <Select
                    value={extractionForm.targetKnowledgeBase}
                    onValueChange={(value) => setExtractionForm({ ...extractionForm, targetKnowledgeBase: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择目标知识库" />
                    </SelectTrigger>
                    <SelectContent>
                      {knowledgeBases.map((kb) => (
                        <SelectItem key={kb.id} value={kb.name}>
                          {kb.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleCreateExtractionTask}
                    disabled={!extractionForm.name || !extractionForm.targetKnowledgeBase}
                  >
                    创建提取任务
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
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="knowledge-bases" className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            知识库 ({knowledgeBases.length})
          </TabsTrigger>
          <TabsTrigger value="extraction-tasks" className="flex items-center gap-2">
            <Upload className="w-4 h-4" />
            提取任务 ({extractionTasks.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="knowledge-bases" className="space-y-4">
          <div className="grid gap-4">
            {knowledgeBases.map((kb) => (
              <Card key={kb.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <BookOpen className="w-5 h-5 text-blue-500" />
                        <div>
                          <h4 className="font-medium">{kb.name}</h4>
                          <p className="text-sm text-gray-600">{kb.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{getTypeLabel(kb.type)}</Badge>
                        <Badge className={getStatusBadge(kb.status).color}>{getStatusBadge(kb.status).label}</Badge>
                        <Button variant="outline" size="sm" onClick={() => setSelectedKB(kb)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">文档数:</span>
                        <span className="ml-2 font-medium">{kb.documentCount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">分块数:</span>
                        <span className="ml-2 font-medium">{kb.chunkCount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">向量数:</span>
                        <span className="ml-2 font-medium">{kb.vectorCount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">大小:</span>
                        <span className="ml-2 font-medium">{kb.size}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500 border-t pt-2">
                      <span>创建: {kb.createdAt}</span>
                      <span>更新: {kb.lastUpdated}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="extraction-tasks" className="space-y-4">
          <div className="grid gap-4">
            {extractionTasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Upload className="w-5 h-5 text-green-500" />
                        <div>
                          <h4 className="font-medium">{task.name}</h4>
                          <p className="text-sm text-gray-600">
                            {getSourceTypeLabel(task.sourceType)} → {task.targetKnowledgeBase}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getStatusBadge(task.status).color}>{getStatusBadge(task.status).label}</Badge>
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {task.status === "running" && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>提取进度</span>
                          <span>
                            {task.extractedCount} / {task.totalCount}
                          </span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">源类型:</span>
                        <span className="ml-2 font-medium">{getSourceTypeLabel(task.sourceType)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">目标数量:</span>
                        <span className="ml-2 font-medium">{task.totalCount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">已提取:</span>
                        <span className="ml-2 font-medium">{task.extractedCount.toLocaleString()}</span>
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
      </Tabs>

      {/* Knowledge Base Detail Modal */}
      {selectedKB && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{selectedKB.name} - 详细信息</CardTitle>
              <Button variant="outline" onClick={() => setSelectedKB(null)}>
                关闭
              </Button>
            </div>
            <CardDescription>{selectedKB.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="overview">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">概览</TabsTrigger>
                <TabsTrigger value="config">配置</TabsTrigger>
                <TabsTrigger value="search">搜索测试</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{selectedKB.documentCount}</p>
                    <p className="text-sm text-gray-500">文档数量</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{selectedKB.chunkCount}</p>
                    <p className="text-sm text-gray-500">分块数量</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">{selectedKB.vectorCount}</p>
                    <p className="text-sm text-gray-500">向量数量</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="config" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>分块大小</Label>
                    <Input value={selectedKB.config.chunkSize} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>重叠长度</Label>
                    <Input value={selectedKB.config.overlap} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>嵌入模型</Label>
                    <Input value={selectedKB.config.embeddingModel} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>索引类型</Label>
                    <Input value={selectedKB.config.indexType} readOnly />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="search" className="space-y-4">
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Input placeholder="输入搜索查询..." className="flex-1" />
                    <Button>
                      <Search className="w-4 h-4 mr-2" />
                      搜索
                    </Button>
                  </div>
                  <div className="text-center py-8 text-gray-500">
                    <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>输入查询内容测试知识库搜索效果</p>
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
              <BookOpen className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{knowledgeBases.length}</p>
                <p className="text-sm text-gray-500">知识库总数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">
                  {knowledgeBases.reduce((sum, kb) => sum + kb.documentCount, 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">文档总数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">
                  {knowledgeBases.reduce((sum, kb) => sum + kb.vectorCount, 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">向量总数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">
                  {extractionTasks.filter((task) => task.status === "running").length}
                </p>
                <p className="text-sm text-gray-500">运行中任务</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
