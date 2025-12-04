import { useState, useEffect, ElementType } from "react";
import { Card, Button, Badge, Table, Modal, message, Tooltip } from "antd";
import {
  Plus,
  ArrowUp,
  ArrowDown,
  Pause,
  Play,
  CheckCircle,
  Sparkles,
} from "lucide-react";
import { DeleteOutlined, EyeOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { SearchControls } from "@/components/SearchControls";
import { formatDateTime } from "@/utils/unit";
import {
  querySynthesisTasksUsingGet,
  deleteSynthesisTaskByIdUsingDelete,
} from "@/pages/SynthesisTask/synthesis-api";

interface SynthesisTask {
  id: string;
  name: string;
  description?: string;
  status: string;
  synthesis_type: string;
  model_id: string;
  progress?: number;
  result_data_location?: string;
  text_split_config?: {
    chunk_size: number;
    chunk_overlap: number;
  };
  synthesis_config?: {
    temperature?: number | null;
    prompt_template?: string;
    synthesis_count?: number | null;
  };
  source_file_id?: string[];
  total_files?: number;
  processed_files?: number;
  total_chunks?: number;
  processed_chunks?: number;
  total_synthesis_data?: number;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
}

export default function SynthesisTaskTab() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [tasks, setTasks] = useState<SynthesisTask[]>([]);
  const [filterStatus, setFilterStatus] = useState("all");
  const [sortBy, setSortBy] = useState<"createdAt" | "name">("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // 获取任务列表
  const loadTasks = async () => {
    setLoading(true);
    try {
      const params = {
        page: page,
        page_size: pageSize,
      } as {
        page?: number;
        page_size?: number;
        synthesis_type?: string;
        status?: string;
        name?: string;
      };
      if (searchQuery) params.name = searchQuery;
      if (filterStatus !== "all") params.synthesis_type = filterStatus;
      const res = await querySynthesisTasksUsingGet(params);
      setTasks(res?.data?.content || []);
      setTotal(res?.data?.totalElements || 0);
    } catch {
      setTasks([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    // eslint-disable-next-line
  }, [searchQuery, filterStatus, page, pageSize]);

  // 状态徽章
  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { label: string; color: string; icon: ElementType }> = {
      pending: { label: "等待中", color: "#F59E0B", icon: Pause },
      running: { label: "运行中", color: "#3B82F6", icon: Play },
      completed: { label: "已完成", color: "#10B981", icon: CheckCircle },
      failed: { label: "失败", color: "#EF4444", icon: Pause },
      paused: { label: "已暂停", color: "#E5E7EB", icon: Pause },
    };
    return statusConfig[status] ?? statusConfig["pending"];
  };

  // 类型映射
  const typeMap: Record<string, string> = {
    QA: "问答对生成",
    COT: "链式推理生成",
  };

  // 表格列
  const taskColumns = [
    {
      title: (
        <Button
          type="text"
          onClick={() => {
            if (sortBy === "name") {
              setSortOrder(sortOrder === "asc" ? "desc" : "asc");
            } else {
              setSortBy("name");
              setSortOrder("desc");
            }
          }}
          className="h-auto p-0 font-semibold text-gray-700 hover:bg-transparent"
        >
          任务名称
          {sortBy === "name" &&
            (sortOrder === "asc" ? (
              <ArrowUp className="w-3 h-3 ml-1" />
            ) : (
              <ArrowDown className="w-3 h-3 ml-1" />
            ))}
        </Button>
      ),
      dataIndex: "name",
      key: "name",
      fixed: "left" as const,
      render: (_: unknown, task: SynthesisTask) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-base">
              {task.synthesis_type?.toUpperCase()?.slice(0, 1) || "T"}
            </span>
          </div>
          <div>
            <Link to={`/data/synthesis/task/${task.id}`}>{task.name}</Link>
          </div>
        </div>
      ),
    },
    {
      title: "类型",
      dataIndex: "synthesis_type",
      key: "synthesis_type",
      render: (type: string) => typeMap[type] || type,
    },
    {
      title: "文件数",
      dataIndex: "total_files",
      key: "total_files",
      render: (num: number, task: SynthesisTask) => <span>{num ?? (task.source_file_id?.length ?? 0)}</span>,
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (val: string) => formatDateTime(val),
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right" as const,
      render: (_: unknown, task: SynthesisTask) => (
        <div className="flex items-center justify-center gap-1">
          <Tooltip title="查看详情">
            <Button
              onClick={() => navigate(`/data/synthesis/task/${task.id}`)}
              className="hover:bg-blue-50 p-1 h-7 w-7"
              type="text"
              icon={<EyeOutlined />}
            />
          </Tooltip>
          <Tooltip title="删除任务">
            <Button
              danger
              type="text"
              className="hover:bg-red-50 p-1 h-7 w-7"
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: `确认删除任务？`,
                  content: `任务名：${task.name}`,
                  okText: "删除",
                  okType: "danger",
                  cancelText: "取消",
                  onOk: async () => {
                    try {
                      await deleteSynthesisTaskByIdUsingDelete(task.id);
                      message.success("删除成功");
                      loadTasks();
                    } catch {
                      message.error("删除失败");
                    }
                  },
                });
              }}
            />
          </Tooltip>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* 搜索和筛选 */}
      <SearchControls
        searchTerm={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="搜索任务名称..."
        filters={[
          {
            key: "status",
            label: "类型",
            options: [
              { label: "全部类型", value: "all" },
              { label: "问答对生成", value: "QA" },
              { label: "链式推理生成", value: "COT" },
            ],
          },
        ]}
        selectedFilters={{ status: [filterStatus] }}
        onFiltersChange={(filters) => {
          setFilterStatus(filters.status?.[0] || "all");
        }}
        showFilters
        showViewToggle={false}
      />
      {/* 任务表格 */}
      <Card>
        <Table
          columns={taskColumns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
            showSizeChanger: true,
          }}
          scroll={{ x: "max-content" }}
          locale={{
            emptyText: (
              <div className="text-center py-12">
                <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-gray-900 mb-2">
                  暂无合成任务
                </h3>
                <p className="text-gray-500 mb-4 text-sm">
                  {searchQuery
                    ? "没有找到匹配的任务"
                    : "开始创建您的第一个合成任务"}
                </p>
                {!searchQuery && filterStatus === "all" && (
                  <Button
                    onClick={() => navigate("/data/synthesis/task/create")}
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 shadow-lg"
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    创建合成任务
                  </Button>
                )}
              </div>
            ),
          }}
        />
      </Card>
    </div>
  );
}
