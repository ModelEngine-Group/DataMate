import type React from "react";
import { useEffect, useState } from "react";
import { Table, Badge, Button, Breadcrumb, Tooltip, App, Card, Input, Empty, Spin } from "antd";
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
import { mapFileData, mapKnowledgeBase } from "../knowledge-base.const";
import {
  deleteKnowledgeBaseByIdUsingDelete,
  deleteKnowledgeBaseFileByIdUsingDelete,
  queryKnowledgeBaseByIdUsingGet,
  queryKnowledgeBaseFilesUsingGet,
  retrieveKnowledgeBaseContent,
  fetchKnowledgeGraph,
} from "../knowledge-base.api";
import useFetchData from "@/hooks/useFetchData";
import AddDataDialog from "../components/AddDataDialog";
import CreateKnowledgeBase from "../components/CreateKnowledgeBase";
import KnowledgeGraphView, { GraphEntitySelection } from "../components/KnowledgeGraphView";
import { Network } from "lucide-react";

interface StatisticItem {
  icon?: React.ReactNode;
  label: string;
  value: string | number;
}
interface RagChunk {
  id: string;
  text: string;
  metadata: string;
}
interface RecallResult {
  score: number;
  entity: RagChunk;
  id?: string | object;
  primaryKey?: string;
}

