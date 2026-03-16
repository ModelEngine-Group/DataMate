import type React from "react";
import { useEffect, useState } from "react";
import { Table, Badge, Button, Breadcrumb, Tooltip, App, Card, Input, Empty, Spin, Tag, Modal } from "antd";
import { ExclamationCircleOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  DeleteOutlined,
  EditOutlined,
  ReloadOutlined,
  CloseOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router";
import DetailHeader from "@/components/DetailHeader";
import { SearchControls } from "@/components/SearchControls";
import { KBFile, KnowledgeBaseItem, KnowledgeGraphNode, KnowledgeGraphEdge, KBType } from "../knowledge-base.model";
import { getKBTypeMap, mapFileData, mapKnowledgeBase } from "../knowledge-base.const";
import {
  deleteKnowledgeBaseByIdUsingDelete,
  deleteKnowledgeBaseFileByIdUsingDelete,
  queryKnowledgeBaseByIdUsingGet,
  queryKnowledgeBaseFilesUsingGet,
  retrieveKnowledgeBaseContent,
  queryKnowledgeBase,
} from "../knowledge-base.api";
import useFetchData from "@/hooks/useFetchData";
import AddDataDialog from "../components/AddDataDialog";
import CreateKnowledgeBase from "../components/CreateKnowledgeBase";
import KnowledgeGraphView, { GraphEntitySelection } from "../components/KnowledgeGraphView";
import { useTranslation } from "react-i18next";

type HeaderStatisticItem = React.ComponentProps<typeof DetailHeader>["statistics"][number];
// Use UnifiedSearchResult from model - flat structure from backend
// Backend returns: { id, text, score, metadata, resultType, knowledgeBaseId, knowledgeBaseName }
interface RecallResult {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, any>;
  resultType?: string;
  knowledgeBaseId?: string;
  knowledgeBaseName?: string;
}

function squashSoftLineBreaksOutsideFences(markdown: string): string {
  if (!markdown) return "";
  const parts = markdown.split(/(```[\s\S]*?```)/g);
  return parts
    .map((part) => {
      if (part.startsWith("```")) return part;
      // keep paragraph breaks (\n\n), but squash single newlines into spaces
      return part.replace(/([^\n])\n(?!\n)/g, "$1 ");
    })
    .join("");
}

const KnowledgeBaseDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { id } = useParams<{ id: string }>();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseItem | undefined>(undefined);
  const [showEdit, setShowEdit] = useState(false);
  const [activeTab, setActiveTab] = useState<'fileList' | 'recallTest'>('fileList');
  const [recallLoading, setRecallLoading] = useState(false);
  const [recallResults, setRecallResults] = useState<RecallResult[]>([]);
  const [recallQuery, setRecallQuery] = useState("");
  const [graphVisible, setGraphVisible] = useState(false);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphData, setGraphData] = useState<{ nodes: KnowledgeGraphNode[]; edges: KnowledgeGraphEdge[] }>({ nodes: [], edges: [] });
  const [graphSelection, setGraphSelection] = useState<GraphEntitySelection | null>(null);

  const kbTypeMap = getKBTypeMap(t);
  const kbTypeMeta = knowledgeBase ? kbTypeMap[knowledgeBase.type as KBType] : undefined;

  const detailHeaderData = knowledgeBase
    ? {
        ...knowledgeBase,
        tags: (() => {
          const rawTags = Array.isArray((knowledgeBase as any)?.tags) ? ((knowledgeBase as any).tags as any[]) : [];
          const normalized = rawTags
            .map((tag) => {
              if (!tag) return "";
              if (typeof tag === "string") return tag;
              return String(tag.label ?? tag.name ?? "");
            })
            .map((s) => s.trim())
            .filter(Boolean);

          const typeLabel = String(kbTypeMeta?.tag?.label ?? "").trim();
          const filtered = typeLabel ? normalized.filter((label) => label !== typeLabel) : normalized;

          return Array.from(new Set(filtered));
        })(),
        description:
          knowledgeBase.description && knowledgeBase.description.trim().length > 0
            ? knowledgeBase.description
            : kbTypeMap[knowledgeBase.type as KBType]?.description ??
              kbTypeMap[knowledgeBase.type as KBType]?.label ??
              knowledgeBase.description,
      }
    : knowledgeBase;

  const fetchKnowledgeBaseDetails = async (id: string) => {
    const { data } = await queryKnowledgeBaseByIdUsingGet(id);
    setKnowledgeBase(mapKnowledgeBase(data, true, t));
  };

  useEffect(() => {
    if (id) {
      fetchKnowledgeBaseDetails(id);
    }
  }, [id, t]);

  useEffect(() => {
    fetchFiles()
  }, [t]);

  useEffect(() => {
    if (!graphVisible) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [graphVisible]);

  const {
    loading,
    tableData: files,
    searchParams,
    pagination,
    fetchData: fetchFiles,
    setSearchParams,
    handleFiltersChange,
    handleKeywordChange,
  } = useFetchData<KBFile>(
    (params) => id ? queryKnowledgeBaseFilesUsingGet(id, params) : Promise.resolve({ data: [] }),
    (file) => mapFileData(file, t),
    30000, // 30秒轮询间隔
    false, // 不自动轮询
    [], // 额外的轮询函数
    0 // pageOffset: Python 后端期望 page 从 1 开始，前端 current=1 时传 page=1
  );

  // File table logic
  const handleDeleteFile = async (file: KBFile) => {
    try {
      await deleteKnowledgeBaseFileByIdUsingDelete(knowledgeBase!.id, {
        ids: [file.id]
      });
      message.success(t("knowledgeBase.detail.messages.fileDeleted"));
      fetchFiles();
      fetchKnowledgeBaseDetails(knowledgeBase!.id);
    } catch {
      message.error(t("knowledgeBase.detail.messages.fileDeleteFailed"));
    }
  };

  const handleDeleteKB = async (kb: KnowledgeBaseItem) => {
    await deleteKnowledgeBaseByIdUsingDelete(kb.id);
    message.success(t("knowledgeBase.detail.messages.kbDeleted"));
    navigate("/data/knowledge-base");
  };

  const handleRefreshPage = () => {
    if (knowledgeBase) {
      fetchKnowledgeBaseDetails(knowledgeBase.id);
    }
    fetchFiles();
    setShowEdit(false);
  };

  const handleRecallTest = async () => {
    if (!recallQuery || !knowledgeBase?.id) return;
    setRecallLoading(true);
    try {
      const result = await retrieveKnowledgeBaseContent({
        query: recallQuery,
        topK: 10,
        threshold: 0.2,
        knowledgeBaseIds: [knowledgeBase.id],
      });
      const data = Array.isArray(result) ? result : (result as any)?.data;
      setRecallResults(Array.isArray(data) ? data : []);
    } catch {
      setRecallResults([]);
    }
    setRecallLoading(false);
  };

  const handleGraphFetch = async () => {
    if (!knowledgeBase?.id) return;
    setGraphLoading(true);
    setGraphSelection(null);
    try {
      const { data } = await queryKnowledgeBase({ knowledge_base_id: knowledgeBase.id, query: "*" });
      setGraphData({ nodes: data?.nodes ?? [], edges: data?.edges ?? [] });
    } catch {
      setGraphData({ nodes: [], edges: [] });
    }
    setGraphLoading(false);
  };

  const handleOpenGraph = () => {
    setGraphSelection(null);
    setGraphVisible(true);
    if (!graphData.nodes.length) {
      handleGraphFetch();
    }
  };

  const handleCloseGraph = () => {
    setGraphVisible(false);
    setGraphSelection(null);
  };

  const handleGraphRefresh = () => {
    handleGraphFetch();
  };

  type DetailOperation = NonNullable<React.ComponentProps<typeof DetailHeader>["operations"][number]>;
  const baseOperations: DetailOperation[] = [
    {
      key: "edit",
      label: t("knowledgeBase.detail.actions.edit"),
      icon: <EditOutlined className="w-4 h-4" />,
      onClick: () => {
        setShowEdit(true);
      },
    },
    {
      key: "refresh",
      label: t("knowledgeBase.detail.actions.refresh"),
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: () => {
        handleRefreshPage();
      },
    },
    {
      key: "delete",
      label: t("knowledgeBase.detail.actions.delete"),
      danger: true,
      confirm: {
        title: t("knowledgeBase.detail.confirm.deleteTitle"),
        description: t("knowledgeBase.detail.confirm.deleteDescription"),
        cancelText: t("knowledgeBase.detail.confirm.cancelText"),
        okText: t("knowledgeBase.detail.confirm.okText"),
        okType: "danger",
        onConfirm: () => knowledgeBase && handleDeleteKB(knowledgeBase),
      },
      icon: <DeleteOutlined className="w-4 h-4" />,
    },
  ];

  const operations: DetailOperation[] = baseOperations;

  const fileOps = [
    {
      key: "delete",
      label: t("knowledgeBase.detail.actions.deleteFile"),
      icon: <DeleteOutlined className="w-4 h-4" />,
      danger: true,
      onClick: (file: KBFile) => {
        Modal.confirm({
          title: t("knowledgeBase.detail.confirm.deleteFileTitle"),
          content: t("knowledgeBase.detail.confirm.deleteFileDescription", { name: file.name }),
          okText: t("knowledgeBase.detail.confirm.okText"),
          okType: "danger",
          cancelText: t("knowledgeBase.detail.confirm.cancelText"),
          centered: true,
          onOk: () => handleDeleteFile(file),
        });
      },
    },
  ];

  const fileColumns = [
    {
      title: t("knowledgeBase.detail.columns.fileName"),
      dataIndex: "name",
      key: "name",
      width: 200,
      ellipsis: true,
      fixed: "left" as const,
      render: (_: unknown, file: KBFile) => (
        <a
          onClick={() => {
            if (knowledgeBase?.type === KBType.GRAPH) {
              handleOpenGraph();
              return;
            }
            navigate(
              `/data/knowledge-base/file-detail/${file.id}?knowledgeBaseId=${knowledgeBase?.id || ""}&fileName=${encodeURIComponent(file.name || file.fileName || "")}`
            );
          }}
        >
          {file.name}
        </a>
      )
    },
    {
      title: t("knowledgeBase.detail.columns.status"),
      dataIndex: "status",
      key: "vectorizationStatus",
      width: 120,
      render: (status: unknown) => {
        if (typeof status === 'object' && status !== null) {
          const s = status as { color?: string; label?: string };
          return <Badge color={s.color} text={s.label} />;
        }
        return <Badge color="default" text={String(status)} />;
      },
    },
    {
      title: t("knowledgeBase.detail.columns.chunkCount"),
      dataIndex: "chunkCount",
      key: "chunkCount",
      width: 100,
      ellipsis: true,
    },
    {
      title: t("knowledgeBase.detail.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
      width: 180,
    },
    {
      title: t("knowledgeBase.detail.columns.updatedAt"),
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
      width: 180,
    },
    {
      title: t("knowledgeBase.detail.columns.actions"),
      key: "actions",
      align: "right" as const,
      width: 100,
      render: (_: unknown, file: KBFile) => (
        <div>
          {fileOps.map((op) => (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                danger={op?.danger}
                onClick={() => op.onClick(file)}
              />
            </Tooltip>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <Breadcrumb>
          <Breadcrumb.Item>
            <a onClick={() => navigate("/data/knowledge-base")}>{t("knowledgeBase.detail.breadcrumb.kbList")}</a>
          </Breadcrumb.Item>
          <Breadcrumb.Item>{knowledgeBase?.name}</Breadcrumb.Item>
        </Breadcrumb>
      </div>
      <DetailHeader
        data={detailHeaderData}
        titleExtra={
          kbTypeMeta?.tag?.label ? (
            <Tag
              className="shrink-0"
              style={{
                background: kbTypeMeta.tag.background,
                color: kbTypeMeta.tag.color,
                borderColor: kbTypeMeta.tag.background,
              }}
            >
              {kbTypeMeta.tag.label}
            </Tag>
          ) : null
        }
        statistics={knowledgeBase && Array.isArray((knowledgeBase as { statistics?: HeaderStatisticItem[] }).statistics)
          ? ((knowledgeBase as { statistics?: HeaderStatisticItem[] }).statistics ?? [])
          : []}
        operations={operations}
      />
      <CreateKnowledgeBase
        showBtn={false}
        isEdit={showEdit}
        data={knowledgeBase}
        onUpdate={handleRefreshPage}
        onClose={() => setShowEdit(false)}
      />
      {graphVisible && (
        <div className="fixed inset-0 z-[2000] cosmic-modal-bg">
          <div className="absolute inset-0 flex flex-col cosmic-modal-panel">
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 backdrop-blur">
              <div>
                <div className="text-lg font-semibold text-white/90">{t("knowledgeBase.detail.graph.title")}</div>
                <div className="text-xs text-white/50">{knowledgeBase?.name}</div>
              </div>
              <div className="flex gap-2">
                <Button
                  ghost
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={handleGraphRefresh}
                  loading={graphLoading}
                  className="cosmic-btn"
                >
                  {t("knowledgeBase.detail.graph.refresh")}
                </Button>
                <Button
                  type="primary"
                  icon={<CloseOutlined />}
                  onClick={handleCloseGraph}
                  className="cosmic-btn danger"
                >
                  {t("knowledgeBase.detail.graph.close")}
                </Button>
              </div>
            </div>
            <div className="flex-1 relative">
              {graphLoading ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Spin size="large" />
                </div>
              ) : (
                <KnowledgeGraphView
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  height="100%"
                  onSelectEntity={setGraphSelection}
                />
              )}
              {graphSelection && (
                <div className="absolute bottom-4 right-4 w-80 max-h-[65vh] overflow-auto rounded-lg bg-slate-900/95 text-white shadow-[0_10px_50px_rgba(15,23,42,0.7)] border border-white/15 p-4">
                  <div className="text-sm font-semibold mb-1 text-white">
                    {graphSelection.type === "node" ? t("knowledgeBase.detail.graph.nodeDetail") : t("knowledgeBase.detail.graph.edgeDetail")}
                  </div>
                  <div className="text-xs text-white/70 mb-3">ID: {graphSelection.data.id}</div>
                  {graphSelection.type === "edge" && (
                    <div className="space-y-1 text-xs mb-3">
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">{t("knowledgeBase.detail.graph.typeLabel")}</span>
                        <span className="text-right break-all text-white">{graphSelection.data.type}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">{t("knowledgeBase.detail.graph.sourceNode")}</span>
                        <span className="text-right break-all text-white">{graphSelection.data.source}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">{t("knowledgeBase.detail.graph.targetNode")}</span>
                        <span className="text-right break-all text-white">{graphSelection.data.target}</span>
                      </div>
                      <div className="border-t border-white/15 my-2" />
                    </div>
                  )}
                  {graphSelection.type === "node" && (
                    <div className="space-y-1 text-xs mb-3">
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">{t("knowledgeBase.detail.graph.labelLabel")}</span>
                        <span className="text-right break-all text-white">
                          {graphSelection.data.labels?.join(", ") || "-"}
                        </span>
                      </div>
                      <div className="border-t border-white/15 my-2" />
                    </div>
                  )}
                  <div className="space-y-1 text-xs">
                    {Object.entries(graphSelection.data.properties ?? {}).map(([key, value]) => (
                      <div key={key} className="flex justify-between gap-2">
                        <span className="text-white/60">{key}</span>
                        <span className="text-right break-all text-white">
                          {typeof value === "object" ? JSON.stringify(value) : String(value ?? "-")}
                        </span>
                      </div>
                    ))}
                    {!Object.keys(graphSelection.data.properties ?? {}).length && (
                      <div className="text-white/60">{t("knowledgeBase.detail.graph.noProperties")}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <div className="flex-1 border-card p-6 mt-4">
        <div className="flex items-center justify-between mb-4 gap-3">
          <div className="flex items-center gap-2">
            <Button type={activeTab === 'fileList' ? 'primary' : 'default'} onClick={() => setActiveTab('fileList')}>
              {t("knowledgeBase.detail.tabs.fileList")}
            </Button>
            <Button type={activeTab === 'recallTest' ? 'primary' : 'default'} onClick={() => setActiveTab('recallTest')}>
              {t("knowledgeBase.detail.tabs.recallTest")}
            </Button>
          </div>
          {activeTab === 'fileList' && (
            <>
              <div className="flex-1">
                <SearchControls
                  searchTerm={searchParams.keyword}
                  onSearchChange={handleKeywordChange}
                  searchPlaceholder={t("knowledgeBase.detail.searchPlaceholder")}
                  filters={[]}
                  onFiltersChange={handleFiltersChange}
                  onClearFilters={() =>
                    setSearchParams({
                      ...searchParams,
                      filter: { type: [], status: [], tags: [], categories: [], selectedStar: false },
                    })
                  }
                  showViewToggle={false}
                  showReload={false}
                />
              </div>
              <AddDataDialog knowledgeBase={knowledgeBase} onDataAdded={handleRefreshPage} />
            </>
          )}
        </div>

        {activeTab === 'fileList' ? (
          <Table
            loading={loading}
            columns={fileColumns}
            dataSource={files}
            rowKey="id"
            pagination={pagination}
            scroll={{ y: "calc(100vh - 30rem)" }}
          />
        ) : (
          <div className="p-2">
            <div style={{ fontSize: 14, fontWeight: 300, marginBottom: 8 }}>{t("knowledgeBase.detail.recallTest.description")}</div>
            <div className="flex items-center mb-4">
              <Input.Search
                value={recallQuery}
                onChange={e => setRecallQuery(e.target.value)}
                onSearch={handleRecallTest}
                placeholder={t("knowledgeBase.detail.recallTest.placeholder")}
                enterButton={t("knowledgeBase.detail.recallTest.searchButton")}
                loading={recallLoading}
                style={{ width: "100%", fontSize: 18, height: 48 }}
              />
            </div>
            {recallLoading ? (
              <Spin className="mt-8" />
            ) : recallResults.length === 0 ? (
              <Empty description={t("knowledgeBase.detail.recallTest.noResult")} />
            ) : knowledgeBase?.type === KBType.GRAPH ? (
              <div className="w-full">
                {(() => {
                  const item = recallResults[0];
                  if (!item) return null;
                  return (
                    <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
                      <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200">
                        <div className="text-xs text-gray-500 font-mono break-all">
                          ID: {item.id ?? "-"}
                        </div>
                      </div>
                       <div className="p-5">
                        <div className="prose prose-slate prose-sm max-w-none
                          prose-headings:text-slate-800 prose-headings:font-semibold
                          prose-p:text-gray-700 prose-p:leading-relaxed prose-p:m-0
                          prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
                          prose-strong:text-slate-800 prose-em:text-slate-600
                          prose-li:text-gray-700
                          prose-code:before:content-none prose-code:after:content-none
                          prose-code:bg-slate-100 prose-code:text-rose-600 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-medium prose-code:whitespace-nowrap
                          prose-pre:bg-slate-900 prose-pre:shadow-lg
                          prose-blockquote:border-l-blue-400 prose-blockquote:bg-slate-50 prose-blockquote:py-1 prose-blockquote:not-italic
                          prose-table:border-collapse prose-th:bg-slate-100 prose-th:border prose-th:border-slate-300 prose-th:px-3 prose-th:py-2
                          prose-td:border prose-td:border-slate-200 prose-td:px-3 prose-td:py-2
                          prose-img:rounded-lg prose-img:shadow-md
                          prose-hr:border-slate-200">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code({ node, inline, className, children, ...props }: any) {
                                const match = /language-(\w+)/.exec(className || '');
                                const codeString = String(children).replace(/\n$/, '');
                                const shouldRenderInline = inline ?? (!match && !codeString.includes("\n"));

                                if (shouldRenderInline) {
                                  return (
                                    <code className="text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded text-sm font-mono inline" {...props}>
                                      {children}
                                    </code>
                                  );
                                }

                                // 有指定语言的代码块才高亮
                                if (match) {
                                  return (
                                    <SyntaxHighlighter
                                      {...props}
                                      style={vscDarkPlus}
                                      language={match[1]}
                                      PreTag="div"
                                      customStyle={{
                                        borderRadius: '0.5rem',
                                        padding: '1rem',
                                        fontSize: '0.8rem',
                                        margin: '0.5rem 0',
                                        overflow: 'auto',
                                        maxWidth: '100%'
                                      }}
                                    >
                                      {codeString}
                                    </SyntaxHighlighter>
                                  );
                                }

                                // 无语言标记的代码块，以普通文本显示（不高亮）
                                return (
                                  <pre className="bg-transparent text-slate-700 p-0 overflow-x-auto text-sm whitespace-pre font-sans leading-relaxed">
                                    {codeString}
                                  </pre>
                                );
                              },
                              p: ({ children }) => (
                                <p className="text-gray-700 leading-relaxed m-0 inline-block !whitespace-nowrap">
                                  {children}
                                </p>
                              ),
                              ul: ({ children }) => (
                                <ul className="my-2 pl-5 list-disc overflow-x-auto !whitespace-nowrap">
                                  {children}
                                </ul>
                              ),
                              ol: ({ children }) => (
                                <ol className="my-2 pl-5 list-decimal overflow-x-auto !whitespace-nowrap">
                                  {children}
                                </ol>
                              ),
                              li: ({ children }) => (
                                <li className="!whitespace-nowrap">
                                  {children}
                                </li>
                              ),
                              br: () => <span> </span>,
                              a: ({ href, children }) => (
                                <a
                                  href={href}
                                  className="text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {children}
                                </a>
                              ),
                              table: ({ children }) => (
                                <div className="overflow-x-auto my-4 rounded border border-slate-200">
                                  <table className="min-w-full">{children}</table>
                                </div>
                              ),
                              thead: ({ children }) => (
                                <thead className="bg-slate-50">{children}</thead>
                              ),
                              th: ({ children }) => (
                                <th className="px-4 py-2 text-left text-sm font-semibold text-slate-700 border-b border-slate-200">{children}</th>
                              ),
                              td: ({ children }) => (
                                <td className="px-4 py-2 text-sm text-slate-600 border-b border-slate-100">{children}</td>
                              ),
                              blockquote: ({ children }) => (
                                <blockquote className="border-l-4 border-blue-400 bg-slate-50 pl-4 py-2 my-4 text-slate-600 italic rounded-r">{children}</blockquote>
                              ),
                            }}
                          >
                            {squashSoftLineBreaksOutsideFences(item.text ?? "")}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recallResults.map((item, idx) => (
                  <Card key={idx} title={`${t("knowledgeBase.detail.recallTest.scoreLabel")}${item.score?.toFixed(4) ?? "-"}`}
                    extra={<span style={{ fontSize: 12 }}>ID: {item.id ?? "-"}</span>}
                    style={{ wordBreak: "break-all" }}
                  >
                    <div style={{ marginBottom: 8, fontWeight: 500 }}>{item.text ?? ""}</div>
                    <div style={{ fontSize: 12, color: '#888' }}>
                      {t("knowledgeBase.detail.recallTest.metadataLabel")} <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>{JSON.stringify(item.metadata, null, 2)}</pre>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeBaseDetailPage;
