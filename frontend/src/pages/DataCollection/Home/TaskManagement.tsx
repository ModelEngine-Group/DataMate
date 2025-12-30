import {App, Button, Card, Popconfirm, Table, Tag, Tooltip,} from "antd";
import {DeleteOutlined, PauseCircleOutlined, PlayCircleOutlined, ProfileOutlined,} from "@ant-design/icons";
import {SearchControls} from "@/components/SearchControls";
import {
  deleteTaskByIdUsingDelete,
  executeTaskByIdUsingPost,
  queryTasksUsingGet,
  stopTaskByIdUsingPost,
} from "../collection.apis";
import {type CollectionTask, TaskStatus} from "../collection.model";
import {mapCollectionTask, StatusMap} from "../collection.const";
import useFetchData from "@/hooks/useFetchData";
import {useNavigate} from "react-router";

export default function TaskManagement() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const filters = [
    {
      key: "status",
      label: "状态筛选",
      options: [
        { value: "all", label: "全部状态" },
        ...Object.values(StatusMap),
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
    mapCollectionTask,
    30000,
    false,
    [],
    0
  );

  const handleStartTask = async (taskId: string) => {
    await executeTaskByIdUsingPost(taskId);
    message.success("任务启动请求已发送");
    fetchData();
  };

  const handleStopTask = async (taskId: string) => {
    await stopTaskByIdUsingPost(taskId);
    message.success("任务停止请求已发送");
    fetchData();
  };

  const handleDeleteTask = async (taskId: string) => {
    await deleteTaskByIdUsingDelete(taskId);
    message.success("任务已删除");
    fetchData();
  };

  const taskOperations = (record: CollectionTask) => {
    const isStopped = record.status === TaskStatus.STOPPED;
    const startButton = {
      key: "start",
      label: "启动",
      icon: <PlayCircleOutlined />,
      onClick: () => handleStartTask(record.id),
    };
    const stopButton = {
      key: "stop",
      label: "停止",
      icon: <PauseCircleOutlined />,
      onClick: () => handleStopTask(record.id),
    };
    return [
      {
        key: "executions",
        label: "执行记录",
        icon: <ProfileOutlined/>,
        onClick: () =>
          navigate(
            `/data/collection?tab=task-execution&taskId=${encodeURIComponent(record.id)}`
          ),
      },
      {
        key: "delete",
        label: "删除",
        danger: true,
        icon: <DeleteOutlined/>,
        confirm: {
          title: "确定要删除该任务吗？此操作不可撤销。",
          okText: "删除",
          cancelText: "取消",
          okType: "danger",
        },
        onClick: () => handleDeleteTask(record.id),
      },
    ];
  };

  const columns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      width: 150,
      ellipsis: true,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 150,
      ellipsis: true,
      render: (status: any) => (
          <Tag color={status.color}>{status.label}</Tag>
      ),
    },
    {
      title: "所用模板",
      dataIndex: "templateName",
      key: "templateName",
      width: 180,
      ellipsis: true,
      render: (v?: string) => v || "-",
    },
    {
      title: "同步方式",
      dataIndex: "syncMode",
      key: "syncMode",
      width: 150,
      ellipsis: true,
      render: (text: any) => (
          <Tag color={text.color}>{text.label}</Tag>
      ),
    },
    {
      title: "Cron调度表达式",
      dataIndex: "scheduleExpression",
      key: "scheduleExpression",
      width: 200,
      ellipsis: true,
    },
    {
      title: "超时时间",
      dataIndex: "timeoutSeconds",
      key: "timeoutSeconds",
      width: 140,
      ellipsis: true,
      render: (v?: number) => (v === undefined || v === null ? "-" : `${v}s`),
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      width: 200,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 150,
      ellipsis: true,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 150,
      ellipsis: true,
    },
    {
      title: "操作",
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
        searchPlaceholder="搜索任务名称..."
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
