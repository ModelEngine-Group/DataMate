import { useState, useEffect } from "react";
import { Button, Card, Table, App, Badge, Popconfirm } from "antd";
import { Plus } from "lucide-react";
import { DeleteOutlined } from "@ant-design/icons";
import type { RatioTaskItem } from "@/pages/RatioTask/ratio.model";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
    (item) => mapRatioTask(item, t),
    30000,
    true,
    [],
    0
  );

  useEffect(() => {
    fetchData();
  }, [t]);

  const handleDeleteTask = async (task: RatioTaskItem) => {
    try {
      await deleteRatioTasksUsingDelete(task.id);
      message.success(t("ratioTask.home.messages.deleteSuccess"));
      fetchData();
    } catch (error) {
      message.error(t("ratioTask.home.messages.deleteFailed"));
    }
  };

  const filters = [
    {
      key: "status",
      label: t("ratioTask.home.filters.statusFilter"),
      options: [
        { label: t("ratioTask.home.filters.allStatus"), value: "all" },
        { label: t("ratioTask.home.filters.pending"), value: "PENDING" },
        { label: t("ratioTask.home.filters.running"), value: "RUNNING" },
        { label: t("ratioTask.home.filters.success"), value: "SUCCESS" },
        { label: t("ratioTask.home.filters.failed"), value: "FAILED" },
        { label: t("ratioTask.home.filters.paused"), value: "PAUSED" },
      ],
    },
  ];

  const columns = [
    {
      title: t("ratioTask.home.columns.taskName"),
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
      title: t("ratioTask.home.columns.status"),
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
      title: t("ratioTask.home.columns.targetCount"),
      dataIndex: "totals",
      key: "totals",
      width: 120,
    },
    {
      title: t("ratioTask.home.columns.targetDataset"),
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
      title: t("ratioTask.home.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
    },
    {
      title: t("ratioTask.home.columns.actions"),
      key: "actions",
      width: 120,
      fixed: "right" as const,
      render: (_: any, task: RatioTaskItem) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => {
            if (op.confirm) {
              return (
                <Popconfirm
                  key={op.key}
                  title={op.confirm.title}
                  description={op.confirm.description}
                  okText={op.confirm.okText}
                  cancelText={op.confirm.cancelText}
                  onConfirm={() => op.onClick(task)}
                >
                  <Button type="text" icon={op.icon} danger={op.danger} />
                </Popconfirm>
              );
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
      label: t("ratioTask.home.confirm.okText"),
      danger: true,
      confirm: {
        title: t("ratioTask.home.confirm.deleteTitle"),
        description: t("ratioTask.home.confirm.deleteDesc"),
        okText: t("ratioTask.home.confirm.okText"),
        cancelText: t("ratioTask.home.confirm.cancelText"),
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDeleteTask,
    },
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{t("ratioTask.home.title")}</h2>
        <Button
          type="primary"
          onClick={() => navigate("/data/synthesis/ratio-task/create")}
          icon={<Plus className="w-4 h-4" />}
        >
          {t("ratioTask.home.createTask")}
        </Button>
      </div>
      <>
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={handleKeywordChange}
          searchPlaceholder={t("ratioTask.home.searchPlaceholder")}
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
