import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router";
import { Badge, Button, Empty, List, Pagination, Spin, Typography, Popconfirm, message, Dropdown, Input } from "antd";
import type { PaginationProps } from "antd";
import { MoreOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
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
      if (res?.data?.code === 200 || res?.code === 200) {
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

  return (
    <div className="p-4 bg-white rounded-lg h-full flex flex-col overflow-hidden">
      {/* 顶部信息和返回 */}
      <div className="flex items-center justify-between mb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Title level={4} style={{ margin: 0 }}>
              合成数据详情
            </Title>
            {state.fileName && (
              <Text type="secondary" className="!text-xs">
                文件：{state.fileName}
              </Text>
            )}
          </div>
          {taskInfo && (
            <div className="text-xs text-gray-500 flex gap-4">
              <span>
                任务：{taskInfo.name}
              </span>
              <span>
                类型：
                {taskInfo.synthesis_type === "QA"
                  ? "问答对生成"
                  : taskInfo.synthesis_type === "COT"
                  ? "链式推理生成"
                  : taskInfo.synthesis_type}
              </span>
              <span>
                创建时间：{formatDateTime(taskInfo.created_at)}
              </span>
              <span>模型ID：{taskInfo.model_id}</span>
            </div>
          )}
        </div>
        <Button onClick={() => navigate(-1)}>返回</Button>
      </div>

      {/* 主体左右布局 */}
      <div className="flex flex-1 min-h-0 gap-4">
        {/* 左侧 Chunk 列表：占比 2/5 */}
        <div className="basis-2/5 max-w-[40%] border rounded-lg flex flex-col overflow-hidden">
          <div className="px-3 py-2 border-b text-sm font-medium bg-gray-50">
            Chunk 列表
          </div>
          <div className="flex-1 overflow-auto">
            {chunkLoading ? (
              <div className="h-full flex items-center justify-center">
                <Spin />
              </div>
            ) : chunks.length === 0 ? (
              <Empty description="暂无 Chunk" style={{ marginTop: 40 }} />
            ) : (
              <List
                size="small"
                dataSource={chunks}
                renderItem={(item) => {
                  const active = item.id === selectedChunkId;
                  return (
                    <List.Item
                      className={
                        "px-3 py-2 !border-0 " +
                        (active ? "bg-blue-50" : "hover:bg-gray-50")
                      }
                    >
                      <div className="flex flex-col gap-1 w-full">
                        <div
                          className="flex items-center justify-between text-xs cursor-pointer"
                          onClick={() => setSelectedChunkId(item.id)}
                        >
                          <span className="font-medium">Chunk #{item.chunk_index}</span>
                          <Badge
                            color={active ? "blue" : "default"}
                            text={active ? "当前" : ""}
                          />
                        </div>
                        <div
                          className="text-xs text-gray-600 whitespace-pre-wrap break-words cursor-pointer"
                          onClick={() => setSelectedChunkId(item.id)}
                        >
                          {item.chunk_content}
                        </div>
                        <div className="flex justify-end mt-1">
                          <Dropdown
                            menu={{
                              items: [
                                {
                                  key: "delete-chunk",
                                  danger: true,
                                  label: (
                                    <Popconfirm
                                      title="确认删除该 Chunk 及其合成数据？"
                                      onConfirm={() => {
                                        setSelectedChunkId(item.id);
                                        handleDeleteCurrentChunk();
                                      }}
                                      okText="删除"
                                      cancelText="取消"
                                    >
                                      <span className="flex items-center gap-1">
                                        <DeleteOutlined />
                                        删除该 Chunk 及合成数据
                                      </span>
                                    </Popconfirm>
                                  ),
                                },
                              ],
                            }}
                            trigger={["click"]}
                          >
                            <Button
                              size="small"
                              type="text"
                              shape="circle"
                              icon={<MoreOutlined />}
                            />
                          </Dropdown>
                        </div>
                      </div>
                    </List.Item>
                  );
                }}
              />
            )}
          </div>
          <div className="border-t px-2 py-1 flex justify-end bg-white">
            <Pagination
              size="small"
              current={chunkPagination.page}
              pageSize={chunkPagination.size}
              total={chunkPagination.total}
              onChange={handleChunkPageChange}
              showSizeChanger
              showTotal={(total) => `共 ${total} 条`}
            />
          </div>
        </div>

        {/* 右侧合成数据展示：占比 3/5 */}
        <div className="basis-3/5 max-w-[60%] border rounded-lg flex flex-col min-w-0 overflow-hidden">
          <div className="px-3 py-2 border-b flex items-center justify-between bg-gray-50 text-sm font-medium">
            <span>合成数据</span>
            {currentChunk && (
              <span className="text-xs text-gray-500">
                当前 Chunk #{currentChunk.chunk_index}
              </span>
            )}
          </div>
          <div className="flex-1 overflow-auto p-3">
            {dataLoading ? (
              <div className="h-full flex items-center justify-center">
                <Spin />
              </div>
            ) : !selectedChunkId ? (
              <Empty description="请选择左侧 Chunk" style={{ marginTop: 40 }} />
            ) : synthDataList.length === 0 ? (
              <Empty description="该 Chunk 暂无合成数据" style={{ marginTop: 40 }} />
            ) : (
              <div className="space-y-4">
                {synthDataList.map((item, index) => {
                  const isEditing = editingId === item.id;
                  return (
                    <div
                      key={item.id || index}
                      className="border border-gray-100 rounded-md p-3 bg-white shadow-sm/50 relative"
                    >
                      <div className="mb-2 text-xs text-gray-500 flex justify-between">
                        <span>记录 {index + 1}</span>
                        <span>ID：{item.id}</span>
                      </div>

                      {/* 右下角更多操作按钮：编辑 & 删除 */}
                      <div className="absolute bottom-2 right-2 flex gap-1">
                        <Dropdown
                          menu={{
                            items: [
                              {
                                key: "edit-data",
                                label: (
                                  <span className="flex items-center gap-1">
                                    <EditOutlined />
                                    编辑
                                  </span>
                                ),
                                onClick: (info) => {
                                  info.domEvent.stopPropagation();
                                  startEdit(item);
                                },
                              },
                              {
                                key: "delete-data",
                                danger: true,
                                label: (
                                  <Popconfirm
                                    title="确认删除该条合成数据？"
                                    onConfirm={(e) => {
                                      e?.stopPropagation();
                                      handleDeleteSingleSynthesisData(item.id);
                                    }}
                                    okText="删除"
                                    cancelText="取消"
                                  >
                                    <span className="flex items-center gap-1">
                                      <DeleteOutlined />
                                      删除
                                    </span>
                                  </Popconfirm>
                                ),
                              },
                            ],
                          }}
                          trigger={["click"]}
                        >
                          <Button
                            size="small"
                            type="text"
                            shape="circle"
                            icon={<MoreOutlined />}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </Dropdown>
                      </div>

                      {/* 表格形式的 key-value 展示 + 可编辑 value */}
                      <div className="w-full border border-gray-100 rounded-md overflow-hidden mt-2">
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
                                "grid grid-cols-[120px,1fr] text-xs " +
                                (rowIdx % 2 === 0 ? "bg-gray-50/60" : "bg-white")
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
                                    autoSize={{ minRows: 1, maxRows: 4 }}
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
                            取消
                          </Button>
                          <Button
                            size="small"
                            type="primary"
                            onClick={() => handleSaveEdit(item)}
                          >
                            确定
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
  );
}
