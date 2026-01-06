import { useState, useEffect } from "react";
import { Card, Button, Table, message, Modal, Tabs, Tag, Progress, Tooltip } from "antd";
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
  queryAutoAnnotationTasksUsingGet,
  deleteAutoAnnotationTaskByIdUsingDelete,
} from "../annotation.api";
import { mapAnnotationTask } from "../annotation.const";
import CreateAnnotationTask from "../Create/components/CreateAnnotationTaskDialog";
import { ColumnType } from "antd/es/table";
import { TemplateList } from "../Template";
// Note: DevelopmentInProgress intentionally not used here

const AUTO_STATUS_LABELS: Record<string, string> = {
  pending: "等待中",
  running: "处理中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

const AUTO_MODEL_SIZE_LABELS: Record<string, string> = {
  n: "YOLOv8n (最快)",
  s: "YOLOv8s",
  m: "YOLOv8m",
  l: "YOLOv8l (推荐)",
  x: "YOLOv8x (最精确)",
};

export default function DataAnnotation() {
  // return <DevelopmentInProgress showTime="2025.10.30" />;
  const [activeTab, setActiveTab] = useState("tasks");
  const [viewMode, setViewMode] = useState<"list" | "card">("list");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [autoTasks, setAutoTasks] = useState<any[]>([]);

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    fetchData,
    handleFiltersChange,
    handleKeywordChange,
  } = useFetchData(queryAnnotationTasksUsingGet, mapAnnotationTask, 30000, true, [], 0);

  const [labelStudioBase, setLabelStudioBase] = useState<string | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<(string | number)[]>([]);
  const [selectedRows, setSelectedRows] = useState<any[]>([]);

  // 拉取自动标注任务（供轮询和创建成功后立即刷新复用）
  const refreshAutoTasks = async (silent = false) => {
    try {
      const response = await queryAutoAnnotationTasksUsingGet();
      const tasks = (response as any)?.data || response || [];
      if (Array.isArray(tasks)) {
        setAutoTasks(tasks);
      }
    } catch (error) {
      console.error("Failed to fetch auto annotation tasks:", error);
      if (!silent) {
        message.error("获取自动标注任务失败");
      }
    }
  };

  // prefetch config on mount so clicking annotate is fast and we know whether base URL exists
  // useEffect ensures this runs once
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const baseUrl = `http://${window.location.hostname}:${parseInt(window.location.port) + 1}`;
        if (mounted) setLabelStudioBase(baseUrl);
      } catch (e) {
        if (mounted) setLabelStudioBase(null);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // 自动标注任务轮询（用于在同一表格中展示处理进度）
  useEffect(() => {
    refreshAutoTasks();
    const timer = setInterval(() => refreshAutoTasks(true), 3000);

    return () => {
      clearInterval(timer);
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
          await deleteAnnotationTaskByIdUsingDelete(task.id);
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

  const handleDeleteAuto = (task: any) => {
    Modal.confirm({
      title: `确认删除自动标注任务「${task.name}」吗？`,
      content: <div>删除任务后，已生成的标注结果不会被删除。</div>,
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await deleteAutoAnnotationTaskByIdUsingDelete(task.id);
          message.success("自动标注任务删除成功");
          // 重新拉取自动标注任务
          setAutoTasks((prev) => prev.filter((t: any) => t.id !== task.id));
          // 清理选中
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
    const manualRows = selectedRows.filter((r) => r._kind !== "auto");
    if (manualRows.length === 0) {
      message.warning("请选择手动标注任务进行同步");
      return;
    }
    Modal.confirm({
      title: `确认同步所选 ${manualRows.length} 个标注任务吗？`,
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
            manualRows.map((r) => syncAnnotationTaskUsingPost({ id: r.id, batchSize }))
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
    const manualRows = selectedRows.filter((r) => r._kind !== "auto");
    const autoRows = selectedRows.filter((r) => r._kind === "auto");
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
            [
              ...manualRows.map((r) => deleteAnnotationTaskByIdUsingDelete(r.id)),
              ...autoRows.map((r) => deleteAutoAnnotationTaskByIdUsingDelete(r.id)),
            ]
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
  // 合并手动标注任务与自动标注任务
  const mergedTableData = [
    // 手动标注任务
    ...tableData.map((task) => ({
      ...task,
      _kind: "manual" as const,
    })),
    // 自动标注任务
    ...autoTasks.map((task: any) => {
      const sourceList = Array.isArray(task.sourceDatasets)
        ? task.sourceDatasets
        : task.datasetName
        ? [task.datasetName]
        : [];
      const datasetName = sourceList.length > 0 ? sourceList.join("，") : "-";

      return {
        id: task.id,
        name: task.name,
        datasetName,
        createdAt: task.createdAt || "-",
        updatedAt: task.updatedAt || "-",
        _kind: "auto" as const,
        autoStatus: task.status,
        autoProgress: task.progress,
        autoProcessedImages: task.processedImages,
        autoTotalImages: task.totalImages,
        autoDetectedObjects: task.detectedObjects,
        autoConfig: task.config || {},
      };
    }),
  ];

  const columns: ColumnType<any>[] = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      fixed: "left" as const,
    },
    {
      title: "类型",
      key: "kind",
      width: 100,
      render: (_: any, record: any) =>
        record._kind === "auto" ? "自动标注" : "手动标注",
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
      title: "模型",
      key: "modelSize",
      width: 160,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const size = record.autoConfig?.modelSize;
        return AUTO_MODEL_SIZE_LABELS[size] || size || "-";
      },
    },
    {
      title: "置信度",
      key: "confThreshold",
      width: 120,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const threshold = record.autoConfig?.confThreshold;
        if (typeof threshold !== "number") return "-";
        return `${(threshold * 100).toFixed(0)}%`;
      },
    },
    {
      title: "目标类别",
      key: "targetClasses",
      width: 160,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const classes: number[] = record.autoConfig?.targetClasses || [];
        if (!classes.length) return "全部类别";
        const text = classes.join(", ");
        return (
          <Tooltip title={text}>
            <span>{`${classes.length} 个类别`}</span>
          </Tooltip>
        );
      },
    },
    {
      title: "自动标注状态",
      key: "autoStatus",
      width: 130,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const status = record.autoStatus as string;
        const label = AUTO_STATUS_LABELS[status] || status || "-";
        return <Tag>{label}</Tag>;
      },
    },
    {
      title: "自动标注进度",
      key: "autoProgress",
      width: 200,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const progress = typeof record.autoProgress === "number" ? record.autoProgress : 0;
        const processed = record.autoProcessedImages ?? 0;
        const total = record.autoTotalImages ?? 0;
        return (
          <div>
            <Progress percent={progress} size="small" />
            <div style={{ fontSize: 12, color: "#999" }}>
              {processed} / {total}
            </div>
          </div>
        );
      },
    },
    {
      title: "检测对象数",
      key: "detectedObjects",
      width: 120,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const count = record.autoDetectedObjects;
        if (typeof count !== "number") return "-";
        try {
          return count.toLocaleString();
        } catch {
          return String(count);
        }
      },
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
          {task._kind === "manual" &&
            operations.map((operation) => (
              <Button
                key={operation.key}
                type="text"
                icon={operation.icon}
                onClick={() => (operation?.onClick as any)?.(task)}
                title={operation.label}
              />
            ))}
          {task._kind === "auto" && (
            <Button
              type="text"
              icon={<DeleteOutlined style={{ color: "#f5222d" }} />}
              onClick={() => handleDeleteAuto(task)}
              title="删除自动标注任务"
            />
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">数据标注</h1>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: "tasks",
            label: "标注任务",
            children: (
              <div className="flex flex-col gap-4">
                {/* Search, Filters and Buttons in one row */}
                <div className="flex items-center justify-between gap-2">
                  {/* Left side: Search and view controls */}
                  <div className="flex items-center gap-2">
                    <SearchControls
                      searchTerm={searchParams.keyword}
                      onSearchChange={handleKeywordChange}
                      searchPlaceholder="搜索任务名称、描述"
                      onFiltersChange={handleFiltersChange}
                      viewMode={viewMode}
                      onViewModeChange={setViewMode}
                      showViewToggle={true}
                      onReload={fetchData}
                    />
                  </div>

                  {/* Right side: All action buttons */}
                  <div className="flex items-center gap-2">
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
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setShowCreateDialog(true)}
                    >
                      创建标注任务
                    </Button>
                  </div>
                </div>

                {/* Task List/Card */}
                {viewMode === "list" ? (
                  <Card>
                    <Table
                      key="id"
                      rowKey="id"
                      loading={loading}
                      columns={columns}
                      dataSource={mergedTableData}
                      pagination={pagination}
                      rowSelection={{
                        selectedRowKeys,
                        onChange: (keys, rows) => {
                          setSelectedRowKeys(keys as (string | number)[]);
                          setSelectedRows(rows as any[]);
                        },
                      }}
                      scroll={{ x: "max-content", y: "calc(100vh - 24rem)" }}
                    />
                  </Card>
                ) : (
                  <CardView
                    data={tableData}
                    operations={operations as any}
                    pagination={pagination}
                    loading={loading}
                  />
                )}

                <CreateAnnotationTask
                  open={showCreateDialog}
                  onClose={() => setShowCreateDialog(false)}
                  onRefresh={(mode?: any) => {
                    // 手动标注创建成功后刷新标注任务列表
                    fetchData();
                    // 自动标注创建成功后立即刷新自动标注任务列表
                    if (mode === "auto") {
                      refreshAutoTasks(true);
                    }
                  }}
                />
              </div>
            ),
          },
          {
            key: "templates",
            label: "标注模板",
            children: <TemplateList />,
          },
        ]}
      />
    </div>
  );
}
