import { useState, useEffect } from "react";
import { Card, Button, Table, message, Modal } from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import type { AnnotationTask } from "../annotation.model";
import useFetchData from "@/hooks/useFetchData";
import {
  deleteAnnotationTaskByIdUsingDelete,
  queryAnnotationTasksUsingGet,
  syncAnnotationTaskUsingPost,
  getConfigUsingGet,
} from "../annotation.api";
import { mapAnnotationTask } from "../annotation.const";
import CreateAnnotationTask from "../Create/components/CreateAnnptationTaskDialog";
import { ColumnType } from "antd/es/table";
// Note: DevelopmentInProgress intentionally not used here

export default function DataAnnotation() {
  // return <DevelopmentInProgress showTime="2025.10.30" />;
  // navigate not needed for label studio external redirect
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
  } = useFetchData(queryAnnotationTasksUsingGet, mapAnnotationTask, 30000, true, [], 0);

  const [labelStudioBase, setLabelStudioBase] = useState<string | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<(string | number)[]>([]);
  const [selectedRows, setSelectedRows] = useState<any[]>([]);

  // prefetch config on mount so clicking annotate is fast and we know whether base URL exists
  // useEffect ensures this runs once
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
      const baseUrl = `http://${window.location.hostname}:8000`;
      if (mounted) setLabelStudioBase(baseUrl);
      } catch (e) {
      if (mounted) setLabelStudioBase(null);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const handleAnnotate = (task: AnnotationTask) => {
    // Open Label Studio project page in a new tab
    (async () => {
      try {
        // prefer using labeling project id already present on the task
        // `mapAnnotationTask` normalizes upstream fields into `labelingProjId`/`projId`,
        // so prefer those and fall back to the task id if necessary.
        let labelingProjId = (task as any).labelingProjId || (task as any).projId || undefined;

        // no fallback external mapping lookup; rely on normalized fields from mapAnnotationTask

        // use prefetched base if available
        const base = labelStudioBase;

        // no debug logging in production

        if (labelingProjId) {
          // only open external Label Studio when we have a configured base url
          if (base) {
            const target = `${base}/projects/${labelingProjId}/data`;
            window.open(target, "_blank");
          } else {
            // no external Label Studio URL configured — do not perform internal redirect in this version
            message.error("无法跳转到 Label Studio：未配置 Label Studio 基础 URL");
            return;
          }
        } else {
          // no labeling project id available — do not attempt internal redirect in this version
          message.error("无法跳转到 Label Studio：该映射未绑定标注项目");
          return;
        }
      } catch (error) {
        // on error, surface a user-friendly message instead of redirecting
        message.error("无法跳转到 Label Studio：发生错误，请检查配置或控制台日志");
        return;
      }
    })();
  };

  const handleDelete = (task: AnnotationTask) => {
    Modal.confirm({
      title: `确认删除标注任务「${task.name}」吗？`,
      content: (
        <div>
          <div>删除标注任务不会删除对应数据集。</div>
          <div>如需保留当前标注结果，请在同步后再删除。</div>
        </div>
      ),
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await deleteAnnotationTaskByIdUsingDelete({ m: task.id, proj: task.labelingProjId });
          message.success("映射删除成功");
          fetchData();
          // clear selection if deleted item was selected
          setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
          setSelectedRows((rows) => rows.filter((r) => r.id !== task.id));
        } catch (e) {
          console.error(e);
          message.error("删除失败，请稍后重试");
        }
      },
    });
  };

  const handleSync = (task: AnnotationTask, batchSize: number = 50) => {
    Modal.confirm({
      title: `确认同步标注任务「${task.name}」吗？`,
      content: (
        <div>
          <div>标注工程中文件列表将与数据集保持一致，差异项将会被修正。</div>
          <div>标注工程中的标签与数据集中标签将进行合并，冲突项将以最新一次内容为准。</div>
        </div>
      ),
      okText: "同步",
      cancelText: "取消",
      onOk: async () => {
        try {
          await syncAnnotationTaskUsingPost({ id: task.id, batchSize });
          message.success("任务同步请求已发送");
          // optional: refresh list/status
          fetchData();
          // clear selection for the task
          setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
          setSelectedRows((rows) => rows.filter((r) => r.id !== task.id));
        } catch (e) {
          console.error(e);
          message.error("同步失败，请稍后重试");
        }
      },
    });
  };

  const handleBatchSync = (batchSize: number = 50) => {
    if (!selectedRows || selectedRows.length === 0) return;
    Modal.confirm({
      title: `确认同步所选 ${selectedRows.length} 个标注任务吗？`,
      content: (
        <div>
          <div>标注工程中文件列表将与数据集保持一致，差异项将会被修正。</div>
          <div>标注工程中的标签与数据集中标签将进行合并，冲突项将以最新一次内容为准。</div>
        </div>
      ),
      okText: "同步",
      cancelText: "取消",
      onOk: async () => {
        try {
          await Promise.all(
            selectedRows.map((r) => syncAnnotationTaskUsingPost({ id: r.id, batchSize }))
          );
          message.success("批量同步请求已发送");
          fetchData();
          setSelectedRowKeys([]);
          setSelectedRows([]);
        } catch (e) {
          console.error(e);
          message.error("批量同步失败，请稍后重试");
        }
      },
    });
  };

  const handleBatchDelete = () => {
    if (!selectedRows || selectedRows.length === 0) return;
    Modal.confirm({
      title: `确认删除所选 ${selectedRows.length} 个标注任务吗？`,
      content: (
        <div>
          <div>删除标注任务不会删除对应数据集。</div>
          <div>如需保留当前标注结果，请在同步后再删除。</div>
        </div>
      ),
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await Promise.all(
            selectedRows.map((r) => deleteAnnotationTaskByIdUsingDelete({ m: r.id, proj: r.labelingProjId }))
          );
          message.success("批量删除已完成");
          fetchData();
          setSelectedRowKeys([]);
          setSelectedRows([]);
        } catch (e) {
          console.error(e);
          message.error("批量删除失败，请稍后重试");
        }
      },
    });
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

  const columns: ColumnType<any>[] = [
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
      render: (_: any, task: any) => (
        <div className="flex items-center justify-center space-x-1">
          {operations.map((operation) => (
            <Button
              key={operation.key}
              type="text"
              icon={operation.icon}
              onClick={() => (operation?.onClick as any)?.(task)}
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
        <div className="flex items-center space-x-2">
          {/* Batch action buttons - availability depends on selection count */}
          <div className="flex items-center space-x-1">
            <Button
              onClick={() => handleBatchSync(50)}
              disabled={selectedRowKeys.length === 0}
            >
              批量同步
            </Button>
            <Button
              danger
              onClick={handleBatchDelete}
              disabled={selectedRowKeys.length === 0}
            >
              批量删除
            </Button>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowCreateDialog(true)}
          >
            创建标注任务
          </Button>
        </div>
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
            rowKey="id"
            loading={loading}
            columns={columns}
            dataSource={tableData}
            pagination={pagination}
            rowSelection={{
              selectedRowKeys,
              onChange: (keys, rows) => {
                setSelectedRowKeys(keys as (string | number)[]);
                setSelectedRows(rows as any[]);
              },
            }}
            scroll={{ x: "max-content", y: "calc(100vh - 20rem)" }}
          />
        </Card>
      ) : (
        <CardView data={tableData} operations={operations as any} pagination={pagination} loading={loading} />
      )}
      <CreateAnnotationTask
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onRefresh={fetchData}
      />
    </div>
  );
}
