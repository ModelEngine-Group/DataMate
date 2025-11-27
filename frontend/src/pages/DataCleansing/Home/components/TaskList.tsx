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
import { mapTask, TaskStatusMap } from "../../cleansing.const";
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
      key: "status",
      label: "状态",
      options: [...Object.values(TaskStatusMap)],
    },
  ];

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData(queryCleaningTasksUsingGet, mapTask);

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

  const taskOperations = (record: CleansingTask) => {
    const isRunning = record.status?.value === TaskStatus.RUNNING;
    const showStart = [
      TaskStatus.PENDING,
      TaskStatus.FAILED,
      TaskStatus.STOPPED,
    ].includes(record.status?.value);
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
      ...(isRunning
        ? [ pauseBtn ]
        : []),
      ...(showStart
        ? [ startBtn ]
        : []),
      {
        key: "delete",
        label: "删除",
        danger: true,
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
      width: 150,
      ellipsis: true,
      render: (_, task: CleansingTask) => {
        return (
          <Button
            type="link"
            onClick={() =>
              navigate("/data/cleansing/task-detail/" + task.id)
            }
          >
            {task.name}
          </Button>
        );
      },
    },
    {
      title: "任务ID",
      dataIndex: "id",
      key: "id",
      width: 150,
      ellipsis: true,
    },
    {
      title: "源数据集",
      dataIndex: "srcDatasetId",
      key: "srcDatasetId",
      width: 150,
      ellipsis: true,
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
      width: 150,
      ellipsis: true,
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
      width: 100,
      render: (status: any) => {
        return <Badge color={status?.color} text={status?.label} />;
      },
    },
    {
      title: "进度",
      dataIndex: "process",
      key: "process",
      width: 200,
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: "已处理文件数",
      dataIndex: "finishedFileNum",
      key: "finishedFileNum",
      width: 120,
      align: "right",
      ellipsis: true,
    },
    {
      title: "总文件数",
      dataIndex: "totalFileNum",
      key: "totalFileNum",
      width: 100,
      align: "right",
      ellipsis: true,
    },
    {
      title: "执行耗时",
      dataIndex: "duration",
      key: "duration",
      width: 100,
      ellipsis: true,
    },
    {
      title: "开始时间",
      dataIndex: "startedAt",
      key: "startedAt",
      width: 180,
      ellipsis: true,
    },
    {
      title: "结束时间",
      dataIndex: "finishedAt",
      key: "finishedAt",
      width: 180,
      ellipsis: true,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
      ellipsis: true,
    },
    {
      title: "数据量变化",
      dataIndex: "dataSizeChange",
      key: "dataSizeChange",
      width: 180,
      ellipsis: true,
      render: (_: any, record: CleansingTask) => {
        if (record.before !== undefined && record.after !== undefined) {
          return `${record.before} → ${record.after}`;
        }
        return "-";
      },
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
                  danger={op?.danger}
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
        searchTerm={searchParams.keyword}
        onSearchChange={(keyword) =>
          setSearchParams({ ...searchParams, keyword })
        }
        searchPlaceholder="搜索任务名称、描述"
        filters={filterOptions}
        onFiltersChange={handleFiltersChange}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle={true}
        onReload={fetchData}
        onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
      />
      {/* Task List */}
      {viewMode === "card" ? (
        <CardView
          data={tableData}
          operations={taskOperations}
          pagination={pagination}
          onView={(tableData) => {
            navigate("/data/cleansing/task-detail/" + tableData.id)
          }}
        />
      ) : (
        <Card>
          <Table
            columns={taskColumns}
            dataSource={tableData}
            rowKey="id"
            loading={loading}
            scroll={{ x: "max-content", y: "calc(100vh - 35rem)" }}
            pagination={pagination}
          />
        </Card>
      )}
    </>
  );
}
