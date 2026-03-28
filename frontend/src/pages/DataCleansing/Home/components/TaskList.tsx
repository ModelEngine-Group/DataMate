import { useState, useEffect } from "react";
import { Table, Progress, Badge, Button, Tooltip, Card, App, Modal } from "antd";
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import {getTaskStatusMap, mapTask} from "../../cleansing.const";
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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  // 删除确认弹窗状态
  const [deleteModal, setDeleteModal] = useState<{
    visible: boolean;
    taskId: string;
    taskName: string;
  }>({
    visible: false,
    taskId: "",
    taskName: "",
  });

  const filterOptions = [
    {
      key: "status",
      label: t("dataCleansing.task.columns.status"),
      options: [...Object.values(getTaskStatusMap(t))],
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
    handleKeywordChange,
  } = useFetchData(queryCleaningTasksUsingGet, task => mapTask(task, t));

  const pauseTask = async (item: CleansingTask) => {
    await stopCleaningTaskUsingPost(item.id);
    message.success(t("dataCleansing.task.messages.taskPaused"));
    fetchData();
  };

  const startTask = async (item: CleansingTask) => {
    await executeCleaningTaskUsingPost(item.id);
    message.success(t("dataCleansing.task.messages.taskStarted"));
    fetchData();
  };

  const deleteTask = async (item: CleansingTask) => {
    setDeleteModal({
      visible: true,
      taskId: item.id,
      taskName: item.name,
    });
  };

  const handleConfirmDelete = async () => {
    try {
      await deleteCleaningTaskByIdUsingDelete(deleteModal.taskId);
      message.success(t("dataCleansing.task.messages.taskDeleted"));
      setDeleteModal({ visible: false, taskId: "", taskName: "" });
      fetchData();
    } catch (error) {
      message.error(t("dataCleansing.task.messages.deleteFailed"));
    }
  };

  const handleCancelDelete = () => {
    setDeleteModal({ visible: false, taskId: "", taskName: "" });
  };

  const taskOperations = (record: CleansingTask) => {
    const isRunning = record.status?.value === TaskStatus.RUNNING;
    const showStart = [
      TaskStatus.PENDING,
      TaskStatus.PARTIAL_SUCCESS,
      TaskStatus.FAILED,
      TaskStatus.STOPPED,
    ].includes(record.status?.value);
    const pauseBtn = {
      key: "pause",
      label: t("dataCleansing.actions.pause"),
      icon: <PauseCircleOutlined />,
      onClick: pauseTask,
    };

    const startBtn = {
      key: "start",
      label: t("dataCleansing.actions.start"),
      icon: <PlayCircleOutlined />,
      onClick: startTask,
    };

    const deleteBtn = {
      key: "delete",
      label: t("dataCleansing.actions.delete"),
      icon: <DeleteOutlined />,
      danger: true,
      disabled: isRunning, // 运行中的任务禁用删除按钮
      onClick: deleteTask,
    };

    return [
      ...(isRunning ? [pauseBtn] : []),
      ...(showStart ? [startBtn] : []),
      deleteBtn,
    ];
  };

  const taskColumns = [
    {
      title: t("dataCleansing.task.columns.taskName"),
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
      title: t("dataCleansing.task.columns.taskId"),
      dataIndex: "id",
      key: "id",
      width: 150,
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.srcDataset"),
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
      title: t("dataCleansing.task.columns.destDataset"),
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
      title: t("dataCleansing.task.columns.status"),
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status: any) => {
        return <Badge color={status?.color} text={status?.label} />;
      },
    },
    {
      title: t("dataCleansing.task.columns.progress"),
      dataIndex: "process",
      key: "process",
      width: 150,
      render: (_, record: CleansingTask) => {
          if (record?.status?.value === TaskStatus.FAILED) {
              return <Progress percent={record?.progress?.process} size="small" status="exception" />;
          }
          if (record?.status?.value === TaskStatus.PARTIAL_SUCCESS) {
              return <Progress percent={record?.progress?.process} size="small" strokeColor="#f59e0b" />;
          }
          return <Progress percent={record?.progress?.process} size="small"/>;
      },
    },
    {
      title: t("dataCleansing.task.columns.processedFiles"),
      dataIndex: "finishedFileNum",
      key: "finishedFileNum",
      width: 120,
      align: "right",
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.totalFiles"),
      dataIndex: "totalFileNum",
      key: "totalFileNum",
      width: 100,
      align: "right",
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.duration"),
      dataIndex: "duration",
      key: "duration",
      width: 100,
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.startTime"),
      dataIndex: "startedAt",
      key: "startedAt",
      width: 180,
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.endTime"),
      dataIndex: "finishedAt",
      key: "finishedAt",
      width: 180,
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
      ellipsis: true,
    },
    {
      title: t("dataCleansing.task.columns.dataSizeChange"),
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
      title: t("dataCleansing.task.columns.actions"),
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
        onSearchChange={handleKeywordChange}
        searchPlaceholder={t("dataCleansing.placeholders.searchTaskName")}
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

      {/* 删除确认弹窗 */}
      <Modal
        title={t("dataCleansing.task.confirm.deleteTitle")}
        open={deleteModal.visible}
        onOk={handleConfirmDelete}
        onCancel={handleCancelDelete}
        okText={t("dataManagement.confirm.deleteConfirm")}
        cancelText={t("dataManagement.confirm.deleteCancel")}
        okButtonProps={{ danger: true }}
      >
        <p>{t("dataCleansing.task.confirm.deleteDesc", { itemName: deleteModal.taskName })}</p>
      </Modal>
    </>
  );
}
