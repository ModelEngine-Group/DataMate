import { useState } from "react";
import {
  Button,
  Card,
  Input,
  Select,
  Badge,
  Progress,
  Table,
  Alert,
} from "antd";
import {
  Plus,
  Eye,
  Clock,
  Play,
  CheckCircle,
  AlertCircle,
  Pause,
  Download as DownloadIcon,
  BarChart3,
} from "lucide-react";
import type { RatioTask } from "@/pages/RatioTask/ratio";
import { mockRatioTasks } from "@/mock/ratio";
import { useNavigate } from "react-router";
import CardView from "@/components/CardView";
import { SearchControls } from "@/components/SearchControls";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

export default function RatioTasksPage() {
  return <DevelopmentInProgress showTime="2025.11.30" />;
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  const [tasks, setTasks] = useState<RatioTask[]>(mockRatioTasks);

  // 过滤和排序任务
  const filteredAndSortedTasks = tasks
    .filter((task) => {
      const matchesSearch = task.name
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
      const matchesStatus =
        filterStatus === "all" || task.status === filterStatus;
      const matchesType = filterType === "all" || task.ratioType === filterType;
      return matchesSearch && matchesStatus && matchesType;
    })
    .sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case "name":
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case "targetCount":
          aValue = a.targetCount;
          bValue = b.targetCount;
          break;
        case "generatedCount":
          aValue = a.generatedCount;
          bValue = b.generatedCount;
          break;
        case "progress":
          aValue = a.progress;
          bValue = b.progress;
          break;
        case "createdAt":
        default:
          aValue = new Date(a.createdAt).getTime();
          bValue = new Date(b.createdAt).getTime();
          break;
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: {
        label: "等待中",
        color: "#f09e10ff",
        icon: <Clock className="w-4 h-4 inline mr-1" />,
      },
      running: {
        label: "运行中",
        color: "#007bff",
        icon: <Play className="w-4 h-4 inline mr-1" />,
      },
      completed: {
        label: "已完成",
        color: "#28a745",
        icon: <CheckCircle className="w-4 h-4 inline mr-1" />,
      },
      failed: {
        label: "失败",
        color: "#dc3545",
        icon: <AlertCircle className="w-4 h-4 inline mr-1" />,
      },
      paused: {
        label: "已暂停",
        color: "#6c757d",
        icon: <Pause className="w-4 h-4 inline mr-1" />,
      },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    );
  };

  const handleTaskAction = (taskId: number, action: string) => {
    setTasks((prev) =>
      prev.map((task) => {
        if (task.id === taskId) {
          switch (action) {
            case "pause":
              return { ...task, status: "paused" as const };
            case "resume":
              return { ...task, status: "running" as const };
            case "stop":
              return {
                ...task,
                status: "failed" as const,
                progress: task.progress,
              };
            default:
              return task;
          }
        }
        return task;
      })
    );
  };

  const columns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
    },
    {
      title: "配比方式",
      dataIndex: "ratioType",
      key: "ratioType",
    },
    {
      title: "进度",
      dataIndex: "progress",
      key: "progress",
    },
    {
      title: "目标数量",
      dataIndex: "targetCount",
      key: "targetCount",
    },
    {
      title: "已生成",
      dataIndex: "generatedCount",
      key: "generatedCount",
    },
    {
      title: "数据源",
      dataIndex: "sourceDatasets",
      key: "sourceDatasets",
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
    },
    {
      title: "操作",
      key: "actions",
      render: (_: any, task: RatioTask) => (
        <div className="flex items-center gap-1 justify-end">
          {task.status === "running" && (
            <Button
              type="link"
              size="small"
              onClick={() => handleTaskAction(task.id, "pause")}
            >
              停止
            </Button>
          )}
          {task.status === "paused" && (
            <Button
              size="small"
              type="link"
              onClick={() => handleTaskAction(task.id, "resume")}
            >
              开始
            </Button>
          )}
          <Button type="link" size="small">
            下载
          </Button>
        </div>
      ),
    },
  ];

  const renderTableView = () => (
    <Card>
      <Table
        columns={columns}
        dataSource={filteredAndSortedTasks}
        rowKey="id"
        scroll={{ x: "max-content" }}
        locale={{
          emptyText: (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                暂无配比任务
              </h3>
              <p className="text-gray-500 mb-4">
                {searchQuery || filterStatus !== "all" || filterType !== "all"
                  ? "没有找到匹配的任务"
                  : "开始创建您的第一个配比任务"}
              </p>
              {!searchQuery &&
                filterStatus === "all" &&
                filterType === "all" && (
                  <Button
                    onClick={() =>
                      navigate("/data/synthesis/ratio-task/create")
                    }
                    type="primary"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    创建配比任务
                  </Button>
                )}
            </div>
          ),
        }}
      />
    </Card>
  );
  const renderCardView = () => (
    <CardView
      data={filteredAndSortedTasks.map((task) => ({
        ...task,
        description:
          task.ratioType === "dataset" ? "按数据集配比" : "按标签配比",
        icon: <BarChart3 className="w-6 h-6" />,
        iconColor:
          task.ratioType === "dataset" ? "bg-blue-100" : "bg-green-100",
        statistics: [
          {
            label: "目标数量",
            value: task.targetCount.toLocaleString(),
          },
          {
            label: "已生成",
            value: task.generatedCount.toLocaleString(),
          },
          {
            label: "进度",
            value: `${Math.round(task.progress)}%`,
          },
        ],
        status: getStatusBadge(task.status),
      }))}
      operations={[
        {
          key: "view",
          label: "查看",
          onClick: (item) => navigate(`/data/synthesis/ratio-task/${item.id}`),
        },
        {
          key: "download",
          label: "下载",
          onClick: (item) => console.log("下载", item.name),
        },
      ]}
    />
  );

  // 搜索、筛选和视图控制相关
  const searchFilters = [
    {
      key: "status",
      label: "状态筛选",
      options: [
        { label: "全部状态", value: "all" },
        { label: "等待中", value: "pending" },
        { label: "运行中", value: "running" },
        { label: "已完成", value: "completed" },
        { label: "失败", value: "failed" },
        { label: "已暂停", value: "paused" },
      ],
    },
    {
      key: "type",
      label: "类型筛选",
      options: [
        { label: "全部类型", value: "all" },
        { label: "按数据集", value: "dataset" },
        { label: "按标签", value: "label" },
      ],
    },
    {
      key: "sortBy",
      label: "排序方式",
      options: [
        { label: "创建时间", value: "createdAt" },
        { label: "任务名称", value: "name" },
        { label: "目标数量", value: "targetCount" },
        { label: "已生成", value: "generatedCount" },
        { label: "进度", value: "progress" },
      ],
    },
    {
      key: "sortOrder",
      label: "排序顺序",
      options: [
        { label: "升序", value: "asc" },
        { label: "降序", value: "desc" },
      ],
    },
  ];

  // 处理 SearchControls 的筛选变化
  const handleSearchControlsFiltersChange = (
    filters: Record<string, string[]>
  ) => {
    setFilterStatus(filters.status?.[0] || "all");
    setFilterType(filters.type?.[0] || "all");
    setSortBy(filters.sortBy?.[0] || "createdAt");
    setSortOrder((filters.sortOrder?.[0] as "asc" | "desc") || "desc");
  };

  // 处理视图切换
  const handleViewModeChange = (mode: "card" | "list") => {
    setViewMode(mode === "card" ? "card" : "list");
  };

  return (
    <div className="">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">配比任务</h2>
        <Button
          type="primary"
          onClick={() => navigate("/data/synthesis/ratio-task/create")}
          icon={<Plus className="w-4 h-4" />}
        >
          创建配比任务
        </Button>
      </div>
      <>
        {/* 搜索、筛选和视图控制 */}
        <SearchControls
          searchTerm={searchQuery}
          onSearchChange={setSearchQuery}
          searchPlaceholder="搜索任务名称"
          filters={searchFilters}
          onFiltersChange={handleSearchControlsFiltersChange}
          viewMode={viewMode === "card" ? "card" : "list"}
          onViewModeChange={handleViewModeChange}
          showViewToggle={true}
        />
        {/* 任务列表 */}
        {viewMode === "list" ? renderTableView() : renderCardView()}
      </>
    </div>
  );
}
