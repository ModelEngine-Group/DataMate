import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams, Link } from "react-router";
import {
  Badge,
  Empty,
  List,
  Pagination,
  Spin,
  Typography,
  Popconfirm,
  message,
  Dropdown,
  Input,
  Breadcrumb,
  Button,
  Tag,
} from "antd";
import type { PaginationProps } from "antd";
import { MoreOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import {
  queryChunksByFileUsingGet,
  querySynthesisDataByChunkUsingGet,
  querySynthesisTaskByIdUsingGet,
  deleteChunkWithDataUsingDelete,
  batchDeleteSynthesisDataUsingDelete,
  updateSynthesisDataUsingPatch,
} from "@/pages/SynthesisTask/synthesis-api";
import { formatDateTime } from "@/utils/unit";

interface LocationState {
  fileName?: string;
  taskId?: string;
}

interface ChunkItem {
  id: string;
  synthesis_file_instance_id: string;
  chunk_index: number;
  chunk_content: string;
  chunk_metadata?: Record<string, unknown>;
}

interface PagedChunkResponse {
  content: ChunkItem[];
  totalElements: number;
  totalPages: number;
  page: number;
  size: number;
}

interface SynthesisDataItem {
  id: string;
  data: Record<string, unknown>;
  synthesis_file_instance_id: string;
  chunk_instance_id: string;
}

interface SynthesisTaskInfo {
  id: string;
  name: string;
  synthesis_type: string;
  status: string;
  created_at: string;
  model_id: string;
}

const { Title, Text } = Typography;

export default function SynthDataDetail() {
  const { t } = useTranslation();
  const { id: fileId = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as LocationState;

  const [taskInfo, setTaskInfo] = useState<SynthesisTaskInfo | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [chunkPagination, setChunkPagination] = useState<{
    page: number;
    size: number;
    total: number;
  }>({ page: 1, size: 10, total: 0 });
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null);
  const [chunkLoading, setChunkLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [synthDataList, setSynthDataList] = useState<SynthesisDataItem[]>([]);
  const [chunkConfirmVisibleId, setChunkConfirmVisibleId] = useState<string | null>(null);
  const [dataConfirmVisibleId, setDataConfirmVisibleId] = useState<string | null>(null);

  // 加载任务信息（用于顶部展示）
  useEffect(() => {
    if (!state.taskId) return;
    querySynthesisTaskByIdUsingGet(state.taskId).then((res) => {
      setTaskInfo(res?.data?.data || null);
    });
  }, [state.taskId]);

  const fetchChunks = async (page = 1, size = 10) => {
    if (!fileId) return;
    setChunkLoading(true);
    try {
      const res = await queryChunksByFileUsingGet(fileId, { page, page_size: size });
      const payload: PagedChunkResponse =
        res?.data?.data ?? res?.data ?? {
          content: [],
          totalElements: 0,
          totalPages: 0,
          page,
          size,
        };
      setChunks(payload.content || []);
      setChunkPagination({
        page: payload.page ?? page,
        size: payload.size ?? size,
        total: payload.totalElements ?? payload.content?.length ?? 0,
      });
      // 默认选中第一个 chunk
      if (!selectedChunkId && payload.content && payload.content.length > 0) {
        setSelectedChunkId(payload.content[0].id);
      }
    } finally {
      setChunkLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks(1, chunkPagination.size);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId]);

  const handleChunkPageChange: PaginationProps["onChange"] = (page, pageSize) => {
    fetchChunks(page, pageSize || 10);
  };

  // 删除当前选中的 Chunk 及其合成数据
  const handleDeleteCurrentChunk = async () => {
    if (!selectedChunkId) return;
    try {
      const res = await deleteChunkWithDataUsingDelete(selectedChunkId);
      if (res?.data) {
        message.success("删除成功");
      } else {
        message.success("删除成功");
      }
      setSelectedChunkId(null);
      fetchChunks(1, chunkPagination.size);
    } catch (error) {
      console.error("Failed to delete chunk", error);
      message.error("删除失败，请稍后重试");
    }
  };

  // 加载选中 chunk 的所有合成数据
  const fetchSynthData = async (chunkId: string) => {
    setDataLoading(true);
    try {
      const res = await querySynthesisDataByChunkUsingGet(chunkId);
      const list: SynthesisDataItem[] = res?.data?.data ?? res?.data ?? [];
      setSynthDataList(list || []);
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    if (selectedChunkId) {
      fetchSynthData(selectedChunkId);
    } else {
      setSynthDataList([]);
    }
  }, [selectedChunkId]);

  const currentChunk = useMemo(
    () => chunks.find((c) => c.id === selectedChunkId) || null,
    [chunks, selectedChunkId]
  );

  // 将合成数据的 data 转换成键值对数组，方便以表格形式展示
  const getDataEntries = (data: Record<string, unknown>) => {
    return Object.entries(data || {});
  };

  // 单条合成数据删除
  const handleDeleteSingleSynthesisData = async (dataId: string) => {
    try {
      await batchDeleteSynthesisDataUsingDelete({ ids: [dataId] });
      message.success("删除成功");
      if (selectedChunkId) {
        fetchSynthData(selectedChunkId);
      }
    } catch (error) {
      console.error("Failed to delete synthesis data", error);
      message.error("删除失败，请稍后重试");
    }
  };

  // 编辑状态：仅编辑各个 key 的 value
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingMap, setEditingMap] = useState<Record<string, string>>({});

  const startEdit = (item: SynthesisDataItem) => {
    setEditingId(item.id);
    const map: Record<string, string> = {};
    Object.entries(item.data || {}).forEach(([k, v]) => {
      if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
        map[k] = String(v);
      } else {
        map[k] = JSON.stringify(v);
      }
    });
    setEditingMap(map);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingMap({});
  };

  const handleSaveEdit = async (item: SynthesisDataItem) => {
    if (editingId !== item.id) return;
    try {
      const newData: Record<string, unknown> = { ...item.data };
      Object.entries(editingMap).forEach(([k, v]) => {
        const original = item.data?.[k];
        if (typeof original === "object" && original !== null) {
          try {
            newData[k] = JSON.parse(v);
          } catch {
            newData[k] = v;
          }
        } else if (typeof original === "number") {
          const n = Number(v);
          newData[k] = Number.isNaN(n) ? v : n;
        } else if (typeof original === "boolean") {
          if (v === "true" || v === "false") {
            newData[k] = v === "true";
          } else {
            newData[k] = v;
          }
        } else {
          newData[k] = v;
        }
      });

      await updateSynthesisDataUsingPatch(item.id, { data: newData });
      message.success("保存成功");
      cancelEdit();
      if (selectedChunkId) {
        fetchSynthData(selectedChunkId);
      }
    } catch (error) {
      console.error("Failed to update synthesis data", error);
      message.error("保存失败，请稍后重试");
    }
  };

  const breadItems = [
    {
      title: <Link to="/data/synthesis/task">{t('synthesisTask.detail.breadcrumb.tasks')}</Link>,
    },
    {
      title: state.taskId ? (
        <Link to={`/data/synthesis/task/${state.taskId}`}>{taskInfo?.name || t('synthesisTask.detail.breadcrumb.taskDetail')}</Link>
      ) : (
        taskInfo?.name || t('synthesisTask.detail.breadcrumb.taskDetail')
      ),
    },
    {
      title: state.fileName || t('synthesisTask.detail.breadcrumb.fileDetail'),
    },
  ];

  const showChunkConfirm = (id: string) => setChunkConfirmVisibleId(id);
  const hideChunkConfirm = () => setChunkConfirmVisibleId(null);

  const showDataConfirm = (id: string) => setDataConfirmVisibleId(id);
  const hideDataConfirm = () => setDataConfirmVisibleId(null);

  return (
    <>
      <Breadcrumb items={breadItems} />
      {/* 全局删除确认遮罩：Chunk */}
      {chunkConfirmVisibleId && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-lg px-6 py-4 shadow-lg min-w-[320px] max-w-[420px]">
            <div className="text-sm font-medium mb-2">{t('synthesisTask.detail.chunkList.confirmDeleteTitle')}</div>
            <div className="text-xs text-gray-500 mb-4 break-all">
              {t('synthesisTask.detail.chunkList.confirmDeleteDesc', { id: chunkConfirmVisibleId })}
            </div>
            <div className="flex justify-end gap-2 text-sm">
              <Button size="small" onClick={hideChunkConfirm}>
                {t('synthesisTask.actions.cancel')}
              </Button>
              <Button
                size="small"
                type="primary"
                danger
                onClick={async () => {
                  setSelectedChunkId(chunkConfirmVisibleId);
                  await handleDeleteCurrentChunk();
                  hideChunkConfirm();
                }}
              >
                {t('synthesisTask.actions.delete')}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 全局删除确认遮罩：合成数据 */}
      {dataConfirmVisibleId && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-lg px-6 py-4 shadow-lg min-w-[320px] max-w-[480px]">
            <div className="text-sm font-medium mb-2">{t('synthesisTask.detail.synthData.confirmDeleteTitle')}</div>
            <div className="text-xs text-gray-500 mb-4 break-all">
              {t('synthesisTask.detail.synthData.confirmDeleteDesc', { id: dataConfirmVisibleId })}
            </div>
            <div className="flex justify-end gap-2 text-sm">
              <Button size="small" onClick={hideDataConfirm}>
                {t('synthesisTask.actions.cancel')}
              </Button>
              <Button
                size="small"
                type="primary"
                danger
                onClick={async () => {
                  await handleDeleteSingleSynthesisData(dataConfirmVisibleId);
                  hideDataConfirm();
                }}
              >
                {t('synthesisTask.actions.delete')}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 flex flex-1 flex-col overflow-hidden rounded-lg bg-transparent">
        <div className="flex flex-1 min-h-0 gap-4">
          {/* 左侧 Chunk 列表 */}
          <div className="basis-2/5 max-w-[40%] flex flex-col min-w-0">
            <div className="rounded-lg border border-gray-100 bg-white shadow-sm flex flex-col overflow-hidden h-full">
              <div className="px-4 py-3 border-b border-gray-100 text-sm font-medium bg-gray-50/80 flex items-center justify-between">
                <span>{t('synthesisTask.detail.chunkList.title')}</span>
                {chunkPagination.total ? (
                  <span className="text-xs text-gray-400">{t('synthesisTask.detail.chunkList.total', { count: chunkPagination.total })}</span>
                ) : null}
              </div>
              <div className="flex-1 overflow-auto">
                {chunkLoading ? (
                  <div className="h-full flex items-center justify-center">
                    <Spin size="small" />
                  </div>
                ) : chunks.length === 0 ? (
                  <Empty description={t('synthesisTask.detail.chunkList.empty')} style={{ marginTop: 40 }} />
                ) : (
                  <List
                    size="small"
                    className="!border-0"
                    dataSource={chunks}
                    renderItem={(item) => {
                      const active = item.id === selectedChunkId;
                      return (
                        <List.Item
                          className={
                            "!border-0 px-4 py-3 transition-colors rounded-none " +
                            (active
                              ? "bg-blue-200 hover:bg-blue-300"
                              : "hover:bg-blue-50")
                          }
                          onClick={() => setSelectedChunkId(item.id)}
                        >
                          <div className="flex flex-col gap-1 w-full">
                            <div className="flex items-center justify-between text-[12px] text-gray-500">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-gray-800">
                                  {t('synthesisTask.detail.chunkList.chunkIndex', { index: item.chunk_index })}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                {/* 右侧显示 Chunk ID，完整展示 */}
                                <span className="text-[11px] text-gray-400" title={item.id}>
                                </span>
                                <Button
                                  type="text"
                                  size="small"
                                  shape="circle"
                                  danger
                                  icon={<DeleteOutlined className="text-[12px]" />}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    showChunkConfirm(item.id);
                                  }}
                                />
                              </div>
                            </div>
                            <div className="text-xs text-gray-600 whitespace-pre-wrap break-words leading-relaxed">
                              {item.chunk_content}
                            </div>
                          </div>
                        </List.Item>
                      );
                    }}
                  />
                )}
              </div>
              {chunkPagination.total ? (
              <div className="border-t border-gray-100 px-3 py-2 flex justify-end bg-white">
                <Pagination
                  size="small"
                  current={chunkPagination.page}
                  pageSize={chunkPagination.size}
                  total={chunkPagination.total}
                  onChange={handleChunkPageChange}
                  showSizeChanger
                  showTotal={(total) => t('synthesisTask.detail.pagination.total', { total })}
                />
              </div>
              ) : null}
            </div>
          </div>

          {/* 右侧合成数据展示 */}
          <div className="basis-3/5 max-w-[60%] flex flex-col min-w-0">
            <div className="rounded-lg border border-gray-100 bg-white shadow-sm flex flex-col overflow-hidden h-full">
              <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-gray-50/80 text-sm font-medium">
                <span>{t('synthesisTask.detail.synthData.title')}</span>
                {currentChunk && (
                  <Tag color="blue" className="text-xs px-2 py-0.5 m-0 rounded-full border-none bg-blue-100 text-blue-200">
                    {t('synthesisTask.detail.synthData.currentChunk', { index: currentChunk.chunk_index })}
                  </Tag>
                )}
              </div>
              <div className="flex-1 overflow-auto p-4">
                {dataLoading ? (
                  <div className="h-full flex items-center justify-center">
                    <Spin size="small" />
                  </div>
                ) : !selectedChunkId ? (
                  <Empty description={t('synthesisTask.detail.synthData.noChunkSelected')} style={{ marginTop: 40 }} />
                ) : synthDataList.length === 0 ? (
                  <Empty description={t('synthesisTask.detail.synthData.empty')} style={{ marginTop: 40 }} />
                ) : (
                  <div className="space-y-4">
                    {synthDataList.map((item, index) => {
                      const isEditing = editingId === item.id;
                      return (
                        <div
                          key={item.id || index}
                          className="border border-gray-100 rounded-md p-3 bg-white hover:bg-blue-50/80 transition-colors"
                        >
                          <div className="mb-2 text-[12px] text-gray-500 flex justify-between items-center">
                            <span>{t('synthesisTask.detail.synthData.record', { index: index + 1 })}</span>
                            <div className="flex items-center gap-2">
                              <span title={item.id}>{t('synthesisTask.common.id', { id: item.id })}</span>
                              {!isEditing && (
                                <>
                                  <Button
                                    type="text"
                                    size="small"
                                    shape="circle"
                                    icon={<EditOutlined className="text-[13px]" />}
                                    onClick={() => startEdit(item)}
                                  />
                                  <Button
                                    type="text"
                                    size="small"
                                    shape="circle"
                                    danger
                                    icon={<DeleteOutlined className="text-[13px]" />}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      showDataConfirm(item.id);
                                    }}
                                  />
                                </>
                              )}
                            </div>
                          </div>

                          {/* key-value 展示区域：不再截断，完整展示 */}
                          <div className="border border-gray-100 rounded-md overflow-hidden">
                            {getDataEntries(item.data).map(([key, value], rowIdx) => {
                              const displayValue =
                                typeof value === "string" ||
                                typeof value === "number" ||
                                typeof value === "boolean"
                                  ? String(value)
                                  : JSON.stringify(value, null, 2);

                              return (
                                <div
                                  key={key + rowIdx}
                                  className={
                                    "grid grid-cols-[120px,1fr] text-[12px] " +
                                    (rowIdx % 2 === 0 ? "bg-white" : "bg-gray-50/80")
                                  }
                                >
                                  <div className="px-3 py-2 border-r border-gray-100 font-medium text-gray-600 break-words">
                                    {key}
                                  </div>
                                  <div className="px-3 py-2 text-gray-700 whitespace-pre-wrap break-words">
                                    {isEditing ? (
                                      <Input.TextArea
                                        value={editingMap[key] ?? displayValue}
                                        onChange={(e) => {
                                          const v = e.target.value;
                                          setEditingMap((prev) => ({ ...prev, [key]: v }));
                                        }}
                                        autoSize={{ minRows: 1, maxRows: 6 }}
                                      />
                                    ) : (
                                      displayValue
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {isEditing && (
                            <div className="flex justify-end gap-2 mt-2">
                              <Button size="small" onClick={cancelEdit}>
                                {t('synthesisTask.actions.cancel')}
                              </Button>
                              <Button
                                size="small"
                                type="primary"
                                onClick={() => handleSaveEdit(item)}
                              >
                                {t('synthesisTask.actions.confirm')}
                              </Button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
