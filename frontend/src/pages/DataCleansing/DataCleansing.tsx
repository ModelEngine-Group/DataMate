import { useState } from "react";
import {
  Card,
  Tabs,
  Table,
  Progress,
  Badge,
  Button,
  Dropdown,
  Menu,
} from "antd";
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  EyeOutlined,
  SettingOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EditOutlined,
  ShareAltOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import { MOCK_TASKS, MOCK_TEMPLATES } from "@/mock/cleansing";

export default function DataProcessingPage() {
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState<"tasks" | "templates">(
    "tasks"
  );
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  // Use state to initiate with mock data
  const [cleaningTasks, setCleaningTasks] = useState(MOCK_TASKS);
  const [templateList, setTemplateList] = useState(MOCK_TEMPLATES);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      运行中: { color: "blue", icon: <PlayCircleOutlined /> },
      已完成: { color: "green", icon: <CheckCircleOutlined /> },
      队列中: { color: "gold", icon: <ClockCircleOutlined /> },
      已暂停: { color: "default", icon: <PauseCircleOutlined /> },
      失败: { color: "red", icon: <AlertOutlined /> },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.队列中
    );
  };

  const handleCreateTask = (taskData: any) => {
    const newTask = {
      id: cleaningTasks.length + 1,
      name: taskData.name,
      description: taskData.description,
      dataset: taskData.datasetId,
      newDatasetName: taskData.newDatasetName,
      template: "自定义流程",
      batchSize: taskData.batchSize,
      status: "队列中",
      progress: 0,
      startTime: "待开始",
      estimatedTime: "预计2小时",
      totalFiles: 1000,
      processedFiles: 0,
      operators: taskData.operators.map((op: any) => op.name),
    };
    setCleaningTasks([...cleaningTasks, newTask]);
    setCurrentView("list");
  };

  const handleViewTask = (task: any) => {
    setSelectedTask(task);
    navigate("/data/cleansing/task-detail/" + task.id);
  };

  const handleCreateTemplate = (templateData: any) => {
    // 在实际应用中，这里会发送API请求保存模板
    setTemplateList([...templateList, templateData]);
  };

  const handleViewTemplate = (template: any) => {
    setSelectedTemplate(template);
    navigate("/data/cleansing/create-template");
  };

  if (currentView === "create") {
    navigate("/data/cleansing/create-task");
  }

  if (currentView === "create-template") {
    navigate("/data/cleansing/create-template");
  }

  if (currentView === "detail" && selectedTask) {
    navigate(`/data/cleansing/task-detail/${selectedTask.id}`);
  }

  if (currentView === "template-detail" && selectedTemplate) {
    navigate(`/data/cleansing/template-detail/${selectedTemplate.id}`);
  }

  const taskColumns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      render: (text: string, record: any) => (
        <a onClick={() => handleViewTask(record)}>{text}</a>
      ),
    },
    {
      title: "数据集",
      dataIndex: "dataset",
      key: "dataset",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => {
        const statusConfig = getStatusBadge(status);
        return <Badge color={statusConfig.color} text={status} />;
      },
    },
    {
      title: "开始时间",
      dataIndex: "startTime",
      key: "startTime",
    },
    {
      title: "进度",
      dataIndex: "progress",
      key: "progress",
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: "操作",
      key: "action",
      render: (text: string, record: any) => (
        <div style={{ display: "flex", gap: 8 }}>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewTask(record)}
          />
          {record.status === "运行中" ? (
            <Button type="text" icon={<PauseCircleOutlined />} />
          ) : record.status === "队列中" ? (
            <Button type="text" icon={<PlayCircleOutlined />} />
          ) : null}
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item key="download" icon={<DownloadOutlined />}>
                  下载结果
                </Menu.Item>
                <Menu.Item key="delete" icon={<DeleteOutlined />} danger>
                  删除任务
                </Menu.Item>
              </Menu>
            }
            trigger={["click"]}
          >
            <Button type="text" icon={<SettingOutlined />} />
          </Dropdown>
        </div>
      ),
    },
  ];

  const renderTemplateManagement = (
    <CardView
      data={templateList.map((template) => ({
        id: template.id,
        name: template.name,
        type: template.category,
        icon: <AppstoreOutlined style={{ color: "#1677ff" }} />,
        iconColor: "bg-blue-100",
        status: {
          label: template.category,
          color: template.color,
        },
        description: template.description,
        tags: template.operators,
        statistics: [{ label: "使用次数", value: template.usage }],
        lastModified: template.updatedAt || "",
      }))}
      operations={[
        {
          key: "use",
          label: "使用模板",
          icon: <AppstoreOutlined />,
          onClick: (item) => {}, // 可实现使用模板逻辑
        },
        {
          key: "view",
          label: "查看详情",
          icon: <EyeOutlined />,
          onClick: (item) =>
            handleViewTemplate(templateList.find((t) => t.id === item.id)),
        },
        {
          key: "edit",
          label: "编辑模板",
          icon: <EditOutlined />,
          onClick: (item) => {}, // 可实现编辑逻辑
        },
        {
          key: "delete",
          label: "删除模板",
          icon: <DeleteOutlined />,
          onClick: (item) => {}, // 可实现删除逻辑
        },
      ]}
      onView={(item) =>
        handleViewTemplate(templateList.find((t) => t.id === item.id))
      }
    />
  );

  return (
    <div className="h-full flex flex-col">
      <div style={{ marginBottom: 24 }}>
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold">数据清洗</h1>
          <div className="flex gap-2">
            <Button
              icon={<PlusOutlined />}
              onClick={() => navigate("/data/cleansing/create-template")}
            >
              创建清洗模板
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate("/data/cleansing/create-task")}
            >
              创建清洗任务
            </Button>
          </div>
        </div>
      </div>

      <Tabs
        activeKey={currentView}
        onChange={(key) => setCurrentView(key as any)}
        items={[
          {
            key: "tasks",
            label: "任务列表",
          },
          {
            key: "templates",
            label: "模板管理",
          },
        ]}
      />
      {currentView === "tasks" && (
        <>
          {/* Search and Filters */}
          <SearchControls
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            searchPlaceholder="搜索任务名称、描述"
            filters={[
              {
                key: "type",
                label: "类型",
                options: [
                  { label: "所有类型", value: "all" },
                  { label: "图像", value: "image" },
                  { label: "文本", value: "text" },
                  { label: "音频", value: "audio" },
                  { label: "视频", value: "video" },
                  { label: "多模态", value: "multimodal" },
                ],
              },
              {
                key: "status",
                label: "状态",
                options: [
                  { label: "所有状态", value: "all" },
                  { label: "活跃", value: "active" },
                  { label: "处理中", value: "processing" },
                  { label: "已归档", value: "archived" },
                ],
              },
            ]}
            selectedFilters={{
              type: filterType !== "all" ? [filterType] : [],
              status: filterStatus !== "all" ? [filterStatus] : [],
            }}
            onFiltersChange={(filters) => {
              setFilterType(filters.type?.[0] || "all");
              setFilterStatus(filters.status?.[0] || "all");
            }}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            showViewToggle={true}
          />
          {/* Task List */}
          {viewMode === "card" ? (
            <CardView
              data={cleaningTasks.map((task) => ({
                id: task.id,
                name: task.name,
                type: task.template,
                icon: <DatabaseOutlined style={{ color: "#1677ff" }} />,
                iconColor: "bg-blue-100",
                status: {
                  label: task.status,
                  color: getStatusBadge(task.status).color,
                },
                description: task.description || "",
                tags: task.operators,
                statistics: [
                  { label: "进度", value: `${task.progress}%` },
                  { label: "已处理", value: task.processedFiles },
                  { label: "总数", value: task.totalFiles },
                ],
                lastModified: task.startTime,
              }))}
              operations={[
                {
                  key: "view",
                  label: "查看",
                  icon: <EyeOutlined />,
                  onClick: (item) =>
                    handleViewTask(cleaningTasks.find((t) => t.id === item.id)),
                },
                {
                  key: "download",
                  label: "下载",
                  icon: <DownloadOutlined />,
                  onClick: (item) => {}, // implement download logic
                },
                {
                  key: "delete",
                  label: "删除",
                  icon: <DeleteOutlined />,
                  onClick: (item) => {}, // implement delete logic
                },
              ]}
              onView={(item) =>
                handleViewTask(cleaningTasks.find((t) => t.id === item.id))
              }
            />
          ) : (
            <Table
              columns={taskColumns}
              dataSource={cleaningTasks}
              rowKey="id"
              scroll={{ x: "max-content", y: "100%" }}
            />
          )}
        </>
      )}
      {currentView === "templates" && renderTemplateManagement}
    </div>
  );
}
