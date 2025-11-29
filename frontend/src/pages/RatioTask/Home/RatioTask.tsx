import { useState } from "react";
import { Button, Card, Table, App, Badge, Popconfirm } from "antd";
import { Plus } from "lucide-react";
import { DeleteOutlined } from "@ant-design/icons";
import type { RatioTaskItem } from "@/pages/RatioTask/ratio.model";
import { useNavigate } from "react-router";
import CardView from "@/components/CardView";
import { SearchControls } from "@/components/SearchControls";
import {
  deleteRatioTasksUsingDelete,
  queryRatioTasksUsingGet,
} from "../ratio.api";
import useFetchData from "@/hooks/useFetchData";
import { mapRatioTask } from "../ratio.const";

export default function RatioTasksPage() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("list");

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    handleFiltersChange,
    fetchData,
    handleKeywordChange,
  } = useFetchData<RatioTaskItem>(
    queryRatioTasksUsingGet,
    mapRatioTask,
    30000,
    true,
    [],
    0
  );

  const handleDeleteTask = async (task: RatioTaskItem) => {
    try {
      // 调用删除接口
      await deleteRatioTasksUsingDelete(task.id);
      message.success("任务删除成功");
      // 重新加载数据
      fetchData();
    } catch (error) {
      message.error("任务删除失败，请稍后重试");
    }
  };

  // 搜索、筛选和视图控制相关
  const filters = [
    {
      key: "status",
      label: "状态筛选",
      options: [
        { label: "全部状态", value: "all" },
        { label: "等待中", value: "PENDING" },
        { label: "运行中", value: "RUNNING" },
        { label: "已完成", value: "SUCCESS" },
        { label: "失败", value: "FAILED" },
        { label: "已暂停", value: "PAUSED" },
      ],
    },
  ];

  const columns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      width: 200,
      fixed: "left" as const,
      render: (text: string, record: RatioTaskItem) => (
        <a
          onClick={() =>
            navigate(`/data/synthesis/ratio-task/detail/${record.id}`)
          }
        >
          {text}
        </a>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status) => {
        return (
          <Badge
            color={status?.color}
            icon={status?.icon}
            text={status?.label}
          />
        );
      },
    },
    {
      title: "目标数量",
      dataIndex: "totals",
      key: "totals",
      width: 120,
    },
    {
      title: "目标数据集",
      dataIndex: "target_dataset_name",
      key: "target_dataset_name",
      render: (text: string, task: RatioTaskItem) => (
        <a
          onClick={() =>
            navigate(`/data/management/detail/${task.target_dataset_id}`)
          }
        >
          {text}
        </a>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
    },
    {
      title: "操作",
      key: "actions",
      width: 120,
      fixed: "right" as const,
      render: (_: any, task: RatioTaskItem) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => {
            if (op.confirm) {
              <Popconfirm
                title={op.confirm.title}
                description={op.confirm.description}
                onConfirm={() => op.onClick(task)}
              >
                <Button type="text" icon={op.icon} />
              </Popconfirm>;
            }
            return (
              <Button
                key={op.key}
                type="text"
                icon={op.icon}
                danger={op.danger}
                onClick={() => op.onClick(task)}
              />
            );
          })}
        </div>
      ),
    },
  ];

  const operations = [
    {
      key: "delete",
      label: "删除",
      danger: true,
      confirm: {
        title: "确认删除该任务？",
        description: "删除后该任务将无法恢复，请谨慎操作。",
        okText: "删除",
        cancelText: "取消",
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDeleteTask,
    },
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">配比任务</h2>
        <Button
          type="primary"
          onClick={() => navigate("/data/synthesis/ratio-task/create")}
          icon={<Plus className="w-4 h-4" />}
        >
          创建配比任务
        </Button>
      </div>
      <>
        {/* 搜索、筛选和视图控制 */}
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={handleKeywordChange}
          searchPlaceholder="搜索任务名称..."
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClearFilters={() =>
            setSearchParams({ ...searchParams, filter: {} })
          }
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          showViewToggle
          onReload={fetchData}
        />
        {/* 任务列表 */}
        {viewMode === "list" ? (
          <Card>
            <Table
              columns={columns}
              dataSource={tableData}
              pagination={pagination}
              rowKey="id"
              scroll={{ x: "max-content", y: "calc(100vh - 30rem)" }}
            />
          </Card>
        ) : (
          <CardView
            loading={loading}
            data={tableData}
            operations={operations}
            pagination={pagination}
            onView={(task) => {
              navigate(`/data/synthesis/ratio-task/detail/${task.id}`);
            }}
          />
        )}
      </>
    </div>
  );
}
