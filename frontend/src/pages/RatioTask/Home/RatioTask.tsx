import { useState } from "react";
import { Button, Card, Table, Tooltip, App } from "antd";
import { Plus, Clock, Play, CheckCircle, AlertCircle, Pause, BarChart3 } from "lucide-react";
import { DeleteOutlined } from "@ant-design/icons";
import type { RatioTaskItem } from "@/pages/RatioTask/ratio.model.ts";
import { useNavigate } from "react-router";
import CardView from "@/components/CardView.tsx";
import { SearchControls } from "@/components/SearchControls.tsx";
import { queryRatioTasksUsingGet, deleteRatioTasksUsingDelete } from "@/pages/RatioTask/ratio.api.ts";
import useFetchData from "@/hooks/useFetchData";

export default function RatioTasksPage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");
  const { message } = App.useApp();

  const { loading, tableData, pagination, searchParams, setSearchParams, handleFiltersChange, fetchData } =
    useFetchData<RatioTaskItem>(queryRatioTasksUsingGet, (d) => d as RatioTaskItem, 30000, true, [], 0);

  const handleDelete = async (id: string) => {
    await deleteRatioTasksUsingDelete([id]);
    message.success("删除成功");
    await fetchData();
  };

  const getStatusBadge = (status: string) => {
    const s = (status || "").toUpperCase();
    const statusConfig = {
      PENDING: {
        label: "等待中",
        color: "#f09e10ff",
        icon: <Clock className="w-4 h-4 inline mr-1" />,
      },
      RUNNING: {
        label: "运行中",
        color: "#007bff",
        icon: <Play className="w-4 h-4 inline mr-1" />,
      },
      SUCCESS: {
        label: "已完成",
        color: "#28a745",
        icon: <CheckCircle className="w-4 h-4 inline mr-1" />,
      },
      FAILED: {
        label: "失败",
        color: "#dc3545",
        icon: <AlertCircle className="w-4 h-4 inline mr-1" />,
      },
      PAUSED: {
        label: "已暂停",
        color: "#6c757d",
        icon: <Pause className="w-4 h-4 inline mr-1" />,
      },
    };
    return statusConfig[s as keyof typeof statusConfig] || statusConfig.PENDING;
  };

  const columns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (v: string) => getStatusBadge(v).label,
    },
    {
      title: "配比方式",
      dataIndex: "ratio_method",
      key: "ratio_method",
    },
    {
      title: "目标数量",
      dataIndex: "totals",
      key: "totals",
    },
    {
      title: "目标数据集",
      dataIndex: "target_dataset_name",
      key: "target_dataset_name",
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
    },
    {
      title: "操作",
      key: "actions",
      render: (_: any, task: RatioTaskItem) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                onClick={() => op.onClick(task.id)}
              />
            </Tooltip>
          ))}
        </div>
      ),
    },
  ];

  const renderTableView = () => (
    <Card>
      <Table
        columns={columns}
        dataSource={tableData}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        scroll={{ x: "max-content" }}
        locale={{
          emptyText: (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                暂无配比任务
              </h3>
              <p className="text-gray-500 mb-4">
                {searchParams.keyword || (searchParams.filter?.status?.[0] && searchParams.filter?.status?.[0] !== "all")
                  ? "没有找到匹配的任务"
                  : "开始创建您的第一个配比任务"}
              </p>
              {!searchParams.keyword && (!searchParams.filter?.status?.length || searchParams.filter?.status?.[0] === "all") && (
                  <Button
                    onClick={() =>
                      navigate("/data/synthesis/ratio-task/create")
                    }
                    type="primary"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    创建配比任务
                  </Button>
                )}
            </div>
          ),
        }}
      />
    </Card>
  );
  const operations = [
    {
      key: "delete",
      label: "删除",
      danger: true,
      confirm: {
        title: "确认删除该数据集？",
        description: "删除后该数据集将无法恢复，请谨慎操作。",
        okText: "删除",
        cancelText: "取消",
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: (item) => handleDelete(String(item.id)),
    }
  ];
  const renderCardView = () => (
    <CardView
      loading={loading}
      data={tableData.map((task) => ({
        ...task,
        description: task.ratio_method === "DATASET" ? "按数据集配比" : "按标签配比",
        icon: <BarChart3 className="w-6 h-6" />,
        iconColor: task.ratio_method === "DATASET" ? "bg-blue-100" : "bg-green-100",
        statistics: [
          {
            label: "目标数量",
            value: (task.totals ?? 0).toLocaleString(),
          },
          {
            label: "创建时间",
            value: task.created_at || "-",
          },
        ],
        status: getStatusBadge(task.status),
      }))}
      pagination={pagination}
      operations={operations}
    />
  );

  // 搜索、筛选和视图控制相关
  const searchFilters = [
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

  // 处理 SearchControls 的筛选变化
  const handleSearchControlsFiltersChange = (
    filters: Record<string, string[]>
  ) => {
    handleFiltersChange(filters);
  };

  // 处理视图切换
  const handleViewModeChange = (mode: "card" | "list") => {
    setViewMode(mode === "card" ? "card" : "list");
  };

  return (
    <div className="">
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
          onSearchChange={(keyword) => setSearchParams({ ...searchParams, keyword })}
          searchPlaceholder="搜索任务名称"
          filters={searchFilters}
          onFiltersChange={handleSearchControlsFiltersChange}
          onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
          viewMode={viewMode === "card" ? "card" : "list"}
          onViewModeChange={handleViewModeChange}
          showViewToggle={true}
        />
        {/* 任务列表 */}
        {viewMode === "list" ? renderTableView() : renderCardView()}
      </>
    </div>
  );
}
