import { Card, Button, Badge, Table, Dropdown, App } from "antd";
import { EllipsisOutlined } from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import {
  deleteTaskByIdUsingDelete,
  executeTaskByIdUsingPost,
  queryTasksUsingPost,
  stopTaskByIdUsingPost,
} from "../../collection.apis";
import { TaskStatus, type CollectionTask } from "../../collection.model";
import { StatusMap, SyncModeMap } from "../../collection.const";
import useFetchData from "@/hooks/useFetchData";

export default function TaskManagement() {
  const { message } = App.useApp();
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
    handleFiltersChange,
  } = useFetchData(queryTasksUsingPost);

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

  const handleViewDetail = (record: CollectionTask) => {
    // Implement your view detail logic here
    console.log("Viewing details for task:", record);
  };

  const columns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      render: (text: string, record: CollectionTask) => (
        <Button type="link" onClick={() => handleViewDetail(record)}>
          {text}
        </Button>
      ),
    },

    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) =>
        StatusMap[status] ? (
          <Badge
            color={StatusMap[status].color}
            text={StatusMap[status].label}
          />
        ) : (
          <Badge text={status} />
        ),
    },
    {
      title: "同步方式",
      dataIndex: "syncMode",
      key: "syncMode",
      render: (text: string) => <span>{SyncModeMap[text]?.label}</span>,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
    },
    {
      title: "最近执行ID",
      dataIndex: "lastExecutionId",
      key: "lastExecutionId",
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
    {
      title: "操作",
      key: "action",
      fixed: "right" as const,
      render: (_: any, record: Task) => (
        <Dropdown
          menu={{
            items: [
              record.status === TaskStatus.STOPPED
                ? {
                    key: "start",
                    label: "启动",
                    onClick: () => handleStartTask(record.id),
                  }
                : {
                    key: "stop",
                    label: "停止",
                    onClick: () => handleStopTask(record.id),
                  },
              {
                key: "edit",
                label: "编辑",
                onClick: () => handleViewDetail(record),
              },
              {
                key: "delete",
                label: "删除",
                danger: true,
                onClick: () => handleDeleteTask(record.id),
              },
            ],
          }}
          trigger={["click"]}
        >
          <Button
            type="text"
            icon={<EllipsisOutlined style={{ fontSize: 20 }} />}
          />
        </Dropdown>
      ),
    },
  ];

  return (
    <div>
      {/* Header Actions */}
      <SearchControls
        searchTerm={searchParams.keywords}
        onSearchChange={(newSearchTerm) =>
          setSearchParams((prev) => ({
            ...prev,
            keywords: newSearchTerm,
            current: 1,
          }))
        }
        searchPlaceholder="搜索任务名称或描述..."
        filters={filters}
        onFiltersChange={handleFiltersChange}
        showViewToggle={false}
        onClearFilters={() =>
          setSearchParams((prev) => ({
            ...prev,
            filters: {},
          }))
        }
        className="mb-4"
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
          scroll={{ x: "max-content" }}
        />
      </Card>
    </div>
  );
}
