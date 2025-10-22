import { useState } from "react";
import { Card, Button, Table, message } from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";
import type { AnnotationTask } from "../annotation.model";
import useFetchData from "@/hooks/useFetchData";
import {
  deleteAnnotationTaskByIdUsingDelete,
  queryAnnotationTasksUsingGet,
  syncAnnotationTaskUsingPost,
} from "../annotation.api";
import { mapAnnotationTask } from "../annotation.const";
import CreateAnnotationTask from "../Create/components/CreateAnnptationTaskDialog";
import { ColumnType } from "antd/es/table";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

export default function DataAnnotation() {
  return <DevelopmentInProgress showTime="2025.10.30" />;
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"list" | "card">("list");
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData(queryAnnotationTasksUsingGet, mapAnnotationTask);

  const handleAnnotate = (task: AnnotationTask) => {
    navigate(`/data/annotation/task-annotate/${task.datasetType}/${task.id}`);
  };

  const handleDelete = async (task: AnnotationTask) => {
    await deleteAnnotationTaskByIdUsingDelete({
      m: task.id,
      proj: task.projId,
    });
  };

  const handleSync = async (task: AnnotationTask, format: string) => {
    await syncAnnotationTaskUsingPost({ task, format });
    message.success("任务同步请求已发送");
  };

  const operations = [
    {
      key: "annotate",
      label: "标注",
      icon: (
        <EditOutlined
          className="w-4 h-4 text-green-400"
          style={{ color: "#52c41a" }}
        />
      ),
      onClick: handleAnnotate,
    },
    {
      key: "sync",
      label: "同步",
      icon: <SyncOutlined className="w-4 h-4" style={{ color: "#722ed1" }} />,
      onClick: handleSync,
    },
    {
      key: "delete",
      label: "删除",
      icon: <DeleteOutlined style={{ color: "#f5222d" }} />,
      onClick: handleDelete,
    },
  ];

  const columns: ColumnType[] = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      fixed: "left" as const,
    },
    {
      title: "任务ID",
      dataIndex: "id",
      key: "id",
    },
    {
      title: "数据集",
      dataIndex: "datasetName",
      key: "datasetName",
      width: 180,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 180,
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right" as const,
      width: 150,
      dataIndex: "actions",
      render: (_: any, task: AnnotationTask) => (
        <div className="flex items-center justify-center space-x-1">
          {operations.map((operation) => (
            <Button
              key={operation.key}
              type="text"
              icon={operation.icon}
              onClick={() => operation?.onClick?.(task)}
              title={operation.label}
            />
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">数据标注</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setShowCreateDialog(true)}
        >
          创建标注任务
        </Button>
      </div>

      {/* Filters Toolbar */}
      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={(keyword) =>
          setSearchParams({ ...searchParams, keyword })
        }
        searchPlaceholder="搜索任务名称、描述"
        onFiltersChange={handleFiltersChange}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle={true}
        onReload={fetchData}
      />
      {/* Task List/Card */}
      {viewMode === "list" ? (
        <Card>
          <Table
            key="id"
            loading={loading}
            columns={columns}
            dataSource={tableData}
            pagination={pagination}
            scroll={{ x: "max-content", y: "calc(100vh - 20rem)" }}
          />
        </Card>
      ) : (
        <CardView data={tableData} operations={operations} />
      )}
      <CreateAnnotationTask
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onRefresh={fetchData}
      />
    </div>
  );
}
