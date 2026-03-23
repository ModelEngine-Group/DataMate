import React, { useEffect, useState, useCallback } from "react";
import {Eye, Edit, Trash2, FileBox, ChevronLeft, ChevronRight, Code, CheckCircle, AlertCircle, Wand2, X} from "lucide-react";
import { Card, Button, Badge, Input, Tabs, Modal, Breadcrumb, Tag, Spin, Empty, Alert, message, Tooltip, Select } from "antd";
import { ExclamationCircleOutlined } from "@ant-design/icons";
import { queryKnowledgeBaseFileDetailUsingGet, updateKnowledgeBaseChunk, deleteKnowledgeBaseChunk } from "@/pages/KnowledgeBase/knowledge-base.api";
import { Link, useParams } from "react-router";
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
  const [metadataValid, setMetadataValid] = useState(true);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [chunkDetailModal, setChunkDetailModal] = useState<string | null>(null);
  const [showSliceTraceDialog, setShowSliceTraceDialog] = useState<string | null>(null);
  const [deleteConfirmModal, setDeleteConfirmModal] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const pageSize = 10;
  const [currentPage, setCurrentPage] = useState(1);

  const [idOperator, setIdOperator] = useState<string>("");
  const [idValue, setIdValue] = useState<string>("");
  const [textKeyword, setTextKeyword] = useState<string>("");

  const buildFilterExpr = useCallback((op: string, val: string, keyword: string): string => {
    const parts: string[] = [];
    if (op && val) {
      parts.push(`id ${op} "${val}"`);
    }
    if (keyword) {
      parts.push(`text like "%${keyword}%"`);
    }
    return parts.join(" && ");
  }, []);

  const handleClearFilter = useCallback(() => {
    setIdOperator("");
    setIdValue("");
    setTextKeyword("");
    setCurrentPage(1);
  }, []);

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
      const expr = buildFilterExpr(idOperator, idValue, textKeyword);
      const res = await queryKnowledgeBaseFileDetailUsingGet(knowledgeBaseId, ragFileId, { page, size: pageSize, expr: expr || undefined });
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
  }, [knowledgeBaseId, ragFileId, currentPage, idOperator, idValue, textKeyword, t]);

  const totalElements = paged?.totalElements ?? 0;
  const totalPages = paged?.totalPages ?? 0;
  const currentChunks = paged?.content ?? [];

  const handleEditChunk = (chunkId: string, content: string, metadata: unknown) => {
    setEditingChunk(chunkId);
    setEditChunkContent(content);
    setEditChunkMetadata(JSON.stringify(metadata ?? {}, null, 2));
    setMetadataValid(true);
    setMetadataError(null);
  };

  const validateJson = useCallback((value: string): { valid: boolean; error: string | null } => {
    if (!value || value.trim() === "") {
      return { valid: true, error: null };
    }
    try {
      JSON.parse(value);
      return { valid: true, error: null };
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : t("knowledgeBase.fileDetail.messages.invalidMetadataFormat");
      return { valid: false, error: errorMessage };
    }
  }, [t]);

  const handleMetadataChange = useCallback((value: string) => {
    setEditChunkMetadata(value);
    const { valid, error } = validateJson(value);
    setMetadataValid(valid);
    setMetadataError(error);
  }, [validateJson]);

  const formatJson = useCallback(() => {
    try {
      const parsed = JSON.parse(editChunkMetadata || "{}");
      const formatted = JSON.stringify(parsed, null, 2);
      setEditChunkMetadata(formatted);
      setMetadataValid(true);
      setMetadataError(null);
      message.success(t("knowledgeBase.fileDetail.messages.formatSuccess"));
    } catch {
      message.error(t("knowledgeBase.fileDetail.messages.invalidMetadataFormat"));
    }
  }, [editChunkMetadata, t]);

  const handleSaveChunk = async (chunkId: string) => {
    if (!knowledgeBaseId) return;

    if (!editChunkContent.trim()) {
      message.error(t("knowledgeBase.fileDetail.messages.textRequired"));
      return;
    }

    if (!metadataValid) {
      message.error(t("knowledgeBase.fileDetail.messages.invalidMetadata"));
      return;
    }

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
      setMetadataValid(true);
      setMetadataError(null);
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
                <span className="text-slate-400 text-xs mr-1">ID</span><span className="font-mono text-sm">{chunk.id}</span>
                {chunk.metadata?.sliceOperator && (
                  <Tag className="text-xs">
                    {chunk.metadata.sliceOperator}
                  </Tag>
                )}
              </div>
            }
            extra={
              <div className="flex items-center gap-1">
                <Tooltip title={t("knowledgeBase.fileDetail.actions.view")}>
                  <Button size="small" type="text" onClick={() => handleViewChunkDetail(chunk.id)}>
                    <Eye className="w-4 h-4" />
                  </Button>
                </Tooltip>
                <Tooltip title={t("knowledgeBase.fileDetail.actions.edit")}>
                  <Button size="small" type="text" onClick={() => handleEditChunk(chunk.id, chunk.text, chunk.metadata)}>
                    <Edit className="w-4 h-4" />
                  </Button>
                </Tooltip>
                <Tooltip title={t("knowledgeBase.fileDetail.actions.delete")}>
                  <Button size="small" type="text" danger onClick={() => setDeleteConfirmModal(chunk.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </Tooltip>
              </div>
            }
            style={{ wordBreak: "break-all" }}
          >
            <div style={{ marginBottom: 8, fontWeight: 500 }}>
              {chunk.text}
            </div>
            <div style={{ fontSize: 12, color: '#888' }}>
              metadata
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0, marginTop: 4 }}>
                {typeof chunk.metadata === "string" ? chunk.metadata : JSON.stringify(chunk.metadata ?? {}, null, 2)}
              </pre>
            </div>
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
          { title: fileName || t("knowledgeBase.fileDetail.defaultFileName", { id: ragFileId }) },
        ]}
      />
      <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-slate-50 to-slate-100/50 rounded-xl border border-slate-200/60">
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center shadow-sm">
          <FileBox className="w-5 h-5 text-amber-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold text-slate-800 truncate">
            {fileName || t("knowledgeBase.fileDetail.defaultFileName", { id: ragFileId })}
          </h1>
          <p className="text-sm text-slate-500">
            {totalElements} {t("knowledgeBase.fileDetail.messages.chunkCount", { count: 0 })}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3 bg-white rounded-lg border border-slate-200/80 px-4 py-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">ID</span>
          <Select
            value={idOperator || undefined}
            onChange={setIdOperator}
            placeholder={t("knowledgeBase.fileDetail.filter.idOperator")}
            allowClear
            className="w-16"
            options={[
              { value: ">", label: ">" },
              { value: "<", label: "<" },
              { value: "==", label: "==" },
            ]}
          />
          <Input
            value={idValue}
            onChange={(e) => setIdValue(e.target.value)}
            placeholder={t("knowledgeBase.fileDetail.filter.idValue")}
            className="w-28"
          />
        </div>
        <div className="h-5 w-px bg-slate-200" />
        <Input.Search
          value={textKeyword}
          onChange={(e) => setTextKeyword(e.target.value)}
          placeholder={t("knowledgeBase.fileDetail.filter.textKeyword")}
          className="w-48"
          allowClear
        />
        <div className="flex items-center gap-2 ml-auto">
          <Button
            type="primary"
            size="small"
            onClick={() => { setCurrentPage(1); fetchChunks(1); }}
          >
            {t("knowledgeBase.fileDetail.filter.apply")}
          </Button>
          {(idOperator || idValue || textKeyword) && (
            <Button size="small" onClick={handleClearFilter}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
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
        centered
      >
        <p>{t("knowledgeBase.fileDetail.modal.deleteConfirmMessage")}</p>
      </Modal>

      <Modal
        open={!!editingChunk}
        onCancel={() => {
          setEditingChunk(null);
          setEditChunkContent("");
          setEditChunkMetadata("");
          setMetadataValid(true);
          setMetadataError(null);
        }}
        footer={null}
        title={
          <div className="flex items-center gap-2">
            <Edit className="w-5 h-5 text-blue-500" />
            <span>{t("knowledgeBase.fileDetail.modal.editChunkTitle")} - {editingChunk}</span>
          </div>
        }
        width={900}
        destroyOnClose
      >
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="font-medium text-gray-700">
                {t("knowledgeBase.fileDetail.modal.chunkContent")}
              </label>
            </div>
            <Input.TextArea
              value={editChunkContent}
              onChange={(e) => setEditChunkContent(e.target.value)}
              rows={6}
              placeholder={t("knowledgeBase.fileDetail.placeholders.chunkContent")}
              className="font-mono"
              style={{
                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
              }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="font-medium text-gray-700 flex items-center gap-2">
                <Code className="w-4 h-4" />
                {t("knowledgeBase.fileDetail.modal.metadata")}
              </label>
              <div className="flex items-center gap-2">
                {metadataValid ? (
                  <span className="flex items-center gap-1 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    {t("knowledgeBase.fileDetail.messages.jsonValid")}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-500 text-sm">
                    <AlertCircle className="w-4 h-4" />
                    {t("knowledgeBase.fileDetail.messages.jsonInvalid")}
                  </span>
                )}
                <Button
                  size="small"
                  icon={<Wand2 className="w-4 h-4" />}
                  onClick={formatJson}
                  type="default"
                >
                  {t("knowledgeBase.fileDetail.actions.formatJson")}
                </Button>
              </div>
            </div>
            <div className="relative">
              <Input.TextArea
                value={editChunkMetadata}
                onChange={(e) => handleMetadataChange(e.target.value)}
                rows={10}
                placeholder={t("knowledgeBase.fileDetail.placeholders.metadata")}
                className="font-mono"
                style={{
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                  borderColor: metadataValid ? '#d9d9d9' : '#ff4d4f',
                }}
                status={metadataValid ? undefined : 'error'}
              />
              {metadataError && (
                <div className="mt-2 text-red-500 text-xs flex items-start gap-1">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span className="break-all">{metadataError}</span>
                </div>
              )}
              <div className="mt-2 text-gray-400 text-xs">
                {t("knowledgeBase.fileDetail.messages.metadataHint")}
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-gray-100">
            <Button
              onClick={() => {
                setEditingChunk(null);
                setEditChunkContent("");
                setEditChunkMetadata("");
                setMetadataValid(true);
                setMetadataError(null);
              }}
            >
              {t("knowledgeBase.fileDetail.actions.cancel")}
            </Button>
            <Button
              type="primary"
              onClick={() => editingChunk && handleSaveChunk(editingChunk)}
              loading={saving}
              disabled={!metadataValid || !editChunkContent.trim()}
              icon={<CheckCircle className="w-4 h-4" />}
            >
              {t("knowledgeBase.fileDetail.actions.save")}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default KnowledgeBaseFileDetail;
