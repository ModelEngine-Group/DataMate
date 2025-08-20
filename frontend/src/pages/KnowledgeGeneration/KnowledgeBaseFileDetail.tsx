import React, { useState } from "react";
import {
  Plus,
  Eye,
  Edit,
  ChevronRight,
  File,
  CheckCircle,
  Clock,
  AlertCircle,
  Trash2,
  History,
  Scissors,
  VideoIcon as Vector,
  Server,
  FileText,
} from "lucide-react";
import { Card, Button, Badge, Progress, Input, Tabs, Modal } from "antd";
import {
  mockChunks,
  mockQAPairs,
  sliceOperators,
  vectorDatabases,
} from "@/mock/knowledgeBase";
import type { KnowledgeBase, KBFile } from "@/types/knowledge-base";
import { useNavigate } from "react-router";

// 状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    ready: "就绪",
    processing: "处理中",
    vectorizing: "向量化中",
    importing: "导入中",
    error: "错误",
    disabled: "已禁用",
    completed: "已完成",
  };
  return labels[status] || status;
};

const KnowledgeBaseFileDetail: React.FC = () => {
  const navigate = useNavigate();
  // 假设通过 props 或路由参数获取 selectedFile/selectedKB
  const [selectedFile] = useState<KBFile>(
    mockChunks.length
      ? {
          id: 1,
          name: "API文档.pdf",
          type: "pdf",
          size: "2.5 MB",
          status: "completed",
          chunkCount: mockChunks.length,
          progress: 100,
          uploadedAt: "2024-01-22 10:30",
          source: "upload",
          vectorizationStatus: "completed",
        }
      : ({} as KBFile)
  );
  const [selectedKB] = useState<KnowledgeBase>({
    id: 1,
    name: "API知识库",
    description: "",
    type: "unstructured",
    status: "ready",
    fileCount: 1,
    chunkCount: mockChunks.length,
    vectorCount: mockChunks.length,
    size: "2.5 MB",
    progress: 100,
    createdAt: "2024-01-22",
    lastUpdated: "2024-01-22",
    vectorDatabase: "pinecone",
    config: {
      embeddingModel: "text-embedding-3-large",
      chunkSize: 512,
      overlap: 50,
      sliceMethod: "semantic",
      enableQA: true,
      vectorDimension: 1536,
      sliceOperators: ["semantic-split", "paragraph-split"],
    },
    files: [],
    vectorizationHistory: [],
  });

  const [currentChunkPage, setCurrentChunkPage] = useState(1);
  const chunksPerPage = 5;
  const totalPages = Math.ceil(mockChunks.length / chunksPerPage);
  const startIndex = (currentChunkPage - 1) * chunksPerPage;
  const currentChunks = mockChunks.slice(
    startIndex,
    startIndex + chunksPerPage
  );

  const [editingChunk, setEditingChunk] = useState<number | null>(null);
  const [editChunkContent, setEditChunkContent] = useState("");
  const [chunkDetailModal, setChunkDetailModal] = useState<number | null>(null);
  const [showSliceTraceDialog, setShowSliceTraceDialog] = useState<
    number | null
  >(null);

  const handleEditChunk = (chunkId: number, content: string) => {
    setEditingChunk(chunkId);
    setEditChunkContent(content);
  };

  const handleSaveChunk = (chunkId: number) => {
    // 实际保存逻辑
    setEditingChunk(null);
    setEditChunkContent("");
  };

  const handleDeleteChunk = (chunkId: number) => {
    // 实际删除逻辑
    setEditingChunk(null);
    setEditChunkContent("");
  };

  const handleViewChunkDetail = (chunkId: number) => {
    setChunkDetailModal(chunkId);
  };

  const renderChunks = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          共 {mockChunks.length} 个分块，第 {startIndex + 1}-
          {Math.min(startIndex + chunksPerPage, mockChunks.length)} 个
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="small"
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
            size="small"
            onClick={() =>
              setCurrentChunkPage(Math.min(totalPages, currentChunkPage + 1))
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
                  <Badge>分块 {chunk.id}</Badge>
                  <Badge className="text-xs">
                    {sliceOperators.find((op) => op.id === chunk.sliceOperator)
                      ?.name || chunk.sliceOperator}
                  </Badge>
                  {chunk.vectorId && (
                    <Badge className="text-xs">
                      <Vector className="w-3 h-3 mr-1" />
                      已向量化
                    </Badge>
                  )}
                </div>
                <div className="text-sm leading-relaxed text-gray-700">
                  {editingChunk === chunk.id ? (
                    <Input.TextArea
                      value={editChunkContent}
                      onChange={(e) => setEditChunkContent(e.target.value)}
                      rows={3}
                    />
                  ) : (
                    chunk.content
                  )}
                </div>
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
                      size="small"
                      onClick={() => handleSaveChunk(chunk.id)}
                    >
                      保存
                    </Button>
                    <Button
                      size="small"
                      onClick={() => {
                        setEditingChunk(null);
                        setEditChunkContent("");
                      }}
                    >
                      取消
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      size="small"
                      onClick={() => handleViewChunkDetail(chunk.id)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      size="small"
                      onClick={() => handleEditChunk(chunk.id, chunk.content)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="small"
                      danger
                      onClick={() => handleDeleteChunk(chunk.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderVectors = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Vector className="w-5 h-5 text-purple-600" />
            <h4 className="font-medium">向量化状态</h4>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">状态:</span>
              <Badge>
                {getStatusLabel(selectedFile.vectorizationStatus || "pending")}
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
              <span className="font-medium">{selectedFile.chunkCount}</span>
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
          <Progress percent={selectedFile.progress} showInfo={false} />
        </div>
      )}
    </div>
  );

  const renderMetaData = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="font-medium mb-1">文件类型</div>
          <Input value={selectedFile.type} readOnly />
        </div>
        <div>
          <div className="font-medium mb-1">文件大小</div>
          <Input value={selectedFile.size} readOnly />
        </div>
        <div>
          <div className="font-medium mb-1">分块数量</div>
          <Input value={selectedFile.chunkCount} readOnly />
        </div>
        <div>
          <div className="font-medium mb-1">上传时间</div>
          <Input value={selectedFile.uploadedAt} readOnly />
        </div>
        <div>
          <div className="font-medium mb-1">数据源</div>
          <Input
            value={selectedFile.source === "upload" ? "上传文件" : "数据集文件"}
            readOnly
          />
        </div>
        {selectedFile.datasetId && (
          <div>
            <div className="font-medium mb-1">数据集ID</div>
            <Input value={selectedFile.datasetId} readOnly />
          </div>
        )}
      </div>
    </div>
  );

  const renderProcessLogs = () => (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm">
        <CheckCircle className="w-4 h-4 text-green-500" />
        <span>文件上传完成</span>
        <span className="text-gray-500 ml-auto">2024-01-22 10:30</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <CheckCircle className="w-4 h-4 text-green-500" />
        <span>文本提取完成</span>
        <span className="text-gray-500 ml-auto">2024-01-22 10:32</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <CheckCircle className="w-4 h-4 text-green-500" />
        <span>切片算子处理完成</span>
        <span className="text-gray-500 ml-auto">2024-01-22 10:35</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <CheckCircle className="w-4 h-4 text-green-500" />
        <span>文档分块完成</span>
        <span className="text-gray-500 ml-auto">2024-01-22 10:35</span>
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
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <button
          onClick={() => navigate("/data/knowledge-generation")}
          className="hover:text-blue-600"
        >
          知识库
        </button>
        <ChevronRight className="w-4 h-4" />
        <button
          onClick={() => navigate("/data/knowledge-generation/detail/1")}
          className="hover:text-blue-600"
        >
          {selectedKB?.name}
        </button>
        <ChevronRight className="w-4 h-4" />
        <span>{selectedFile.name}</span>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <File className="w-5 h-5" />
          {selectedFile.name}
          {selectedFile.size} • {selectedFile.chunkCount} 个分块 •{" "}
          {getStatusLabel(selectedFile.status)}
          {selectedFile.source === "dataset" && (
            <Badge>数据集: {selectedFile.datasetId}</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowSliceTraceDialog(selectedFile.id)}>
            <History className="w-4 h-4 mr-1" />
            切片回溯
          </Button>
          {selectedFile.vectorizationStatus !== "completed" && (
            <Button onClick={() => {}}>
              <Vector className="w-4 h-4 mr-1" />
              开始向量化
            </Button>
          )}
        </div>
      </div>
      <Card
        tabList={[
          {
            key: "chunks",
            label: "分块内容",
            children: renderChunks(),
          },
          {
            key: "vectors",
            label: "向量信息",
            children: renderVectors(),
          },
          {
            key: "metadata",
            label: "元数据",
            children: renderMetaData(),
          },
          {
            key: "processing",
            label: "处理日志",
            children: renderProcessLogs(),
          },
        ]}
        defaultActiveTabKey="chunks"
      ></Card>

      {/* Slice Trace Modal */}
      <Modal
        open={!!showSliceTraceDialog}
        onCancel={() => setShowSliceTraceDialog(null)}
        footer={null}
        title="知识切片回溯"
        width={800}
        destroyOnClose
      >
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
                <Badge>完成</Badge>
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
                <Badge>完成</Badge>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </div>
                <div className="flex-1">
                  <p className="font-medium">段落分割算子</p>
                  <p className="text-sm text-gray-600">按段落边界进一步细分</p>
                </div>
                <Badge>完成</Badge>
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
                <Badge>
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
      </Modal>

      {/* Chunk Detail Modal */}
      <Modal
        open={!!chunkDetailModal}
        onCancel={() => setChunkDetailModal(null)}
        footer={null}
        title={`分块详细信息 - 分块 ${chunkDetailModal}`}
        width={900}
        destroyOnClose
      >
        <Tabs
          defaultActiveKey="content"
          items={[
            {
              key: "content",
              label: "内容详情",
              children: (
                <div>
                  <div className="font-medium mb-1">分块内容</div>
                  <Input.TextArea
                    value={
                      mockChunks.find((c) => c.id === chunkDetailModal)
                        ?.content || ""
                    }
                    rows={8}
                    readOnly
                    className="mt-2"
                  />
                </div>
              ),
            },
            {
              key: "metadata",
              label: "元数据",
              children: (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="font-medium mb-1">位置</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.position || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">Token数量</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.tokens || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">相似度</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.similarity || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">向量维度</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.embedding?.length || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">创建时间</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.createdAt || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">更新时间</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.updatedAt || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">向量ID</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.vectorId || ""
                      }
                      readOnly
                    />
                  </div>
                  <div>
                    <div className="font-medium mb-1">切片算子</div>
                    <Input
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.sliceOperator || ""
                      }
                      readOnly
                    />
                  </div>
                </div>
              ),
            },
            {
              key: "qa",
              label: "Q&A对",
              children: (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">关联的问答对</span>
                    <Button size="small">
                      <Plus className="w-4 h-4 mr-1" />
                      添加Q&A
                    </Button>
                  </div>
                  {mockQAPairs.map((qa) => (
                    <Card key={qa.id} className="p-4">
                      <div className="space-y-2">
                        <div>
                          <span className="text-sm font-medium text-blue-600">
                            问题 {qa.id}
                          </span>
                          <p className="text-sm mt-1">{qa.question}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-green-600">
                            答案
                          </span>
                          <p className="text-sm mt-1">{qa.answer}</p>
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button type="text" size="small">
                            <Edit className="w-3 h-3 mr-1" />
                            编辑
                          </Button>
                          <Button type="text" size="small" danger>
                            <Trash2 className="w-3 h-3 mr-1" />
                            删除
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ),
            },
            {
              key: "trace",
              label: "切片回溯",
              children: (
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
              ),
            },
          ]}
        />
      </Modal>
    </div>
  );
};

export default KnowledgeBaseFileDetail;
