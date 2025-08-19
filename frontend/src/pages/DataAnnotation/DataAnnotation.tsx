"use client";

import { useState } from "react";
import {
  Card,
  Button,
  Table,
  Badge,
  Progress,
  Avatar,
  Dropdown,
  Menu,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  CustomerServiceOutlined,
} from "@ant-design/icons";
import { mockTasks } from "@/mock/annotation";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import type { AnnotationTask } from "@/types/data-annotation";

export default function DataAnnotation() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<AnnotationTask[]>(mockTasks);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterDatasetType, setFilterDatasetType] = useState<string>("all");
  const [searchText, setSearchText] = useState("");
  const [sortBy, setSortBy] = useState<string>("default");
  const [currentView, setCurrentView] = useState<
    "list" | "create" | "detail" | "annotate"
  >("list");
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");

  const handleTaskNameClick = (task: AnnotationTask) => {
    setSelectedTaskId(task.id);
    navigate(`/data/annotation/detail/${task.id}`);
  };

  const handleAnnotate = (task: AnnotationTask) => {
    setSelectedTaskId(task.id);
    navigate(`/data-annotation/annotation/${task.id}`);
  };

  const handleDelete = (task: AnnotationTask) => {
    setTasks(tasks.filter((t) => t.id !== task.id));
    // toast logic here
  };

  const handleDownload = (task: AnnotationTask, format: string) => {
    // ...existing download logic...
  };

  // ...other helper functions...

  // 筛选和排序逻辑
  const filteredAndSortedTasks = tasks
    .filter((task) => {
      const matchesStatus =
        filterStatus === "all" || task.status === filterStatus;
      const matchesDatasetType =
        filterDatasetType === "all" || task.datasetType === filterDatasetType;
      const matchesSearch =
        task.text.toLowerCase().includes(searchText.toLowerCase()) ||
        task.id.includes(searchText) ||
        task.name.toLowerCase().includes(searchText.toLowerCase());
      return matchesStatus && matchesDatasetType && matchesSearch;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "completed_asc":
          return a.completedCount - b.completedCount;
        case "completed_desc":
          return b.completedCount - a.completedCount;
        case "uncompleted_asc":
          return (
            a.totalCount - a.completedCount - (b.totalCount - b.completedCount)
          );
        case "uncompleted_desc":
          return (
            b.totalCount - b.completedCount - (a.totalCount - a.completedCount)
          );
        default:
          return 0;
      }
    });

  // 如果当前视图是创建任务
  if (currentView === "create") {
    router.push("/data-annotation/create-task");
  }

  // 如果当前视图是任务详情
  if (currentView === "detail") {
    const selectedTask = tasks.find((t) => t.id === selectedTaskId);
    navigate(`/data/annotation/task-detail/${selectedTask?.id}`);
  }

  // 如果当前视图是标注工作区
  if (currentView === "annotate") {
    const selectedTask = tasks.find((t) => t.id === selectedTaskId);
    navigate(`/data/annotation/annotation/${selectedTask?.id}`);
  }

  const columns: ColumnType[] = [
    {
      title: "任务ID",
      dataIndex: "id",
      key: "id",
      render: (id: string) => <span className="font-mono text-sm">{id}</span>,
    },
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      render: (_: any, task: AnnotationTask) => (
        <Button
          type="link"
          style={{ padding: 0, height: "auto" }}
          onClick={() => handleAnnotate(task)}
        >
          {task.name}
        </Button>
      ),
    },
    {
      title: "完成时间",
      dataIndex: "completed",
      key: "completed",
      render: (completed: string) => (
        <span className="text-sm text-gray-600">{completed}</span>
      ),
    },
    {
      title: "完成",
      dataIndex: "completedCount",
      key: "completedCount",
      align: "center" as const,
    },
    {
      title: "跳过",
      dataIndex: "skippedCount",
      key: "skippedCount",
      align: "center" as const,
    },
    {
      title: "总数",
      dataIndex: "totalCount",
      key: "totalCount",
      align: "center" as const,
    },
    {
      title: "标注进度",
      dataIndex: "progress",
      key: "progress",
      render: (progress: number) => (
        <div className="flex items-center space-x-2">
          <Progress percent={progress} size="small" style={{ width: 64 }} />
          <span className="text-sm text-gray-600">{progress}%</span>
        </div>
      ),
    },
    {
      title: "标注者",
      dataIndex: "annotators",
      key: "annotators",
      render: (annotators: any[]) => (
        <div className="flex items-center space-x-1">
          {annotators.map((annotator) => (
            <Avatar
              key={annotator.id}
              src={annotator.avatar || "/placeholder.svg"}
              size={24}
              style={{ marginRight: 2 }}
            >
              {annotator.name.charAt(0)}
            </Avatar>
          ))}
        </div>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <Badge
          status={
            status === "completed"
              ? "success"
              : status === "in_progress"
              ? "processing"
              : status === "skipped"
              ? "error"
              : "default"
          }
          text={
            status === "completed"
              ? "已完成"
              : status === "in_progress"
              ? "进行中"
              : status === "skipped"
              ? "已跳过"
              : "待开始"
          }
        />
      ),
    },
    {
      title: "数据类型",
      dataIndex: "datasetType",
      key: "datasetType",
      render: (type: string) => (
        <Badge
          color="blue"
          text={
            type === "text"
              ? "文本"
              : type === "image"
              ? "图像"
              : type === "video"
              ? "视频"
              : type === "audio"
              ? "音频"
              : ""
          }
        />
      ),
    },
    {
      title: "描述",
      dataIndex: "text",
      key: "text",
      render: (text: string) => (
        <div className="truncate max-w-xs text-sm text-gray-700">{text}</div>
      ),
    },
    {
      title: "操作",
      key: "actions",
      align: "center" as const,
      fixed: "right" as const,
      width: 150,
      dataIndex: "actions",
      // 使用 Ant Design 的 render 函数来定义操作列的内容
      render: (_: any, task: AnnotationTask) => (
        <div className="flex items-center justify-center space-x-1">
          <Button
            type="text"
            icon={<EditOutlined style={{ color: "#52c41a" }} />}
            onClick={() => handleAnnotate(task)}
            title="标注"
          />
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item onClick={() => handleDownload(task, "json")}>
                  JSON 格式
                </Menu.Item>
                <Menu.Item onClick={() => handleDownload(task, "csv")}>
                  CSV 格式
                </Menu.Item>
                <Menu.Item onClick={() => handleDownload(task, "xml")}>
                  XML 格式
                </Menu.Item>
                <Menu.Item onClick={() => handleDownload(task, "coco")}>
                  COCO 格式
                </Menu.Item>
              </Menu>
            }
            trigger={["click"]}
          >
            <Button
              type="text"
              icon={<DownloadOutlined style={{ color: "#722ed1" }} />}
              title="下载"
            />
          </Dropdown>
          <Button
            type="text"
            icon={<DeleteOutlined style={{ color: "#f5222d" }} />}
            onClick={() => handleDelete(task)}
            title="删除"
          />
        </div>
      ),
    },
  ];
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-bold">数据标注</span>
          </div>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCurrentView("create")}
        >
          创建标注任务
        </Button>
      </div>

      {/* Filters Toolbar */}
      <SearchControls
        searchTerm={searchText}
        onSearchChange={setSearchText}
        searchPlaceholder="搜索任务..."
        filters={[
          {
            key: "status",
            label: "状态筛选",
            options: [
              { value: "all", label: "全部状态" },
              { value: "completed", label: "已完成" },
              { value: "in_progress", label: "进行中" },
              { value: "pending", label: "待开始" },
              { value: "skipped", label: "已跳过" },
            ],
          },
          {
            key: "datasetType",
            label: "数据集类型",
            options: [
              { value: "all", label: "全部类型" },
              { value: "text", label: "文本" },
              { value: "image", label: "图像" },
              { value: "video", label: "视频" },
              { value: "audio", label: "音频" },
            ],
          },
        ]}
        selectedFilters={{
          status: filterStatus !== "all" ? [filterStatus] : [],
          datasetType: filterDatasetType !== "all" ? [filterDatasetType] : [],
        }}
        onFiltersChange={(filters) => {
          setFilterStatus(filters.status?.[0] || "all");
          setFilterDatasetType(filters.datasetType?.[0] || "all");
        }}
        sortBy={sortBy}
        sortOptions={[
          { value: "default", label: "默认排序" },
          { value: "completed_desc", label: "已标注数量↓" },
          { value: "completed_asc", label: "已标注数量↑" },
          { value: "uncompleted_desc", label: "未标注数量↓" },
          { value: "uncompleted_asc", label: "未标注数量↑" },
        ]}
        onSortChange={(field) => setSortBy(field)}
        viewMode={viewMode === "grid" ? "card" : "list"}
        onViewModeChange={(mode) =>
          setViewMode(mode === "card" ? "grid" : "list")
        }
        showViewToggle={true}
      />
      {/* Task List/Grid */}
      {viewMode === "list" ? (
        <Card>
          <Table
            columns={columns}
            dataSource={filteredAndSortedTasks}
            pagination={false}
            scroll={{ x: "max-content" }}
          />
        </Card>
      ) : (
        <CardView
          data={filteredAndSortedTasks.map((task) => ({
            id: task.id,
            name: task.name,
            type: task.datasetType,
            icon:
              task.datasetType === "text" ? (
                <FileTextOutlined style={{ color: "#1677ff" }} />
              ) : task.datasetType === "image" ? (
                <PictureOutlined style={{ color: "#52c41a" }} />
              ) : task.datasetType === "video" ? (
                <VideoCameraOutlined style={{ color: "#722ed1" }} />
              ) : task.datasetType === "audio" ? (
                <CustomerServiceOutlined style={{ color: "#fa8c16" }} />
              ) : undefined,
            iconColor:
              task.datasetType === "text"
                ? "bg-blue-100"
                : task.datasetType === "image"
                ? "bg-green-100"
                : task.datasetType === "video"
                ? "bg-purple-100"
                : task.datasetType === "audio"
                ? "bg-orange-100"
                : "bg-gray-100",
            status: {
              label:
                task.status === "completed"
                  ? "已完成"
                  : task.status === "in_progress"
                  ? "进行中"
                  : task.status === "skipped"
                  ? "已跳过"
                  : "待开始",
              color:
                task.status === "completed"
                  ? "success"
                  : task.status === "in_progress"
                  ? "processing"
                  : task.status === "skipped"
                  ? "error"
                  : "default",
            },
            description: task.text,
            tags: task.tags,
            statistics: [
              { label: "进度", value: `${task.progress}%` },
              { label: "已完成", value: task.completedCount },
              { label: "总数", value: task.totalCount },
            ],
            lastModified: task.completed,
          }))}
          operations={[
            {
              key: "annotate",
              label: "标注",
              icon: <EditOutlined style={{ color: "#52c41a" }} />,
              onClick: (item) =>
                handleAnnotate(tasks.find((t) => t.id === item.id)),
            },
            {
              key: "download",
              label: "下载",
              icon: <DownloadOutlined style={{ color: "#722ed1" }} />,
              onClick: (item) =>
                handleDownload(
                  tasks.find((t) => t.id === item.id),
                  "json"
                ),
            },
            {
              key: "delete",
              label: "删除",
              icon: <DeleteOutlined style={{ color: "#f5222d" }} />,
              onClick: (item) =>
                handleDelete(tasks.find((t) => t.id === item.id)),
            },
          ]}
          onView={(item) => handleAnnotate(tasks.find((t) => t.id === item.id))}
        />
      )}

      {/* Footer Stats */}
      <div className="text-sm text-gray-500 text-center">
        显示 {filteredAndSortedTasks.length} 个任务
      </div>
    </div>
  );
}
