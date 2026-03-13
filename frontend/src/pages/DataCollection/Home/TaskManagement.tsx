import { App, Button, Card, Table, Tag, Tooltip } from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ProfileOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import DeleteConfirmModal from "@/components/DeleteConfirmModal";
import { SearchControls } from "@/components/SearchControls";
import {
  deleteTaskByIdUsingDelete,
  executeTaskByIdUsingPost,
  queryTasksUsingGet,
  stopTaskByIdUsingPost,
} from "../collection.apis";
import { type CollectionTask, TaskStatus } from "../collection.model";
import { getStatusMap, mapCollectionTask } from "../collection.const";
import useFetchData from "@/hooks/useFetchData";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";

export default function TaskManagement() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const statusMap = getStatusMap(t);

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

  const filters = [
    {
      key: "status",
      label: t("dataCollection.taskManagement.filters.statusFilter"),
      options: [
        { value: "all", label: t("dataCollection.taskManagement.filters.allStatus") },
        ...Object.values(statusMap),
      ],
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
  } = useFetchData(
    (params) => {
      const { keyword, status, ...rest } = params || {};
      return queryTasksUsingGet({
        ...rest,
        name: keyword || undefined,
        status: status || undefined,
      });
    },
    (task) => mapCollectionTask(task, t),
    30000,
    false,
    [],
    0
  );

  useEffect(() => {
    fetchData()
  }, [t]);

  const handleStartTask = async (taskId: string) => {
    await executeTaskByIdUsingPost(taskId);
    message.success(t("dataCollection.taskManagement.messages.startSuccess"));
    fetchData();
  };

  const handleStopTask = async (taskId: string) => {
    await stopTaskByIdUsingPost(taskId);
    message.success(t("dataCollection.taskManagement.messages.stopSuccess"));
    fetchData();
  };

  const handleDeleteTask = async (taskId: string) => {
    await deleteTaskByIdUsingDelete(taskId);
    message.success(t("dataCollection.taskManagement.messages.deleteSuccess"));
    setDeleteModal({ visible: false, taskId: "", taskName: "" });
    fetchData();
  };

  const showDeleteConfirm = (taskId: string, taskName: string) => {
    setDeleteModal({ visible: true, taskId, taskName });
  };

  const handleCancelDelete = () => {
    setDeleteModal({ visible: false, taskId: "", taskName: "" });
  };

  const handleRetryTask = async (taskId: string) => {
    await executeTaskByIdUsingPost(taskId);
    message.success(t("dataCollection.taskManagement.messages.retrySuccess"));
    fetchData();
  };

  const handleEditTask = (record: CollectionTask) => {
    navigate(`/data/collection/create-task?taskId=${encodeURIComponent(record.id)}`);
  };

  const taskOperations = (record: CollectionTask) => {
    // 获取实际的枚举值
    const statusValue = record.status?.value || record.status;

    const isStopped = statusValue === TaskStatus.STOPPED;
    const isFailed = statusValue === TaskStatus.FAILED;
    const isPending = statusValue === TaskStatus.PENDING;
    const isRunning = statusValue === TaskStatus.RUNNING;
    const isCompleted = statusValue === TaskStatus.COMPLETED;

    const startButton = {
      key: "start",
      label: t("dataCollection.taskManagement.actions.start"),
      icon: <PlayCircleOutlined />,
      onClick: () => handleStartTask(record.id),
    };
    const stopButton = {
      key: "stop",
      label: t("dataCollection.taskManagement.actions.stop"),
      icon: <PauseCircleOutlined />,
      onClick: () => handleStopTask(record.id),
    };
    const retryButton = {
      key: "retry",
      label: t("dataCollection.taskManagement.actions.retry"),
      icon: <ReloadOutlined />,
      onClick: () => handleRetryTask(record.id),
    };
    const editButton = {
      key: "edit",
      label: t("dataCollection.taskManagement.actions.edit"),
      icon: <EditOutlined />,
      onClick: () => handleEditTask(record),
    };

    const operations = [
      {
        key: "executions",
        label: t("dataCollection.taskManagement.actions.executionRecords"),
        icon: <ProfileOutlined />,
        onClick: () =>
          navigate(
            `/data/collection?tab=task-execution&taskId=${encodeURIComponent(record.id)}`
          ),
      },
    ];

    // 根据状态添加不同的操作按钮
    // PENDING 状态可以启动和编辑
    if (isPending) {
      operations.push(startButton);
      operations.push(editButton);
    }
    // RUNNING 状态可以编辑
    else if (isRunning) {
      operations.push(editButton);
    }
    // FAILED 状态可以重试和编辑
    else if (isFailed) {
      operations.push(retryButton);
      operations.push(editButton);
    }
    // STOPPED 状态可以启动和编辑
    else if (isStopped) {
      operations.push(startButton);
      operations.push(editButton);
    }
    // COMPLETED 状态的任务不可编辑
    else if (isCompleted) {
      // 不添加任何操作
    }
    // 其他状态（如 DRAFT）可以编辑
    else {
      operations.push(editButton);
    }

    operations.push({
      key: "delete",
      label: t("dataCollection.taskManagement.actions.delete"),
      danger: true,
      icon: <DeleteOutlined />,
      onClick: () => showDeleteConfirm(record.id, record.name),
    });

    return operations;
  };

  const columns = [
    {
      title: t("dataCollection.taskManagement.columns.taskName"),
      dataIndex: "name",
      key: "name",
      fixed: "left",
      width: 150,
      ellipsis: true,
    },
    {
      title: t("dataCollection.taskManagement.columns.status"),
      dataIndex: "status",
      key: "status",
      width: 150,
      ellipsis: true,
      render: (status: any) => (
        <Tag color={status.color}>{status.label}</Tag>
      ),
    },
    {
      title: t("dataCollection.taskManagement.columns.template"),
      dataIndex: "templateName",
      key: "templateName",
      width: 180,
      ellipsis: true,
      render: (v?: string) => v || t("common.placeholders.empty"),
    },
    {
      title: t("dataCollection.taskManagement.columns.syncMode"),
      dataIndex: "syncMode",
      key: "syncMode",
      width: 150,
      ellipsis: true,
      render: (text: any) => (
        <Tag color={text.color}>{text.label}</Tag>
      ),
    },
    {
      title: t("dataCollection.taskManagement.columns.cronExpression"),
      dataIndex: "scheduleExpression",
      key: "scheduleExpression",
      width: 200,
      ellipsis: true,
    },
    {
      title: t("dataCollection.taskManagement.columns.timeout"),
      dataIndex: "timeoutSeconds",
      key: "timeoutSeconds",
      width: 140,
      ellipsis: true,
      render: (v?: number) =>
        v === undefined || v === null
          ? t("common.placeholders.empty")
          : `${v}${t("dataCollection.execution.duration.secondsSuffix")}`,
    },
    {
      title: t("dataCollection.taskManagement.columns.description"),
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      width: 200,
    },
    {
      title: t("dataCollection.taskManagement.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      width: 150,
      ellipsis: true,
    },
    {
      title: t("dataCollection.taskManagement.columns.updatedAt"),
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 150,
      ellipsis: true,
    },
    {
      title: t("dataCollection.taskManagement.columns.actions"),
      key: "action",
      fixed: "right" as const,
      render: (_: any, record: CollectionTask) => {
        return taskOperations(record).map((op) => {
          return (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                danger={op?.danger}
                onClick={() => op.onClick()}
              />
            </Tooltip>
          );
        });
      },
    },
  ];

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={(newSearchTerm) =>
          setSearchParams((prev) => ({
            ...prev,
            keyword: newSearchTerm,
            current: 1,
          }))
        }
        searchPlaceholder={t("dataCollection.taskManagement.filters.searchPlaceholder")}
        filters={filters}
        selectedFilters={searchParams.filter}
        onFiltersChange={handleFiltersChange}
        showViewToggle={false}
        onClearFilters={() =>
          setSearchParams((prev) => ({
            ...prev,
            filter: { ...prev.filter, status: [] },
            current: 1,
            keyword: "",
          }))
        }
        onReload={fetchData}
      />

      {/* Tasks Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={tableData}
          loading={loading}
          rowKey="id"
          pagination={{
            ...pagination,
            current: searchParams.current,
            pageSize: searchParams.pageSize,
            total: pagination.total,
          }}
          scroll={{ x: "max-content", y: "calc(100vh - 25rem)" }}
        />
      </Card>

      {/* 删除确认弹窗 */}
      <DeleteConfirmModal
        visible={deleteModal.visible}
        title={t("dataCollection.taskManagement.messages.deleteTitle")}
        message={t("dataCollection.taskManagement.messages.deleteDesc", {
          itemName: deleteModal.taskName,
        })}
        itemName={deleteModal.taskName}
        onConfirm={() => handleDeleteTask(deleteModal.taskId)}
        onCancel={handleCancelDelete}
      />
    </div>
  );
}
