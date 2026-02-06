import { App, Button, Card, Popconfirm, Table, Tag, Tooltip } from "antd";
import {
  DeleteOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ProfileOutlined,
} from "@ant-design/icons";
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
import { useEffect } from "react";

export default function TaskManagement() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const statusMap = getStatusMap(t);
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
  } = useFetchData(
    (params) => {
      const { keyword, ...rest } = params || {};
      return queryTasksUsingGet({
        ...rest,
        name: keyword || undefined,
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
    fetchData();
  };

  const taskOperations = (record: CollectionTask) => {
    const isStopped = record.status === TaskStatus.STOPPED;
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
    return [
      {
        key: "executions",
        label: t("dataCollection.taskManagement.actions.executionRecords"),
        icon: <ProfileOutlined />,
        onClick: () =>
          navigate(
            `/data/collection?tab=task-execution&taskId=${encodeURIComponent(record.id)}`
          ),
      },
      {
        key: "delete",
        label: t("dataCollection.taskManagement.actions.delete"),
        danger: true,
        icon: <DeleteOutlined />,
        confirm: {
          title: t("dataCollection.taskManagement.messages.deleteConfirm"),
          okText: t("dataCollection.taskManagement.messages.confirmDelete"),
          cancelText: t("dataCollection.taskManagement.messages.cancel"),
          okType: "danger",
        },
        onClick: () => handleDeleteTask(record.id),
      },
    ];
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
          const button = (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                danger={op?.danger}
                onClick={() => op.onClick()}
              />
            </Tooltip>
          );
          if (op.confirm) {
            return (
              <Popconfirm
                key={op.key}
                title={op.confirm.title}
                okText={op.confirm.okText}
                cancelText={op.confirm.cancelText}
                okType={op.danger ? "danger" : "primary"}
                onConfirm={() => op.onClick()}
              >
                <Tooltip key={op.key} title={op.label}>
                  <Button type="text" icon={op.icon} danger={op?.danger} />
                </Tooltip>
              </Popconfirm>
            );
          }
          return button;
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
        onFiltersChange={() => {}}
        showViewToggle={false}
        onClearFilters={() =>
          setSearchParams((prev) => ({
            ...prev,
            filter: { ...prev.filter, status: [] },
            current: 1,
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
    </div>
  );
}
