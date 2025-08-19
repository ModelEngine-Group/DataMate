"use client";

import type React from "react";

import { useState } from "react";
import {
  Plus,
  Eye,
  Edit,
  ChevronRight,
  File,
  CheckCircle,
  Clock,
  AlertCircle,
  MoreHorizontal,
  Trash2,
  History,
  Scissors,
  VideoIcon as Vector,
  Server,
  FileText,
  GitBranch,
} from "lucide-react";

const mockChunks = Array.from({ length: 23 }, (_, i) => ({
  id: i + 1,
  content: `这是第 ${
    i + 1
  } 个文档分块的内容示例。在实际应用中，这里会显示从原始文档中提取和分割的具体文本内容。用户可以在这里查看和编辑分块的内容，确保知识库的质量和准确性。这个分块包含了重要的业务信息和技术细节，需要仔细维护以确保检索的准确性。`,
  position: i + 1,
  tokens: Math.floor(Math.random() * 200) + 100,
  embedding: Array.from({ length: 1536 }, () => Math.random() - 0.5),
  similarity: (Math.random() * 0.3 + 0.7).toFixed(3),
  createdAt: "2024-01-22 10:35",
  updatedAt: "2024-01-22 10:35",
  vectorId: `vec_${i + 1}_${Math.random().toString(36).substr(2, 9)}`,
  sliceOperator: ["semantic-split", "paragraph-split", "table-extract"][
    Math.floor(Math.random() * 3)
  ],
  parentChunkId: i > 0 ? Math.floor(Math.random() * i) + 1 : undefined,
  metadata: {
    source: "API文档.pdf",
    page: Math.floor(i / 5) + 1,
    section: `第${Math.floor(i / 3) + 1}章`,
  },
}));

const mockQAPairs = [
  {
    id: 1,
    question: "什么是API文档的主要用途？",
    answer:
      "API文档的主要用途是为开发者提供详细的接口说明，包括请求参数、响应格式和使用示例.",
  },
  {
    id: 2,
    question: "如何正确使用这个API？",
    answer:
      "使用API时需要先获取访问令牌，然后按照文档中的格式发送请求，注意处理错误响应.",
  },
];

const vectorDatabases = [
  {
    id: "pinecone",
    name: "Pinecone",
    description: "云端向量数据库，高性能检索",
  },
  {
    id: "weaviate",
    name: "Weaviate",
    description: "开源向量数据库，支持多模态",
  },
  { id: "qdrant", name: "Qdrant", description: "高性能向量搜索引擎" },
  { id: "chroma", name: "ChromaDB", description: "轻量级向量数据库" },
  { id: "milvus", name: "Milvus", description: "分布式向量数据库" },
  { id: "faiss", name: "FAISS", description: "Facebook AI 相似性搜索库" },
];
const sliceOperators: SliceOperator[] = [
  {
    id: "paragraph-split",
    name: "段落分割",
    description: "按段落自然分割文档",
    type: "text",
    icon: "📄",
    params: { minLength: 50, maxLength: 1000 },
  },
  {
    id: "sentence-split",
    name: "句子分割",
    description: "按句子边界分割文档",
    type: "text",
    icon: "📝",
    params: { maxSentences: 5, overlap: 1 },
  },
  {
    id: "semantic-split",
    name: "语义分割",
    description: "基于语义相似度智能分割",
    type: "semantic",
    icon: "🧠",
    params: { threshold: 0.7, windowSize: 3 },
  },
  {
    id: "length-split",
    name: "长度分割",
    description: "按固定字符长度分割",
    type: "text",
    icon: "📏",
    params: { chunkSize: 512, overlap: 50 },
  },
  {
    id: "structure-split",
    name: "结构化分割",
    description: "按文档结构（标题、章节）分割",
    type: "structure",
    icon: "🏗️",
    params: { preserveHeaders: true, minSectionLength: 100 },
  },
  {
    id: "table-extract",
    name: "表格提取",
    description: "提取并单独处理表格内容",
    type: "structure",
    icon: "📊",
    params: { includeHeaders: true, mergeRows: false },
  },
  {
    id: "code-extract",
    name: "代码提取",
    description: "识别并提取代码块",
    type: "custom",
    icon: "💻",
    params: {
      languages: ["python", "javascript", "sql"],
      preserveIndentation: true,
    },
  },
  {
    id: "qa-extract",
    name: "问答提取",
    description: "自动识别问答格式内容",
    type: "semantic",
    icon: "❓",
    params: { confidenceThreshold: 0.8, generateAnswers: true },
  },
];
const getStatusLabel = (status: string) => {
  const labels = {
    ready: "就绪",
    processing: "处理中",
    vectorizing: "向量化中",
    importing: "导入中",
    error: "错误",
    disabled: "已禁用",
    completed: "已完成",
  };
  return labels[status as keyof typeof labels] || status;
};

