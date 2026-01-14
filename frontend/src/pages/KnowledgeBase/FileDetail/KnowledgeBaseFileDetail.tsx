import React, { useEffect, useState } from "react";
import {Eye, Edit, Trash2, FileText, Download, FileType2, FileBox} from "lucide-react";
import { Card, Button, Badge, Input, Tabs, Modal, Breadcrumb, Tag, Spin, Empty, Alert } from "antd";
import { queryKnowledgeBaseFileDetailUsingGet } from "@/pages/KnowledgeBase/knowledge-base.api";
import { Link, useParams } from "react-router";
import DetailHeader from "@/components/DetailHeader";

interface RagChunk {
  id: string;
  text: string;
  metadata: unknown; // may be string or object
}

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

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    ready: "green",
    processing: "blue",
    vectorizing: "purple",
    importing: "orange",
    error: "blue",
    disabled: "gray",
    completed: "green",
  };
  return colors[status] || "default";
};

const KnowledgeBaseFileDetail: React.FC = () => {
  const { id } = useParams();
  // id 为路由中的 ragFileId，knowledgeBaseId 通过上一级 detail 路由或 query 传入
  const search = new URLSearchParams(window.location.search);
  const knowledgeBaseId = search.get("knowledgeBaseId") || "";
  const fileName = search.get("fileName") || "";
  const ragFileId = id || "";
  const kbLink = knowledgeBaseId ? `/data/knowledge-base/detail/${knowledgeBaseId}` : "/data/knowledge-base";

  // 远程数据状态
  const [paged, setPaged] = useState<{
    page: number;
    size: number;
    totalElements: number;
    totalPages: number;
    content: RagChunk[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 本地 UI 状态
  const [editingChunk, setEditingChunk] = useState<string | null>(null);
  const [editChunkContent, setEditChunkContent] = useState("");
  const [chunkDetailModal, setChunkDetailModal] = useState<string | null>(null);
  const [showSliceTraceDialog, setShowSliceTraceDialog] = useState<string | null>(null);

  const pageSize = 20;
  const [currentPage, setCurrentPage] = useState(1);

  const safeParse = (meta: unknown): unknown => {
    if (typeof meta === "string") {
      try {
        return JSON.parse(meta);
      } catch {
        return meta; // 保持原样
      }
    }
    return meta;
  };

  const fetchChunks = async (page: number) => {
    if (!knowledgeBaseId || !ragFileId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await queryKnowledgeBaseFileDetailUsingGet(knowledgeBaseId, ragFileId, { page, size: pageSize });
      // 兼容返回结构 ResponsePagedResponseRagChunk -> { code, message, data }
      const raw = (res?.data ?? res) as {
        page: number;
        size: number;
        totalElements: number;
        totalPages: number;
        content: RagChunk[];
      };
      const normalized = {
        ...raw,
        content: (raw?.content ?? []).map((c) => ({
          ...c,
          metadata: safeParse((c as RagChunk)?.metadata),
        })),
      };
      setPaged(normalized);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "message" in err ? String((err as { message?: string }).message) : "加载失败";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks(currentPage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [knowledgeBaseId, ragFileId, currentPage]);

  const totalElements = paged?.totalElements ?? 0;
  const totalPages = paged?.totalPages ?? 0;
  const currentChunks = paged?.content ?? [];

  const handleEditChunk = (chunkId: string, content: string) => {
    setEditingChunk(chunkId);
    setEditChunkContent(content);
  };

  const handleSaveChunk = (chunkId: string) => {
    // TODO: 保存到后端（暂不实现）
    setEditingChunk(null);
    setEditChunkContent("");
  };

  const handleDeleteChunk = (chunkId: string) => {
    // TODO: 删除后端分块（暂不实现）
    setEditingChunk(null);
    setEditChunkContent("");
  };

  const handleViewChunkDetail = (chunkId: string) => {
    setChunkDetailModal(chunkId);
  };

  const renderChunks = () => (
    <div className="space-y-4">
      {error && <Alert type="error" message={error} showIcon />}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          共 {totalElements} 个分块，第 {totalElements === 0 ? 0 : (currentPage - 1) * pageSize + 1}-
          {Math.min(currentPage * pageSize, totalElements)} 个
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="small"
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
          >
            上一页
          </Button>
          <span className="text-sm text-gray-600">
            {totalPages === 0 ? 0 : currentPage} / {totalPages}
          </span>
          <Button
            size="small"
            onClick={() => setCurrentPage(Math.min(totalPages || 1, currentPage + 1))}
            disabled={currentPage >= (totalPages || 1)}
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
                  <div className="flex-1 flex items-center gap-2">
                    <h4 className="text-sm font-semibold">分块 {chunk.id}</h4>
                    {/* 算子名：从 metadata.sliceOperator 显示 */}
                    {chunk.metadata?.sliceOperator && (
                      <Tag className="text-xs">
                        {chunk.metadata.sliceOperator}
                      </Tag>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    {editingChunk === chunk.id ? (
                      <>
                        <Button
                          type="primary"
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
                        <Button size="small" onClick={() => handleViewChunkDetail(chunk.id)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button size="small" onClick={() => handleEditChunk(chunk.id, chunk.text)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button size="small" danger onClick={() => handleDeleteChunk(chunk.id)}>
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
                <div className="text-sm leading-relaxed text-gray-700">
                  {editingChunk === chunk.id ? (
                    <Input.TextArea
                      value={editChunkContent}
                      onChange={(e) => setEditChunkContent(e.target.value)}
                      rows={3}
                    />
                  ) : (
                    chunk.text
                  )}
                </div>
                {/* 元数据展示，保持和召回结果风格一致 */}
                <div className="mt-2 text-xs text-gray-600">
                  <div className="font-medium">metadata:</div>
                  <pre className="whitespace-pre-wrap break-all m-0">
                    {typeof chunk.metadata === "string"
                      ? chunk.metadata
                      : JSON.stringify(chunk.metadata ?? {}, null, 2)}
                  </pre>
                </div>
                {/* 结构化元数据的快捷标签（若可用） */}
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  {chunk?.metadata?.position && <span>位置: {chunk.metadata.position}</span>}
                  {chunk?.metadata?.tokens && <span>Token: {chunk.metadata.tokens}</span>}
                  {chunk?.metadata?.page && <span>页码: {chunk.metadata.page}</span>}
                  {chunk?.metadata?.section && <span>章节: {chunk.metadata.section}</span>}
                </div>
              </div>
            </div>
          </Card>
        ))}
        {!loading && currentChunks.length === 0 && (
          <Empty description="暂无分块数据" />
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      <Breadcrumb
        items={[
          { title: <Link to="/data/knowledge-base">知识库</Link> },
          { title: (<Link to={kbLink}>知识库详情</Link>) },
          { title: fileName || `文件 ${ragFileId}` },
        ]}
      />
      {/* 头部统计使用最简占位，后续可扩展 */}
      <DetailHeader
        data={{
          id: ragFileId,
          icon: <FileBox className="w-full h-full" />,
          iconColor: "#a27e7e",
          status: { label: "就绪", color: "default" },
          name: fileName || `文件 ${ragFileId}`,
          description: `${totalElements} 个分块`,
          createdAt: "",
          lastUpdated: "",
        }}
        statistics={[]}
        operations={[{ key: "download", label: "下载", icon: <Download className="w-4 h-4" />, onClick: () => {} }]}
      />
      <Card>
        {loading ? <div className="flex items-center justify-center py-8"><Spin /></div> : renderChunks()}
      </Card>

      {/* Slice Trace Modal */}
      <Modal
        open={!!showSliceTraceDialog}
        onCancel={() => setShowSliceTraceDialog(null)}
        footer={null}
        title="知识切片回溯"
        width={800}
        destroyOnClose
      >
        {/* 简化为内容占位，真实数据待后端提供更多字段 */}
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
                  <p className="text-sm text-gray-600">文件: {ragFileId}</p>
                </div>
                <Badge>完成</Badge>
              </div>
            </div>
          </div>
        </div>
      </Modal>

      {/* Chunk Detail Modal */}
      <Modal
        open={!!chunkDetailModal}
        onCancel={() => setChunkDetailModal(null)}
        footer={null}
        title={`分块详细信息 - 分块 ${chunkDetailModal ?? ""}`}
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
                    value={currentChunks.find((c) => c.id === chunkDetailModal)?.text || ""}
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
                    <Input value={currentChunks.find((c) => c.id === chunkDetailModal)?.metadata?.position || ""} readOnly />
                  </div>
                  <div>
                    <div className="font-medium mb-1">Token数量</div>
                    <Input value={currentChunks.find((c) => c.id === chunkDetailModal)?.metadata?.tokens || ""} readOnly />
                  </div>
                  <div>
                    <div className="font-medium mb-1">页码</div>
                    <Input value={currentChunks.find((c) => c.id === chunkDetailModal)?.metadata?.page || ""} readOnly />
                  </div>
                  <div>
                    <div className="font-medium mb-1">章节</div>
                    <Input value={currentChunks.find((c) => c.id === chunkDetailModal)?.metadata?.section || ""} readOnly />
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
