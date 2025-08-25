import { Card, Button, Statistic, Table, Tooltip, Tag } from "antd";
import { Download, Edit, Plus, Trash2 } from "lucide-react";
import { getStatusBadge } from "@/mock/dataset";
import TagManager from "./components/TagManagement";
import { Link, useNavigate } from "react-router";
import { useState } from "react";
import { useDatasets } from "./hooks/useDatasets";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import type { Dataset } from "@/types/dataset";
import { DatasetTypeMap } from "./model";

export default function DatasetManagementPage() {
  const {
    datasets,
    pagination,
    contextHolder,
    searchTerm,
    filterOptions,
    statisticsData,
    setSearchTerm,
    handleFiltersChange,
    handleDownloadDataset,
    handleDeleteDataset,
  } = useDatasets();

  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  const operations = [
    {
      key: "edit",
      label: "编辑",
      icon: <Edit className="w-4 h-4" />,
      onClick: (item) => {
        navigate(`/data/management/create/${item.id}`);
      },
    },
    {
      key: "download",
      label: "下载",
      icon: <Download className="w-4 h-4" />,
      onClick: handleDownloadDataset,
    },
    {
      key: "delete",
      label: "删除",
      icon: <Trash2 className="w-4 h-4" />,
      onClick: (item) => handleDeleteDataset(item.id),
    },
  ];

  const columns = [
    {
      title: "名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      render: (type: string) => DatasetTypeMap[type]?.label || type,
      width: 100,
    },
    {
      title: "大小",
      dataIndex: "size",
      key: "size",
      width: 120,
    },
    {
      title: "数据项",
      dataIndex: "itemCount",
      key: "itemCount",
      render: (count: number) => <span>{count?.toLocaleString()}</span>,
      width: 100,
    },
    {
      title: "质量",
      dataIndex: "quality",
      key: "quality",
      render: (quality: number) => (
        <span className="font-medium">{quality}%</span>
      ),
      width: 100,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (_: any, record: Dataset) => {
        const status = getStatusBadge(record.status);
        return (
          <Tag icon={status.icon} color={status.color}>
            {status.label}
          </Tag>
        );
      },
      width: 120,
    },
    {
      title: "操作",
      key: "actions",
      width: 200,
      render: (_: any, record: Dataset) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                onClick={() => op.onClick(record)}
              />
            </Tooltip>
          ))}
        </div>
      ),
    },
  ];

  const renderCardView = () => (
    <CardView
      data={datasets}
      pageSize={9}
      operations={operations}
      pagination={pagination}
      onView={(dataset) => {
        navigate("/data/management/detail/" + dataset.id);
      }}
      showFavorite={false}
    />
  );

  const renderListView = () => (
    <div className="flex-1 overflow-auto">
      <Table
        columns={columns}
        dataSource={datasets}
        pagination={pagination}
        rowKey="id"
        scroll={{ x: "max-content" }}
      />
    </div>
  );

  return (
    <div className="space-y-2 h-full flex flex-col">
      {contextHolder}
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">数据管理</h1>
        </div>
        <div className="flex gap-2">
          {/* tasks */}
          <TagManager />
          <Link to="/data/management/create">
            <Button type="primary" icon={<Plus className="w-4 h-4 mr-2" />}>
              创建数据集
            </Button>
          </Link>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="数据集统计">
          <div className="grid grid-cols-4">
            {statisticsData.map((item) => (
              <Statistic
                key={item.title}
                title={item.title}
                value={item.value}
              />
            ))}
          </div>
        </Card>
        <Card title="大小统计">
          <div className="grid grid-cols-4">
            {statisticsData.map((item) => (
              <Statistic
                key={item.title}
                title={item.title}
                value={`${item.value} MB`}
              />
            ))}
          </div>
        </Card>
      </div>
      <SearchControls
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        searchPlaceholder="搜索数据集名称、描述或标签..."
        filters={filterOptions}
        onFiltersChange={handleFiltersChange}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle
      />
      {viewMode === "card" ? renderCardView() : renderListView()}
    </div>
  );
}