const KnowledgeFileDetailPage: React.FC = () => {
  const router = useRouter();

  const [showSliceTraceDialog, setShowSliceTraceDialog] = useState<
    number | null
  >(null);
  const [selectedFile, setSelectedFile] = useState({
    id: 1,
    name: "API文档.pdf",
    size: "2.5 MB",
    chunkCount: mockChunks.length,
    status: "已向量化",
    vectorizationStatus: "completed",
    vectorizationProgress: 100,
    source: "upload",
    datasetId: null,
    uploadedAt: "2024-01-22 10:30",
  });
  const [selectedKB, setSelectedKB] = useState({
    id: 1,
    name: "API知识库",
    config: {
      vectorDimension: 1536,
      embeddingModel: "text-embedding-3-large",
    },
    vectorDatabase: "vector_db_1",
  });
  const chunksPerPage = 5;
  const [currentChunkPage, setCurrentChunkPage] = useState(1);

  const totalPages = Math.ceil(mockChunks.length / chunksPerPage);

  const startIndex = (currentChunkPage - 1) * chunksPerPage;
  const currentChunks = mockChunks.slice(
    startIndex,
    startIndex + chunksPerPage
  );

  const [editingChunk, setEditingChunk] = useState<number | null>(null);
  const [editChunkContent, setEditChunkContent] = useState("");

  const [chunkDetailModal, setChunkDetailModal] = useState<number | null>(null);

  const handleEditChunk = (chunkId: number, content: string) => {
    setEditingChunk(chunkId);
    setEditChunkContent(content);
  };

  const handleSaveChunk = (chunkId: number) => {
    alert(`保存分块 ${chunkId} 的修改`);
    setEditingChunk(null);
    setEditChunkContent("");
  };

  const handleDeleteChunk = (chunkId: number) => {
    if (confirm(`确定要删除分块 ${chunkId} 吗？`)) {
      alert(`删除��块 ${chunkId}`);
    }
  };

  const handleViewChunkDetail = (chunkId: number) => {
    setChunkDetailModal(chunkId);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <button
          onClick={() => router.push("/knowledge-generation")}
          className="hover:text-blue-600"
        >
          知识库
        </button>
        <ChevronRight className="w-4 h-4" />
        <button
          onClick={() => router.push("/knowledge-generation/detail/1")}
          className="hover:text-blue-600"
        >
          {selectedKB?.name}
        </button>
        <ChevronRight className="w-4 h-4" />
        <span>{selectedFile.name}</span>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <File className="w-5 h-5" />
                {selectedFile.name}
              </CardTitle>
              <CardDescription>
                {selectedFile.size} • {selectedFile.chunkCount} 个分块 •{" "}
                {getStatusLabel(selectedFile.status)}
                {selectedFile.source === "dataset" && (
                  <Badge variant="outline" className="ml-2">
                    数据集: {selectedFile.datasetId}
                  </Badge>
                )}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSliceTraceDialog(selectedFile.id)}
              >
                <History className="w-4 h-4 mr-1" />
                切片回溯
              </Button>
              {selectedFile.vectorizationStatus !== "completed" && (
                <Button variant="outline" size="sm" onClick={() => {}}>
                  <Vector className="w-4 h-4 mr-1" />
                  开始向量化
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="chunks">
            <TabsList>
              <TabsTrigger value="chunks">分块内容</TabsTrigger>
              <TabsTrigger value="vectors">向量信息</TabsTrigger>
              <TabsTrigger value="metadata">元数据</TabsTrigger>
              <TabsTrigger value="processing">处理日志</TabsTrigger>
            </TabsList>

            <TabsContent value="chunks" className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  共 {mockChunks.length} 个分块，第 {startIndex + 1}-
                  {Math.min(startIndex + chunksPerPage, mockChunks.length)} 个
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentChunkPage(Math.max(1, currentChunkPage - 1))
                    }
                    disabled={currentChunkPage === 1}
                  >
                    上一页
                  </Button>
                  <span className="text-sm text-gray-600">
                    {currentChunkPage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentChunkPage(
                        Math.min(totalPages, currentChunkPage + 1)
                      )
                    }
                    disabled={currentChunkPage === totalPages}
                  >
                    下一页
                  </Button>
                </div>
              </div>

              <div className="space-y-4">
                {currentChunks.map((chunk) => (
                  <Card key={chunk.id} className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">分块 {chunk.id}</Badge>
                          <Badge variant="secondary" className="text-xs">
                            {sliceOperators.find(
                              (op) => op.id === chunk.sliceOperator
                            )?.name || chunk.sliceOperator}
                          </Badge>
                          {chunk.vectorId && (
                            <Badge variant="outline" className="text-xs">
                              <Vector className="w-3 h-3 mr-1" />
                              已向量化
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm leading-relaxed text-gray-700 line-clamp-3">
                          {editingChunk === chunk.id ? (
                            <Textarea
                              value={editChunkContent}
                              onChange={(e) =>
                                setEditChunkContent(e.target.value)
                              }
                              rows={3}
                              className="text-sm"
                            />
                          ) : (
                            chunk.content
                          )}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span>位置: {chunk.position}</span>
                          <span>Token: {chunk.tokens}</span>
                          {chunk.metadata?.page && (
                            <span>页码: {chunk.metadata.page}</span>
                          )}
                          {chunk.metadata?.section && (
                            <span>章节: {chunk.metadata.section}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        {editingChunk === chunk.id ? (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleSaveChunk(chunk.id)}
                            >
                              保存
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingChunk(null);
                                setEditChunkContent("");
                              }}
                            >
                              取消
                            </Button>
                          </>
                        ) : (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => handleViewChunkDetail(chunk.id)}
                              >
                                <Eye className="w-4 h-4 mr-2" />
                                查看详情
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() =>
                                  handleEditChunk(chunk.id, chunk.content)
                                }
                              >
                                <Edit className="w-4 h-4 mr-2" />
                                编辑内容
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() =>
                                  setShowSliceTraceDialog(chunk.id)
                                }
                              >
                                <GitBranch className="w-4 h-4 mr-2" />
                                切片回溯
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleDeleteChunk(chunk.id)}
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                删除
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="vectors" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Vector className="w-5 h-5 text-purple-600" />
                    <h4 className="font-medium">向量化状态</h4>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">状态:</span>
                      <Badge
                        variant={getStatusBadgeVariant(
                          selectedFile.vectorizationStatus || "pending"
                        )}
                      >
                        {getStatusLabel(
                          selectedFile.vectorizationStatus || "pending"
                        )}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">向量维度:</span>
                      <span className="font-medium">
                        {selectedKB?.config.vectorDimension}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">向量数量:</span>
                      <span className="font-medium">
                        {selectedFile.chunkCount}
                      </span>
                    </div>
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Server className="w-5 h-5 text-blue-600" />
                    <h4 className="font-medium">存储信息</h4>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">向量数据库:</span>
                      <span className="font-medium">
                        {
                          vectorDatabases.find(
                            (db) => db.id === selectedKB?.vectorDatabase
                          )?.name
                        }
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">嵌入模型:</span>
                      <span className="font-medium">
                        {selectedKB?.config.embeddingModel}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
              {selectedFile.vectorizationStatus === "processing" && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>向量化进度</span>
                    <span>{selectedFile.progress}%</span>
                  </div>
                  <Progress value={selectedFile.progress} className="h-2" />
                </div>
              )}
            </TabsContent>

            <TabsContent value="metadata" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>文件类型</Label>
                  <Input value={selectedFile.type} readOnly />
                </div>
                <div>
                  <Label>文件大小</Label>
                  <Input value={selectedFile.size} readOnly />
                </div>
                <div>
                  <Label>分块数量</Label>
                  <Input value={selectedFile.chunkCount} readOnly />
                </div>
                <div>
                  <Label>上传时间</Label>
                  <Input value={selectedFile.uploadedAt} readOnly />
                </div>
                <div>
                  <Label>数据源</Label>
                  <Input
                    value={
                      selectedFile.source === "upload"
                        ? "上传文件"
                        : "数据集文件"
                    }
                    readOnly
                  />
                </div>
                {selectedFile.datasetId && (
                  <div>
                    <Label>数据集ID</Label>
                    <Input value={selectedFile.datasetId} readOnly />
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="processing" className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>文件上传完成</span>
                  <span className="text-gray-500 ml-auto">
                    2024-01-22 10:30
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>文本提取完成</span>
                  <span className="text-gray-500 ml-auto">
                    2024-01-22 10:32
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>切片算子处理完成</span>
                  <span className="text-gray-500 ml-auto">
                    2024-01-22 10:35
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>文档分块完成</span>
                  <span className="text-gray-500 ml-auto">
                    2024-01-22 10:35
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  {selectedFile.vectorizationStatus === "completed" ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : selectedFile.vectorizationStatus === "processing" ? (
                    <Clock className="w-4 h-4 text-blue-500" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-gray-400" />
                  )}
                  <span>
                    向量化处理
                    {selectedFile.vectorizationStatus === "completed"
                      ? "完成"
                      : selectedFile.vectorizationStatus === "processing"
                      ? "中"
                      : "待开始"}
                  </span>
                  <span className="text-gray-500 ml-auto">
                    {selectedFile.vectorizationStatus === "completed"
                      ? "2024-01-22 10:38"
                      : "-"}
                  </span>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Slice Trace Dialog */}
      {showSliceTraceDialog && (
        <Dialog
          open={!!showSliceTraceDialog}
          onOpenChange={() => setShowSliceTraceDialog(null)}
        >
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>知识切片回溯</DialogTitle>
              <DialogDescription>
                查看分块 {showSliceTraceDialog} 的切片处理历史和算子应用过程
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-3">切片处理流程</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      1
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">原始文档导入</p>
                      <p className="text-sm text-gray-600">
                        文档: {selectedFile.name}
                      </p>
                    </div>
                    <Badge variant="outline">完成</Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      2
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">语义分割算子</p>
                      <p className="text-sm text-gray-600">
                        基于语义相似度智能分割，阈值: 0.7
                      </p>
                    </div>
                    <Badge variant="outline">完成</Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      3
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">段落分割算子</p>
                      <p className="text-sm text-gray-600">
                        按段落边界进一步细分
                      </p>
                    </div>
                    <Badge variant="outline">完成</Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      4
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">向量化处理</p>
                      <p className="text-sm text-gray-600">
                        使用 {selectedKB?.config.embeddingModel} 生成向量
                      </p>
                    </div>
                    <Badge
                      variant={
                        selectedFile.vectorizationStatus === "completed"
                          ? "outline"
                          : "secondary"
                      }
                    >
                      {selectedFile.vectorizationStatus === "completed"
                        ? "完成"
                        : "处理中"}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4">
                  <h4 className="font-medium mb-2">分块信息</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">分块ID:</span>
                      <span>{showSliceTraceDialog}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">父分块:</span>
                      <span>
                        {mockChunks.find((c) => c.id === showSliceTraceDialog)
                          ?.parentChunkId || "无"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Token数:</span>
                      <span>
                        {
                          mockChunks.find((c) => c.id === showSliceTraceDialog)
                            ?.tokens
                        }
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">创建时间:</span>
                      <span>
                        {
                          mockChunks.find((c) => c.id === showSliceTraceDialog)
                            ?.createdAt
                        }
                      </span>
                    </div>
                  </div>
                </Card>

                <Card className="p-4">
                  <h4 className="font-medium mb-2">向量信息</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">向量ID:</span>
                      <span className="font-mono text-xs">
                        {
                          mockChunks.find((c) => c.id === showSliceTraceDialog)
                            ?.vectorId
                        }
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">向量维度:</span>
                      <span>{selectedKB?.config.vectorDimension}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">相似度:</span>
                      <span>
                        {
                          mockChunks.find((c) => c.id === showSliceTraceDialog)
                            ?.similarity
                        }
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {chunkDetailModal && (
        <Dialog
          open={!!chunkDetailModal}
          onOpenChange={() => setChunkDetailModal(null)}
        >
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>分块详细信息 - 分块 {chunkDetailModal}</DialogTitle>
              <DialogDescription>
                查看分块的完整内容、元数据和关联信息
              </DialogDescription>
            </DialogHeader>

            <Tabs defaultValue="content">
              <TabsList>
                <TabsTrigger value="content">内容详情</TabsTrigger>
                <TabsTrigger value="metadata">元数据</TabsTrigger>
                <TabsTrigger value="qa">Q&A对</TabsTrigger>
                <TabsTrigger value="trace">切片回溯</TabsTrigger>
              </TabsList>

              <TabsContent value="content" className="space-y-4">
                <div>
                  <Label>分块内容</Label>
                  <Textarea
                    value={
                      mockChunks.find((c) => c.id === chunkDetailModal)
                        ?.content || ""
                    }
                    rows={8}
                    readOnly
                    className="mt-2"
                  />
                </div>
              </TabsContent>

              <TabsContent value="metadata" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>位置</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.position || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>Token数量</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.tokens || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>相似度</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.similarity || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>向量维度</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.embedding?.length || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>创建时间</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.createdAt || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>更新时间</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.updatedAt || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>向量ID</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.vectorId || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <Label>切片算子</Label>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.sliceOperator || ""
                      }
                      readOnly
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="qa" className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>关联的问答对</Label>
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-1" />
                    添加Q&A
                  </Button>
                </div>
                <div className="space-y-3">
                  {mockQAPairs.map((qa) => (
                    <Card key={qa.id} className="p-4">
                      <div className="space-y-2">
                        <div>
                          <Label className="text-sm font-medium text-blue-600">
                            问题 {qa.id}
                          </Label>
                          <p className="text-sm mt-1">{qa.question}</p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium text-green-600">
                            答案
                          </Label>
                          <p className="text-sm mt-1">{qa.answer}</p>
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm">
                            <Edit className="w-3 h-3 mr-1" />
                            编辑
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            删除
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="trace" className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <div className="flex-1">
                      <p className="font-medium">原始文档</p>
                      <p className="text-sm text-gray-600">
                        {selectedFile.name}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                    <Scissors className="w-5 h-5 text-green-600" />
                    <div className="flex-1">
                      <p className="font-medium">切片算子处理</p>
                      <p className="text-sm text-gray-600">
                        应用算子:{" "}
                        {
                          sliceOperators.find(
                            (op) =>
                              op.id ===
                              mockChunks.find((c) => c.id === chunkDetailModal)
                                ?.sliceOperator
                          )?.name
                        }
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                    <Vector className="w-5 h-5 text-purple-600" />
                    <div className="flex-1">
                      <p className="font-medium">向量化处理</p>
                      <p className="text-sm text-gray-600">
                        生成 {selectedKB?.config.vectorDimension} 维向量
                      </p>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default KnowledgeFileDetailPage;
