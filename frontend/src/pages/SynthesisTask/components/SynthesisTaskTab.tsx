import { useState } from "react";
import { Card, Button, Badge, Table, Progress } from "antd";
import {
  Plus,
  Sparkles,
  ArrowUp,
  ArrowDown,
  Pause,
  Play,
  DownloadIcon,
  CheckCircle,
  Check,
  StopCircle,
} from "lucide-react";
import type { SynthesisTask } from "@/pages/SynthesisTask/synthesis";
import { mockSynthesisTasks } from "@/mock/synthesis";
import { Link, useNavigate } from "react-router";
import { SearchControls } from "@/components/SearchControls";
import { formatDateTime } from "@/utils/unit";

export default function SynthesisTaskTab() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [tasks, setTasks] = useState<SynthesisTask[]>(mockSynthesisTasks);
  const [filterStatus, setFilterStatus] = useState("all");
  const [sortBy, setSortBy] = useState<"createdAt" | "name">("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // 过滤任务
  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.template.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      filterStatus === "all" || task.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  // 排序任务
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    if (sortBy === "createdAt") {
      const dateA = new Date(a.createdAt).getTime();
      const dateB = new Date(b.createdAt).getTime();
      return sortOrder === "asc" ? dateA - dateB : dateB - dateA;
    } else if (sortBy === "name") {
      return sortOrder === "asc"
        ? a.name.localeCompare(b.name)
        : b.name.localeCompare(a.name);
    }
    return 0;
  });
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
  // 状态徽章
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: {
        label: "等待中",
        color: "#F59E0B",
        icon: Pause,
      },
      running: {
        label: "运行中",
        color: "#3B82F6",
        icon: Play,
      },
      completed: {
        label: "已完成",
        color: "#10B981",
        icon: CheckCircle,
      },
      failed: {
        label: "失败",
        color: "#EF4444",
        icon: Pause,
      },
      paused: {
        label: "已暂停",
        color: "#E5E7EB",
        icon: Pause,
      },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    );
  };

  // 任务表格列
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
      render: (text: string, task: SynthesisTask) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shadow-sm">
            {/* 可根据 type 渲染不同图标 */}
            <span className="text-white font-bold text-base">
              {task.type?.toUpperCase()?.slice(0, 1) || "T"}
            </span>
          </div>
          <div>
            <Link to={`/data/synthesis/task/${task.id}`}>{task.name}</Link>
            <div className="text-xs text-gray-500">{task.template}</div>
          </div>
        </div>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      render: (type: string) => type.toUpperCase(),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => {
        const statusConfig = getStatusBadge(status);
        return <Badge color={statusConfig.color} text={statusConfig.label} />;
      },
    },
    {
      title: "进度",
      dataIndex: "progress",
      key: "progress",
      width: 150,
      render: (_: any, task: SynthesisTask) => (
        <Progress percent={task.progress} size="small" />
      ),
    },
    {
      title: "源数据集",
      dataIndex: "sourceDataset",
      key: "sourceDataset",
      render: (text: string) => (
        <div className="text-sm text-gray-900">{text}</div>
      ),
    },
    {
      title: "生成数量",
      dataIndex: "generatedCount",
      key: "generatedCount",
      render: (_: any, task: SynthesisTask) => (
        <div className="text-sm font-medium text-gray-900">
          {task.generatedCount?.toLocaleString?.()} /{" "}
          {task.targetCount?.toLocaleString?.()}
        </div>
      ),
    },
    {
      title: "质量评分",
      dataIndex: "quality",
      key: "quality",
      render: (quality: number) => (quality ? `${quality}%` : "-"),
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      render: formatDateTime,
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right" as const,
      render: (_: any, task: SynthesisTask) => (
        <div className="flex items-center justify-center gap-1">
          {task.status === "running" && (
            <Button
              onClick={() => handleTaskAction(task.id, "pause")}
              className="hover:bg-orange-50 p-1 h-7 w-7"
              type="text"
              icon={<Pause className="w-4 h-4" />}
            ></Button>
          )}
          {task.status === "paused" && (
            <Button
              onClick={() => handleTaskAction(task.id, "resume")}
              className="hover:bg-green-50 p-1 h-7 w-7"
              type="text"
              icon={<Play className="w-4 h-4" />}
            ></Button>
          )}
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
        searchPlaceholder="搜索任务名称或模板..."
        filters={[
          {
            key: "status",
            label: "状态",
            options: [
              { label: "全部状态", value: "all" },
              { label: "等待中", value: "pending" },
              { label: "运行中", value: "running" },
              { label: "已完成", value: "completed" },
              { label: "失败", value: "failed" },
              { label: "已暂停", value: "paused" },
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
          dataSource={sortedTasks}
          rowKey="id"
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