const KnowledgeBaseDetailPage: React.FC = () => {
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

  const fetchKnowledgeBaseDetails = async (id: string) => {
    const { data } = await queryKnowledgeBaseByIdUsingGet(id);
    setKnowledgeBase(mapKnowledgeBase(data));
  };

  useEffect(() => {
    if (id) {
      fetchKnowledgeBaseDetails(id);
    }
  }, [id]);

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
    mapFileData
  );

  // File table logic
  const handleDeleteFile = async (file: KBFile) => {
    try {
      await deleteKnowledgeBaseFileByIdUsingDelete(knowledgeBase!.id, {
        ids: [file.id]
      });
      message.success("文件已删除");
      fetchFiles();
    } catch {
      message.error("文件删除失败");
    }
  };

  const handleDeleteKB = async (kb: KnowledgeBaseItem) => {
    await deleteKnowledgeBaseByIdUsingDelete(kb.id);
    message.success("知识库已删除");
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
      setRecallResults(result?.data || []);
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
      const { data } = await fetchKnowledgeGraph({ knowledge_base_id: knowledgeBase.id, query: "*" });
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
  const graphOperation: DetailOperation | null = knowledgeBase?.type === KBType.GRAPH
    ? {
        key: "graph",
        label: "知识图谱",
        icon: <Network />,
        onClick: handleOpenGraph,
      }
    : null;

  const baseOperations: DetailOperation[] = [
    {
      key: "edit",
      label: "编辑知识库",
      icon: <EditOutlined className="w-4 h-4" />,
      onClick: () => {
        setShowEdit(true);
      },
    },
    {
      key: "refresh",
      label: "刷新知识库",
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: () => {
        handleRefreshPage();
      },
    },
    {
      key: "delete",
      label: "删除知识库",
      danger: true,
      confirm: {
        title: "确认删除该知识库吗？",
        description: "删除后将无法恢复，请谨慎操作。",
        cancelText: "取消",
        okText: "删除",
        okType: "danger",
        onConfirm: () => knowledgeBase && handleDeleteKB(knowledgeBase),
      },
      icon: <DeleteOutlined className="w-4 h-4" />,
    },
  ];

  const operations: DetailOperation[] = [graphOperation, ...baseOperations].filter(Boolean) as DetailOperation[];

  const fileOps = [
    {
      key: "delete",
      label: "删除文件",
      icon: <DeleteOutlined className="w-4 h-4" />,
      danger: true,
      onClick: handleDeleteFile,
    },
  ];

  const fileColumns = [
    {
      title: "文件名",
      dataIndex: "name",
      key: "name",
      width: 200,
      ellipsis: true,
      fixed: "left" as const,
      render: (_: unknown, file: KBFile) => (
        <a onClick={() => navigate(`/data/knowledge-base/file-detail/${file.id}?knowledgeBaseId=${knowledgeBase?.id || ''}&fileName=${encodeURIComponent(file.name || file.fileName || '')}`)}>
          {file.name}
        </a>
      )
    },
    {
      title: "状态",
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
      title: "分块数",
      dataIndex: "chunkCount",
      key: "chunkCount",
      width: 100,
      ellipsis: true,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
      width: 180,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
      width: 180,
    },
    {
      title: "操作",
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
            <a onClick={() => navigate("/data/knowledge-base")}>知识库</a>
          </Breadcrumb.Item>
          <Breadcrumb.Item>{knowledgeBase?.name}</Breadcrumb.Item>
        </Breadcrumb>
      </div>
      <DetailHeader
        data={knowledgeBase}
        statistics={knowledgeBase && Array.isArray((knowledgeBase as { statistics?: StatisticItem[] }).statistics)
          ? ((knowledgeBase as { statistics?: StatisticItem[] }).statistics ?? [])
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
                <div className="text-lg font-semibold text-white/90">知识图谱</div>
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
                  刷新
                </Button>
                <Button
                  type="primary"
                  icon={<CloseOutlined />}
                  onClick={handleCloseGraph}
                  className="cosmic-btn danger"
                >
                  关闭
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
                    {graphSelection.type === "node" ? "节点详情" : "边详情"}
                  </div>
                  <div className="text-xs text-white/70 mb-3">ID: {graphSelection.data.id}</div>
                  {graphSelection.type === "edge" && (
                    <div className="space-y-1 text-xs mb-3">
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">类型</span>
                        <span className="text-right break-all text-white">{graphSelection.data.type}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">源节点</span>
                        <span className="text-right break-all text-white">{graphSelection.data.source}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">目标节点</span>
                        <span className="text-right break-all text-white">{graphSelection.data.target}</span>
                      </div>
                      <div className="border-t border-white/15 my-2" />
                    </div>
                  )}
                  {graphSelection.type === "node" && (
                    <div className="space-y-1 text-xs mb-3">
                      <div className="flex justify-between gap-2">
                        <span className="text-white/60">标签</span>
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
                      <div className="text-white/60">暂无属性</div>
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
              文件列表
            </Button>
            <Button type={activeTab === 'recallTest' ? 'primary' : 'default'} onClick={() => setActiveTab('recallTest')}>
              召回测试
            </Button>
          </div>
          {activeTab === 'fileList' && (
            <>
              <div className="flex-1">
                <SearchControls
                  searchTerm={searchParams.keyword}
                  onSearchChange={handleKeywordChange}
                  searchPlaceholder="搜索文件名..."
                  filters={[]}
                  onFiltersChange={handleFiltersChange}
                  onClearFilters={() => setSearchParams({ ...searchParams, filter: { type: [], status: [], tags: [] } })}
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
            <div style={{ fontSize: 14, fontWeight: 300, marginBottom: 8 }}>基于语义文本检索和全文检索后的加权平均结果</div>
            <div className="flex items-center mb-4">
              <Input.Search
                value={recallQuery}
                onChange={e => setRecallQuery(e.target.value)}
                onSearch={handleRecallTest}
                placeholder="请输入召回测试问题"
                enterButton="检索"
                loading={recallLoading}
                style={{ width: "100%", fontSize: 18, height: 48 }}
              />
            </div>
            {recallLoading ? (
              <Spin className="mt-8" />
            ) : recallResults.length === 0 ? (
              <Empty description="暂无召回结果" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recallResults.map((item, idx) => (
                  <Card key={idx} title={`得分：${item.score?.toFixed(4) ?? "-"}`}
                    extra={<span style={{ fontSize: 12 }}>ID: {item.entity?.id ?? "-"}</span>}
                    style={{ wordBreak: "break-all" }}
                  >
                    <div style={{ marginBottom: 8, fontWeight: 500 }}>{item.entity?.text ?? ""}</div>
                    <div style={{ fontSize: 12, color: '#888' }}>
                      metadata: <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>{item.entity?.metadata}</pre>
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
