import React, { useEffect, useState } from "react";
import {Eye, Edit, Trash2, FileBox, ChevronLeft, ChevronRight} from "lucide-react";
import { Card, Button, Badge, Input, Tabs, Modal, Breadcrumb, Tag, Spin, Empty, Alert, message } from "antd";
import { queryKnowledgeBaseFileDetailUsingGet, updateKnowledgeBaseChunk, deleteKnowledgeBaseChunk } from "@/pages/KnowledgeBase/knowledge-base.api";
import { Link, useParams } from "react-router";
import DetailHeader from "@/components/DetailHeader";
import { useTranslation } from "react-i18next";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface RagChunk {
  id: string;
  text: string;
  metadata: unknown;
}

const { TextArea } = Input;

const KnowledgeBaseFileDetail: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams();
  const search = new URLSearchParams(window.location.search);
  const knowledgeBaseId = search.get("knowledgeBaseId") || "";
  const fileName = search.get("fileName") || "";
  const ragFileId = id || "";
  const kbLink = knowledgeBaseId ? `/data/knowledge-base/detail/${knowledgeBaseId}` : "/data/knowledge-base";

  const [paged, setPaged] = useState<{
    page: number;
    size: number;
    totalElements: number;
    totalPages: number;
    content: RagChunk[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [editingChunk, setEditingChunk] = useState<string | null>(null);
  const [editChunkContent, setEditChunkContent] = useState("");
  const [editChunkMetadata, setEditChunkMetadata] = useState("");
  const [chunkDetailModal, setChunkDetailModal] = useState<string | null>(null);
  const [showSliceTraceDialog, setShowSliceTraceDialog] = useState<string | null>(null);
  const [deleteConfirmModal, setDeleteConfirmModal] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const pageSize = 10;
  const [currentPage, setCurrentPage] = useState(1);

  const safeParse = (meta: unknown): unknown => {
    if (typeof meta === "string") {
      try {
        return JSON.parse(meta);
      } catch {
        return meta;
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
      const msg = typeof err === "object" && err !== null && "message" in err ? String((err as { message?: string }).message) : t("knowledgeBase.fileDetail.messages.loadFailed");
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks(currentPage);
  }, [knowledgeBaseId, ragFileId, currentPage, t]);

  const totalElements = paged?.totalElements ?? 0;
  const totalPages = paged?.totalPages ?? 0;
  const currentChunks = paged?.content ?? [];

  const handleEditChunk = (chunkId: string, content: string, metadata: unknown) => {
    setEditingChunk(chunkId);
    setEditChunkContent(content);
    setEditChunkMetadata(JSON.stringify(metadata ?? {}, null, 2));
  };

  const handleSaveChunk = async (chunkId: string) => {
    if (!knowledgeBaseId) return;
    
    let parsedMetadata = {};
    try {
      parsedMetadata = editChunkMetadata ? JSON.parse(editChunkMetadata) : {};
    } catch {
      message.error(t("knowledgeBase.fileDetail.messages.invalidMetadata"));
      return;
    }

    setSaving(true);
    try {
      await updateKnowledgeBaseChunk(knowledgeBaseId, chunkId, {
        text: editChunkContent,
        metadata: parsedMetadata,
      });
      message.success(t("knowledgeBase.fileDetail.messages.updateSuccess"));
      setEditingChunk(null);
      setEditChunkContent("");
      setEditChunkMetadata("");
      fetchChunks(currentPage);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "message" in err 
        ? String((err as { message?: string }).message) 
        : t("knowledgeBase.fileDetail.messages.updateFailed");
      message.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteChunk = async (chunkId: string) => {
    if (!knowledgeBaseId) return;

    setDeleting(true);
    try {
      await deleteKnowledgeBaseChunk(knowledgeBaseId, chunkId);
      message.success(t("knowledgeBase.fileDetail.messages.deleteSuccess"));
      setDeleteConfirmModal(null);
      fetchChunks(currentPage);
    } catch (err: unknown) {
      const msg = typeof err === "object" && err !== null && "message" in err 
        ? String((err as { message?: string }).message) 
        : t("knowledgeBase.fileDetail.messages.deleteFailed");
      message.error(msg);
    } finally {
      setDeleting(false);
    }
  };

  const handleViewChunkDetail = (chunkId: string) => {
    setChunkDetailModal(chunkId);
  };

  const renderChunks = () => (
    <div className="space-y-4">
      {error && <Alert type="error" message={error} showIcon />}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          {t("knowledgeBase.fileDetail.messages.totalChunks", { count: totalElements })}，{t("knowledgeBase.fileDetail.messages.showingRange", { start: totalElements === 0 ? 0 : (currentPage - 1) * pageSize + 1, end: totalElements === 0 ? 0 : Math.min(currentPage * pageSize, totalElements) })}
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="small"
            icon={<ChevronLeft className="w-4 h-4" />}
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
          />
          <span className="text-sm text-gray-600">
            {totalPages === 0 ? 0 : currentPage} / {totalPages}
          </span>
          <Button
            size="small"
            icon={<ChevronRight className="w-4 h-4" />}
            onClick={() => setCurrentPage(Math.min(totalPages || 1, currentPage + 1))}
            disabled={currentPage >= (totalPages || 1)}
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {currentChunks.map((chunk) => (
          <Card
            key={chunk.id}
            title={
              <div className="flex items-center gap-2">
                <span>{t("knowledgeBase.fileDetail.messages.chunkLabel")} {chunk.id}</span>
                {chunk.metadata?.sliceOperator && (
                  <Tag className="text-xs">
                    {chunk.metadata.sliceOperator}
                  </Tag>
                )}
              </div>
            }
            extra={
              <div className="flex items-center gap-1">
                {editingChunk === chunk.id ? (
                  <>
                    <Button
                      type="primary"
                      size="small"
                      onClick={() => handleSaveChunk(chunk.id)}
                      loading={saving}
                    >
                      {t("knowledgeBase.fileDetail.actions.save")}
                    </Button>
                    <Button
                      size="small"
                      onClick={() => {
                        setEditingChunk(null);
                        setEditChunkContent("");
                        setEditChunkMetadata("");
                      }}
                    >
                      {t("knowledgeBase.fileDetail.actions.cancel")}
                    </Button>
                  </>
                ) : (
                  <>
                    <Button size="small" type="text" onClick={() => handleViewChunkDetail(chunk.id)}>
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button size="small" type="text" onClick={() => handleEditChunk(chunk.id, chunk.text, chunk.metadata)}>
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button size="small" type="text" danger onClick={() => setDeleteConfirmModal(chunk.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </>
                )}
              </div>
            }
            style={{ wordBreak: "break-all" }}
          >
            <div style={{ marginBottom: 8, fontWeight: 500 }}>
              {editingChunk === chunk.id ? (
                <>
                  <TextArea
                    value={editChunkContent}
                    onChange={(e) => setEditChunkContent(e.target.value)}
                    rows={3}
                    placeholder={t("knowledgeBase.fileDetail.placeholders.chunkContent")}
                  />
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>metadata</div>
                    <TextArea
                      value={editChunkMetadata}
                      onChange={(e) => setEditChunkMetadata(e.target.value)}
                      rows={4}
                      placeholder={t("knowledgeBase.fileDetail.placeholders.metadata")}
                    />
                  </div>
                </>
              ) : (
                chunk.text
              )}
            </div>
            {editingChunk !== chunk.id && (
              <div style={{ fontSize: 12, color: '#888' }}>
                metadata <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>{typeof chunk.metadata === "string" ? chunk.metadata : JSON.stringify(chunk.metadata ?? {}, null, 2)}</pre>
              </div>
            )}
          </Card>
        ))}
        {!loading && currentChunks.length === 0 && (
          <div className="col-span-2">
            <Empty description={t("knowledgeBase.fileDetail.messages.noChunks")} />
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      <Breadcrumb
        items={[
          { title: <Link to="/data/knowledge-base">{t("knowledgeBase.fileDetail.breadcrumb.kbList")}</Link> },
          { title: (<Link to={kbLink}>{t("knowledgeBase.fileDetail.breadcrumb.kbDetail")}</Link>) },
          { title: fileName || `文件 ${ragFileId}` },
        ]}
      />
      <DetailHeader
        data={{
          id: ragFileId,
          icon: <FileBox className="w-full h-full" />,
          iconColor: "#a27e7e",
          name: fileName || `文件 ${ragFileId}`,
          description: `${totalElements} ${t("knowledgeBase.fileDetail.messages.chunkCount", { count: 0 })}`,
          createdAt: "",
          lastUpdated: "",
        }}
        statistics={[]}
        operations={[]}
      />
      <Card>
        {loading ? <div className="flex items-center justify-center py-8"><Spin /></div> : renderChunks()}
      </Card>

      <Modal
        open={!!showSliceTraceDialog}
        onCancel={() => setShowSliceTraceDialog(null)}
        footer={null}
        title={t("knowledgeBase.fileDetail.modal.sliceTraceTitle")}
        width={800}
        destroyOnClose
      >
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium mb-3">{t("knowledgeBase.fileDetail.modal.sliceProcessTitle")}</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  1
                </div>
                <div className="flex-1">
                  <p className="font-medium">{t("knowledgeBase.fileDetail.modal.originalDocImport")}</p>
                  <p className="text-sm text-gray-600">{t("knowledgeBase.fileDetail.modal.fileLabel")}: {ragFileId}</p>
                </div>
                <Badge>{t("knowledgeBase.fileDetail.modal.completed")}</Badge>
              </div>
            </div>
          </div>
        </div>
      </Modal>

      <Modal
        open={!!chunkDetailModal}
        onCancel={() => setChunkDetailModal(null)}
        footer={null}
        title={`${t("knowledgeBase.fileDetail.modal.chunkDetailTitle")} ${chunkDetailModal ?? ""}`}
        width={900}
        destroyOnClose
      >
        <Tabs
          defaultActiveKey="content"
          items={[
            {
              key: "content",
              label: t("knowledgeBase.fileDetail.modal.contentDetail"),
              children: (
                <div>
                  <div className="font-medium mb-1">{t("knowledgeBase.fileDetail.modal.chunkContent")}</div>
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
              label: t("knowledgeBase.fileDetail.modal.metadata"),
              children: (
                <div>
                  <SyntaxHighlighter
                    language="json"
                    style={vscDarkPlus}
                    showLineNumbers
                    customStyle={{
                      margin: 0,
                      borderRadius: "0.5rem",
                      fontSize: "0.875rem",
                      maxHeight: "400px",
                      overflow: "auto",
                    }}
                  >
                    {JSON.stringify(
                      currentChunks.find((c) => c.id === chunkDetailModal)?.metadata || {},
                      null,
                      2
                    ) || "{}"}
                  </SyntaxHighlighter>
                </div>
              ),
            },
          ]}
        />
      </Modal>

      <Modal
        open={!!deleteConfirmModal}
        onCancel={() => setDeleteConfirmModal(null)}
        onOk={() => handleDeleteChunk(deleteConfirmModal!)}
        title={t("knowledgeBase.fileDetail.modal.deleteConfirmTitle")}
        okText={t("knowledgeBase.fileDetail.actions.confirm")}
        cancelText={t("knowledgeBase.fileDetail.actions.cancel")}
        okButtonProps={{ danger: true, loading: deleting }}
      >
        <p>{t("knowledgeBase.fileDetail.modal.deleteConfirmMessage")}</p>
      </Modal>
    </div>
  );
};

export default KnowledgeBaseFileDetail;
