import { useState } from "react";
import { Table, Progress, Badge, Button, Tooltip, Card, App } from "antd";
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import {
  mapTask,
  TaskStatusMap,
  templateTypesMap,
} from "../../cleansing.const";
import {
  TaskStatus,
  type CleansingTask,
} from "@/pages/DataCleansing/cleansing.model";
import useFetchData from "@/hooks/useFetchData";
import {
  deleteCleaningTaskByIdUsingDelete,
  executeCleaningTaskUsingPost,
  queryCleaningTasksUsingGet,
  stopCleaningTaskUsingPost,
} from "../../cleansing.api";

export default function TaskList() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [viewMode, setViewMode] = useState<"card" | "list">("list");
  const filterOptions = [
    {
      key: "type",
      label: "类型",
      options: [
        { label: "所有类型", value: "all" },
        ...Object.values(templateTypesMap),
      ],
    },
    {
      key: "status",
      label: "状态",
      options: [
        { label: "所有状态", value: "all" },
        ...Object.values(TaskStatusMap),
      ],
    },
  ];

  const {
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData(queryCleaningTasksUsingGet, mapTask);

  const handleViewTask = (task: any) => {
    navigate("/data/cleansing/task-detail/" + task.id);
  };

  const pauseTask = async (item: CleansingTask) => {
    await stopCleaningTaskUsingPost(item.id);
    message.success("任务已暂停");
    fetchData();
  };

  const startTask = async (item: CleansingTask) => {
    await executeCleaningTaskUsingPost(item.id);
    message.success("任务已启动");
    fetchData();
  };

  const deleteTask = async (item: CleansingTask) => {
    await deleteCleaningTaskByIdUsingDelete(item.id);
    message.success("任务已删除");
    fetchData();
  };

  const taskOperations = (record) => {
    const isRunning = record.status?.value === TaskStatus.RUNNING;
    const isPending = record.status?.value === TaskStatus.PENDING;
    
    const pauseBtn = {
      key: "pause",
      label: "暂停",
      icon: isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />,
      onClick: pauseTask, // implement pause/play logic
    };

    const startBtn = {
      key: "start",
      label: "启动",
      icon: isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />,
      onClick: startTask, // implement pause/play logic
    };
    return [
      isRunning && pauseBtn,
      isPending && startBtn,
      {
        key: "delete",
        label: "删除",
        icon: <DeleteOutlined />,
        onClick: deleteTask, // implement delete logic
      },
    ];
  };

  const taskColumns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      render: (text: string, record: any) => (
        <a onClick={() => handleViewTask(record)}>{text}</a>
      ),
    },
    {
      title: "源数据集",
      dataIndex: "srcDatasetId",
      key: "srcDatasetId",
      render: (_, record: CleansingTask) => {
        return (
          <Button
            type="link"
            onClick={() =>
              navigate("/data/management/detail/" + record.srcDatasetId)
            }
          >
            {record.srcDatasetName}
          </Button>
        );
      },
    },
    {
      title: "目标数据集",
      dataIndex: "destDatasetId",
      key: "destDatasetId",
      render: (_, record: CleansingTask) => {
        return (
          <Button
            type="link"
            onClick={() =>
              navigate("/data/management/detail/" + record.destDatasetId)
            }
          >
            {record.destDatasetName}
          </Button>
        );
      },
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: any) => {
        return <Badge color={status.color} text={status.label} />;
      },
    },
    {
      title: "开始时间",
      dataIndex: "startedAt",
      key: "startedAt",
      width: 180,
    },
    {
      title: "结束时间",
      dataIndex: "endedAt",
      key: "endedAt",
      width: 180,
      sorter: true,
    },
    {
      title: "进度",
      dataIndex: "progress",
      key: "progress",
      width: 200,
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: "操作",
      key: "action",
      fixed: "right",
      render: (text: string, record: any) => (
        <div className="flex gap-2">
          {taskOperations(record).map((op) =>
            op ? (
              <Tooltip key={op.key} title={op.label}>
                <Button
                  type="text"
                  icon={op.icon}
                  onClick={() => op.onClick(record)}
                />
              </Tooltip>
            ) : null
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      {/* Search and Filters */}
      <SearchControls
        className="mb-4"
        searchTerm={searchParams.keywords}
        onSearchChange={(keywords) =>
          setSearchParams({ ...searchParams, keywords })
        }
        searchPlaceholder="搜索任务名称、描述"
        filters={filterOptions}
        onFiltersChange={handleFiltersChange}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle={true}
        onReload={fetchData}
      />
      {/* Task List */}
      {viewMode === "card" ? (
        <CardView
          data={tableData}
          operations={taskOperations}
          onView={(item) =>
            handleViewTask(tableData.find((t) => t.id === item.id))
          }
          pagination={pagination}
        />
      ) : (
        <Card>
          <Table
            columns={taskColumns}
            dataSource={tableData}
            rowKey="id"
            scroll={{ x: "max-content", y: "calc(100vh - 20rem)" }}
            pagination={pagination}
          />
        </Card>
      )}
    </>
  );
}
