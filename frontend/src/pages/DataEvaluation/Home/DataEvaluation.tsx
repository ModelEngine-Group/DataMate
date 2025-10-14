import { useState, useEffect } from "react";
import { Button, Card, Badge, Progress, Table } from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  UserOutlined,
  RobotOutlined,
  EditOutlined,
} from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import { mockTasks } from "@/mock/evaluation";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import type { Dataset } from "@/pages/DataManagement/dataset.model";

export default function DataEvaluationPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<EvaluationTask[]>(mockTasks);
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  // 搜索和过滤状态
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<
    Record<string, string[]>
  >({});
  const [sortBy, setSortBy] = useState("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"card" | "table">("card");

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("evaluation-tasks", JSON.stringify(tasks));
    }
  }, [tasks]);

  // 搜索和过滤配置
  const filterOptions = [
    {
      key: "evaluationType",
      label: "评估方式",
      options: [
        { label: "模型评估", value: "model" },
        { label: "人工评估", value: "manual" },
      ],
    },
    {
      key: "status",
      label: "状态",
      options: [
        { label: "待处理", value: "pending" },
        { label: "运行中", value: "running" },
        { label: "已完成", value: "completed" },
        { label: "失败", value: "failed" },
      ],
    },
    {
      key: "dataset",
      label: "数据集",
      options: datasets.map((d) => ({ label: d.name, value: d.id })),
    },
  ];

  const sortOptions = [
    { label: "创建时间", value: "createdAt" },
    { label: "任务名称", value: "name" },
    { label: "完成时间", value: "completedAt" },
    { label: "评分", value: "score" },
  ];

  // 过滤和排序逻辑
  const filteredTasks = tasks.filter((task) => {
    // 搜索过滤
    if (
      searchTerm &&
      !task.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !task.datasetName.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }

    // 评估方式过滤
    if (
      selectedFilters.evaluationType?.length &&
      !selectedFilters.evaluationType.includes(task.evaluationType)
    ) {
      return false;
    }

    // 状态过滤
    if (
      selectedFilters.status?.length &&
      !selectedFilters.status.includes(task.status)
    ) {
      return false;
    }

    // 数据集过滤
    if (
      selectedFilters.dataset?.length &&
      !selectedFilters.dataset.includes(task.datasetId)
    ) {
      return false;
    }

    return true;
  });

  // 排序
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    let aValue: any = a[sortBy as keyof EvaluationTask];
    let bValue: any = b[sortBy as keyof EvaluationTask];

    if (sortBy === "score") {
      aValue = a.score || 0;
      bValue = b.score || 0;
    }

    if (typeof aValue === "string") {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }

    if (sortOrder === "asc") {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "green";
      case "running":
        return "blue";
      case "failed":
        return "red";
      case "pending":
        return "gold";
      default:
        return "gray";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircleOutlined />;
      case "running":
        return <ReloadOutlined spin />;
      case "failed":
        return <CloseCircleOutlined />;
      case "pending":
        return <ClockCircleOutlined />;
      default:
        return <ExclamationCircleOutlined />;
    }
  };

  // 开始人工评估
  const handleStartManualEvaluation = (task: EvaluationTask) => {
    navigate(`/data/evaluation/manual-evaluate/${task.id}`);
  };

  // 查看评估报告
  const handleViewReport = (task: EvaluationTask) => {
    navigate(`/data/evaluation/task-report/${task.id}`);
  };

  // 删除任务
  const handleDeleteTask = (taskId: string) => {
    setTasks(tasks.filter((task) => task.id !== taskId));
  };

  // 主列表界面
  return (
    <div>
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">数据评估</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/data/evaluation/create-task")}
        >
          创建评估任务
        </Button>
      </div>

      {/* 搜索和过滤控件 */}
      <SearchControls
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        searchPlaceholder="搜索任务名称或数据集..."
        filters={filterOptions}
        selectedFilters={selectedFilters}
        onFiltersChange={setSelectedFilters}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* 任务列表 */}
      {viewMode === "card" ? (
        <CardView
          data={sortedTasks.map((task) => ({
            id: task.id,
            name: task.name,
            type: task.evaluationType,
            icon:
              task.evaluationType === "model" ? (
                <RobotOutlined style={{ fontSize: 24, color: "#722ed1" }} />
              ) : (
                <UserOutlined style={{ fontSize: 24, color: "#52c41a" }} />
              ),
            iconColor: "",
            status: {
              label:
                task.status === "completed"
                  ? "已完成"
                  : task.status === "running"
                  ? "运行中"
                  : task.status === "failed"
                  ? "失败"
                  : "待处理",
              icon: getStatusIcon(task.status),
              color: getStatusColor(task.status),
            },
            description: task.description,
            tags: [task.datasetName],
            statistics: [
              {
                label: "进度",
                value: task.progress !== undefined ? `${task.progress}%` : "-",
              },
              { label: "评分", value: task.score ? `${task.score}分` : "-" },
            ],
            lastModified: task.createdAt,
          }))}
          operations={[
            {
              key: "view",
              label: "查看报告",
              icon: <EyeOutlined />,
              onClick: (item) => {
                const task = tasks.find((t) => t.id === item.id);
                if (task) handleViewReport(task);
              },
            },
            {
              key: "evaluate",
              label: "开始评估",
              icon: <EditOutlined />,
              onClick: (item) => {
                const task = tasks.find((t) => t.id === item.id);
                if (task) handleStartManualEvaluation(task);
              },
            },
            {
              key: "delete",
              label: "删除",
              icon: <DeleteOutlined />,
              onClick: (item) => handleDeleteTask(item.id as string),
            },
          ]}
          onView={(item) => {
            const task = tasks.find((t) => t.id === item.id);
            if (task) handleViewReport(task);
          }}
        />
      ) : (
        <Card>
          <Table
            rowKey="id"
            dataSource={sortedTasks}
            pagination={false}
            scroll={{ x: "max-content" }}
            columns={[
              {
                title: "任务名称",
                dataIndex: "name",
                key: "name",
                render: (text, record) => (
                  <div>
                    <div style={{ fontWeight: 500 }}>{text}</div>
                    <div style={{ fontSize: 13, color: "#888" }}>
                      {record.description}
                    </div>
                  </div>
                ),
              },
              {
                title: "数据集",
                dataIndex: "datasetName",
                key: "datasetName",
                render: (text) => (
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 4 }}
                  >
                    <DatabaseOutlined />
                    <span style={{ fontSize: 13 }}>{text}</span>
                  </div>
                ),
              },
              {
                title: "评估方式",
                dataIndex: "evaluationType",
                key: "evaluationType",
                render: (type) => (
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 4 }}
                  >
                    {type === "model" ? (
                      <RobotOutlined style={{ color: "#722ed1" }} />
                    ) : (
                      <UserOutlined style={{ color: "#52c41a" }} />
                    )}
                    <span style={{ fontSize: 13 }}>
                      {type === "model" ? "模型评估" : "人工评估"}
                    </span>
                  </div>
                ),
              },
              {
                title: "状态",
                dataIndex: "status",
                key: "status",
                render: (status) => (
                  <Badge
                    color={getStatusColor(status)}
                    style={{ background: "none", padding: 0 }}
                    count={
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                      >
                        {getStatusIcon(status)}
                        <span>
                          {status === "completed" && "已完成"}
                          {status === "running" && "运行中"}
                          {status === "failed" && "失败"}
                          {status === "pending" && "待处理"}
                        </span>
                      </span>
                    }
                    showZero={false}
                  />
                ),
              },
              {
                title: "进度",
                dataIndex: "progress",
                key: "progress",
                render: (progress) =>
                  progress !== undefined ? (
                    <div style={{ width: 100 }}>
                      <Progress
                        percent={progress}
                        size="small"
                        showInfo={false}
                      />
                      <div
                        style={{
                          fontSize: 12,
                          color: "#888",
                          textAlign: "right",
                        }}
                      >
                        {progress}%
                      </div>
                    </div>
                  ) : (
                    <span style={{ fontSize: 13, color: "#bbb" }}>-</span>
                  ),
              },
              {
                title: "评分",
                dataIndex: "score",
                key: "score",
                render: (score) =>
                  score ? (
                    <span style={{ fontWeight: 500, color: "#389e0d" }}>
                      {score}分
                    </span>
                  ) : (
                    <span style={{ fontSize: 13, color: "#bbb" }}>-</span>
                  ),
              },
              {
                title: "创建时间",
                dataIndex: "createdAt",
                key: "createdAt",
                render: (text) => <span style={{ fontSize: 13 }}>{text}</span>,
              },
              {
                title: "操作",
                key: "action",
                render: (_, task) => (
                  <div style={{ display: "flex", gap: 8 }}>
                    {task.status === "completed" && (
                      <Button
                        type="default"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewReport(task)}
                      >
                        报告
                      </Button>
                    )}
                    {task.evaluationType === "manual" &&
                      task.status === "pending" && (
                        <Button
                          type="default"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => handleStartManualEvaluation(task)}
                        >
                          评估
                        </Button>
                      )}
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeleteTask(task.id)}
                    />
                  </div>
                ),
              },
            ]}
            locale={{
              emptyText: (
                <div
                  style={{ textAlign: "center", padding: 48, color: "#bbb" }}
                >
                  <DatabaseOutlined style={{ fontSize: 48, marginBottom: 8 }} />
                  <div style={{ marginTop: 8 }}>暂无评估任务</div>
                  <div style={{ fontSize: 13, color: "#ccc" }}>
                    点击"创建评估任务"开始评估数据集质量
                  </div>
                </div>
              ),
            }}
          />
        </Card>
      )}

      {sortedTasks.length === 0 && (
        <div style={{ textAlign: "center", padding: "48px 0" }}>
          <DatabaseOutlined
            style={{ fontSize: 64, color: "#bbb", marginBottom: 16 }}
          />
          <div style={{ fontSize: 18, fontWeight: 500, marginBottom: 8 }}>
            暂无评估任务
          </div>
          <div style={{ color: "#888", marginBottom: 24 }}>
            创建您的第一个数据评估任务
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate("/data/evaluation/create-task")}
          >
            创建评估任务
          </Button>
        </div>
      )}
    </div>
  );
}
