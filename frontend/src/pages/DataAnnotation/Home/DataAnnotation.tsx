import { useState, useEffect } from "react";
import { Card, Button, Table, message, Modal, Tabs, Tag, Progress, Tooltip, Dropdown } from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SyncOutlined,
  MoreOutlined,
  SettingOutlined,
  ExportOutlined,
  ImportOutlined,
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
  getAutoAnnotationLabelStudioProjectUsingGet,
  loginAnnotationUsingGet,
  syncManualAnnotationToDatabaseUsingPost,
  syncAutoAnnotationToDatabaseUsingPost,
} from "../annotation.api";
import { mapAnnotationTask } from "../annotation.const";
import CreateAnnotationTask from "../Create/components/CreateAnnotationTaskDialog";
import { ColumnType } from "antd/es/table";
import { TemplateList } from "../Template";
import EditAutoAnnotationDatasetDialog from "../AutoAnnotation/components/EditAutoAnnotationDatasetDialog";
import ImportFromLabelStudioDialog from "../AutoAnnotation/components/ImportFromLabelStudioDialog";
import ManualImportFromLabelStudioDialog from "../ManualImportFromLabelStudioDialog";
import EditManualAnnotationDatasetDialog from "../EditManualAnnotationDatasetDialog";
import { useTranslation } from "react-i18next";
// Note: DevelopmentInProgress intentionally not used here

export default function DataAnnotation() {
  const { t } = useTranslation();
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
  } = useFetchData(queryAnnotationTasksUsingGet, (item) => mapAnnotationTask(item, t), 30000, true, [], 0);

  const [labelStudioBase, setLabelStudioBase] = useState<string | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<(string | number)[]>([]);
  const [selectedRows, setSelectedRows] = useState<any[]>([]);
  const [datasetProjectMap, setDatasetProjectMap] = useState<Record<string, string>>({});
  const [editingAutoTask, setEditingAutoTask] = useState<any | null>(null);
  const [showEditAutoDatasetDialog, setShowEditAutoDatasetDialog] = useState(false);
  const [editingManualTask, setEditingManualTask] = useState<AnnotationTask | null>(null);
  const [showEditManualDatasetDialog, setShowEditManualDatasetDialog] = useState(false);
  const [importingAutoTask, setImportingAutoTask] = useState<any | null>(null);
  const [showImportAutoDialog, setShowImportAutoDialog] = useState(false);
  const [importingManualTask, setImportingManualTask] = useState<AnnotationTask | null>(null);
  const [showImportManualDialog, setShowImportManualDialog] = useState(false);

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
        message.error(t('dataAnnotation.home.messages.fetchAutoTasksFailed'));
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

  // 基于手动标注任务构建 datasetId -> Label Studio project 映射，供自动标注跳转使用
  useEffect(() => {
    const map: Record<string, string> = {};
    (tableData as any[]).forEach((task: any) => {
      const datasetId = task.datasetId || task.dataset_id;
      const projId = task.labelingProjId || task.projId || task.labeling_project_id;
      if (datasetId && projId) {
        map[String(datasetId)] = String(projId);
      }
    });
    setDatasetProjectMap(map);
  }, [tableData]);

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
        await loginAnnotationUsingGet(labelingProjId)
        if (labelingProjId) {
          // only open external Label Studio when we have a configured base url
          if (base) {
            const target = `${base}/projects/${labelingProjId}/data`;
            window.open(target, "_blank");
        } else {
          // no external Label Studio URL configured — do not perform internal redirect in this version
          message.error(t('dataAnnotation.home.messages.cannotJumpNoBase'));
          return;
        }
      } else {
        // no labeling project id available — do not attempt internal redirect in this version
        message.error(t('dataAnnotation.home.messages.cannotJumpNoMapping'));
        return;
      }
    } catch (error) {
      // on error, surface a user-friendly message instead of redirecting
      message.error(t('dataAnnotation.home.messages.cannotJumpError'));
      return;
      }
    })();
  };

  const handleDelete = (task: AnnotationTask) => {
    Modal.confirm({
      title: t('dataAnnotation.home.confirm.deleteTaskTitle', { name: task.name }),
      content: (
        <div>
          <div>{t('dataAnnotation.home.confirm.deleteTaskContent1')}</div>
          <div>{t('dataAnnotation.home.confirm.deleteTaskContent2')}</div>
        </div>
      ),
      okText: t('dataAnnotation.home.confirm.deleteOkText'),
      okType: "danger",
      cancelText: t('dataAnnotation.home.confirm.deleteCancelText'),
      onOk: async () => {
        try {
          await deleteAnnotationTaskByIdUsingDelete(task.id);
          message.success(t('dataAnnotation.home.messages.deleteSuccess'));
          fetchData();
          // clear selection if deleted item was selected
          setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
          setSelectedRows((rows) => rows.filter((r) => r.id !== task.id));
        } catch (e) {
          console.error(e);
          message.error(t('dataAnnotation.home.messages.deleteFailed'));
        }
      },
    });
  };

  const handleDeleteAuto = (task: any) => {
    Modal.confirm({
      title: t('dataAnnotation.home.confirm.deleteAutoTaskTitle', { name: task.name }),
      content: <div>{t('dataAnnotation.home.confirm.deleteAutoTaskContent')}</div>,
      okText: t('dataAnnotation.home.confirm.deleteOkText'),
      okType: "danger",
      cancelText: t('dataAnnotation.home.confirm.deleteCancelText'),
      onOk: async () => {
        try {
          await deleteAutoAnnotationTaskByIdUsingDelete(task.id);
          message.success(t('dataAnnotation.home.messages.autoTaskDeleteSuccess'));
          // 重新拉取自动标注任务
          setAutoTasks((prev) => prev.filter((t: any) => t.id !== task.id));
          // 清理选中
          setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
          setSelectedRows((rows) => rows.filter((r) => r.id !== task.id));
        } catch (e) {
          console.error(e);
          message.error(t('dataAnnotation.home.messages.deleteFailed'));
        }
      },
    });
  };

  const handleEditAutoTaskDataset = (row: any) => {
    if (!row?.id) {
      message.error(t('dataAnnotation.home.messages.autoTaskNotFound'));
      return;
    }

    const full = autoTasks.find((t: any) => t.id === row.id);
    if (!full) {
      message.error(t('dataAnnotation.home.messages.autoTaskNotFound') + t('dataAnnotation.home.messages.deleteFailed').split('，')[1]);
      return;
    }

    setEditingAutoTask(full);
    setShowEditAutoDatasetDialog(true);
  };

  const handleEditManualTaskDataset = (task: AnnotationTask) => {
    if (!task?.id) {
      message.error(t('dataAnnotation.home.messages.taskNotFound'));
      return;
    }
    setEditingManualTask(task);
    setShowEditManualDatasetDialog(true);
  };

  const handleImportManualFromLabelStudio = (task: AnnotationTask) => {
    if (!task?.id) {
      message.error(t('dataAnnotation.home.messages.taskNotFound'));
      return;
    }

    setImportingManualTask(task);
    setShowImportManualDialog(true);
  };

  const handleSyncManualToDatabase = async (task: AnnotationTask) => {
    if (!task?.id) {
      message.error(t('dataAnnotation.home.messages.taskNotFound'));
      return;
    }

    Modal.confirm({
      title: t('dataAnnotation.home.messages.syncToDbTitle', { name: task.name }),
      content: (
        <div>
          <div>{t('dataAnnotation.home.messages.syncToDbContent1')}</div>
          <div>{t('dataAnnotation.home.messages.syncToDbContent2')}</div>
        </div>
      ),
      okText: t('dataAnnotation.home.actions.syncToDb'),
      cancelText: t('dataAnnotation.home.confirm.deleteCancelText'),
      onOk: async () => {
        const hide = message.loading(t('dataAnnotation.dialogs.syncToDb.loading'), 0);
        try {
          await syncManualAnnotationToDatabaseUsingPost(task.id as any);
          hide();
          message.success(t('dataAnnotation.dialogs.syncToDb.success'));
        } catch (e) {
          console.error(e);
          hide();
          message.error(t('dataAnnotation.dialogs.syncToDb.fail'));
        }
      },
    });
  };

  const handleImportAutoFromLabelStudio = (row: any) => {
    if (!row?.id) {
      message.error(t('dataAnnotation.home.messages.autoTaskNotFound'));
      return;
    }

    const full = autoTasks.find((t: any) => t.id === row.id);
    if (!full) {
      message.error(t('dataAnnotation.home.messages.autoTaskNotFound') + t('dataAnnotation.home.messages.deleteFailed').split('，')[1]);
      return;
    }

    setImportingAutoTask(full);
    setShowImportAutoDialog(true);
  };

  const handleSyncAutoToDatabase = (row: any) => {
    if (!row?.id) {
      message.error(t('dataAnnotation.home.messages.autoTaskNotFound'));
      return;
    }

    Modal.confirm({
      title: t('dataAnnotation.home.messages.syncToDbTitle', { name: row.name }),
      content: (
        <div>
          <div>{t('dataAnnotation.home.messages.syncToDbContent1')}</div>
          <div>{t('dataAnnotation.home.messages.syncToDbContent2')}</div>
        </div>
      ),
      okText: t('dataAnnotation.home.actions.syncToDb'),
      cancelText: t('dataAnnotation.home.confirm.deleteCancelText'),
      onOk: async () => {
        const hide = message.loading(t('dataAnnotation.dialogs.syncToDb.loading'), 0);
        try {
          await syncAutoAnnotationToDatabaseUsingPost(row.id);
          hide();
          message.success(t('dataAnnotation.dialogs.syncToDb.success'));
        } catch (e) {
          console.error(e);
          hide();
          message.error(t('dataAnnotation.dialogs.syncToDb.fail'));
        }
      },
    });
  };

  const handleAnnotateAuto = (task: any) => {
    (async () => {
      try {
        if (!labelStudioBase) {
          message.error(t('dataAnnotation.home.messages.cannotJumpNoBase'));
          return;
        }

        let projId: string | undefined;

        try {
          const resp = await getAutoAnnotationLabelStudioProjectUsingGet(task.id);
          const data = (resp as any)?.data ?? resp;
          projId = data?.projectId || data?.labeling_project_id;
        } catch (e) {
          console.error("Failed to resolve LS project for auto task", e);
        }

        // 兼容旧逻辑：若后端未能找到专属项目，则回退到按数据集映射跳转
        if (!projId) {
          const datasetId = task.datasetId;
          if (!datasetId) {
            message.error(t('dataAnnotation.home.messages.cannotJumpAutoNoDataset'));
            return;
          }

          projId = datasetProjectMap[String(datasetId)];
        }

        if (!projId) {
          message.error(t('dataAnnotation.home.messages.cannotJumpAutoNoProject'));
          return;
        }

        const target = `${labelStudioBase}/projects/${projId}/data`;
        window.open(target, "_blank");
      } catch (error) {
        console.error(error);
        message.error(t('dataAnnotation.home.messages.cannotJumpError'));
      }
    })();
  };

  const handleSync = (task: AnnotationTask, batchSize: number = 50) => {
    Modal.confirm({
      title: t('dataAnnotation.home.confirm.syncTitle', { name: task.name }),
      content: (
        <div>
          <div>{t('dataAnnotation.home.confirm.syncContent1')}</div>
          <div>{t('dataAnnotation.home.confirm.syncContent2')}</div>
        </div>
      ),
      okText: t('dataAnnotation.home.confirm.syncOkText'),
      cancelText: t('dataAnnotation.home.confirm.syncCancelText'),
      onOk: async () => {
        try {
          await syncAnnotationTaskUsingPost({ id: task.id, batchSize });
          message.success(t('dataAnnotation.home.messages.syncRequestSent'));
          // optional: refresh list/status
          fetchData();
          // clear selection for the task
          setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
          setSelectedRows((rows) => rows.filter((r) => r.id !== task.id));
        } catch (e) {
          console.error(e);
          message.error(t('dataAnnotation.home.messages.syncFailed'));
        }
      },
    });
  };

  const handleBatchSync = (batchSize: number = 50) => {
    if (!selectedRows || selectedRows.length === 0) return;
    const manualRows = selectedRows.filter((r) => r._kind !== "auto");
    if (manualRows.length === 0) {
      message.warning(t('dataAnnotation.home.messages.batchSyncManualOnly'));
      return;
    }
    Modal.confirm({
      title: t('dataAnnotation.home.confirm.batchSyncTitle', { count: manualRows.length }),
      content: (
        <div>
          <div>{t('dataAnnotation.home.confirm.syncContent1')}</div>
          <div>{t('dataAnnotation.home.confirm.syncContent2')}</div>
        </div>
      ),
      okText: t('dataAnnotation.home.confirm.syncOkText'),
      cancelText: t('dataAnnotation.home.confirm.syncCancelText'),
      onOk: async () => {
        try {
          await Promise.all(
            manualRows.map((r) => syncAnnotationTaskUsingPost({ id: r.id, batchSize }))
          );
          message.success(t('dataAnnotation.home.messages.batchSyncSuccess'));
          fetchData();
          setSelectedRowKeys([]);
          setSelectedRows([]);
        } catch (e) {
          console.error(e);
          message.error(t('dataAnnotation.home.messages.batchSyncFailed'));
        }
      },
    });
  };

  const handleBatchDelete = () => {
    if (!selectedRows || selectedRows.length === 0) return;
    const manualRows = selectedRows.filter((r) => r._kind !== "auto");
    const autoRows = selectedRows.filter((r) => r._kind === "auto");
    Modal.confirm({
      title: t('dataAnnotation.home.confirm.batchDeleteTitle', { count: selectedRows.length }),
      content: (
        <div>
          <div>{t('dataAnnotation.home.confirm.deleteTaskContent1')}</div>
          <div>{t('dataAnnotation.home.confirm.deleteTaskContent2')}</div>
        </div>
      ),
      okText: t('dataAnnotation.home.confirm.deleteOkText'),
      okType: "danger",
      cancelText: t('dataAnnotation.home.confirm.deleteCancelText'),
      onOk: async () => {
        try {
          await Promise.all(
            [
              ...manualRows.map((r) => deleteAnnotationTaskByIdUsingDelete(r.id)),
              ...autoRows.map((r) => deleteAutoAnnotationTaskByIdUsingDelete(r.id)),
            ]
          );
          message.success(t('dataAnnotation.home.messages.batchDeleteSuccess'));
          fetchData();
          setSelectedRowKeys([]);
          setSelectedRows([]);
        } catch (e) {
          console.error(e);
          message.error(t('dataAnnotation.home.messages.batchDeleteFailed'));
        }
      },
    });
  };

  const operations = [
    {
      key: "annotate",
      label: t('dataAnnotation.home.actions.annotate'),
      icon: (
        <EditOutlined
          className="w-4 h-4 text-green-400"
          style={{ color: "#52c41a" }}
        />
      ),
      onClick: handleAnnotate,
    },
    {
      key: "sync-db",
      label: t('dataAnnotation.home.actions.syncToDb'),
      icon: <SyncOutlined className="w-4 h-4" style={{ color: "#1890ff" }} />,
      onClick: handleSyncManualToDatabase,
    },
    {
      key: "export-result",
      label: t('dataAnnotation.home.actions.exportResult'),
      icon: <ExportOutlined className="w-4 h-4" />, // 导出/下载类图标
      onClick: handleImportManualFromLabelStudio,
    },
    {
      key: "delete",
      label: t('dataAnnotation.home.actions.delete'),
      icon: <DeleteOutlined style={{ color: "#f5222d" }} />,
      onClick: handleDelete,
    },
  ];
  // 合并手动标注任务与自动标注任务
  // 对于由自动标注逻辑内部创建的 Label Studio 映射（名称以 " - 自动标注" 结尾），
  // 仅用于 datasetId -> projectId 映射，不在列表中单独展示，避免给人“多了一条手动任务”的感觉。
  const manualVisibleTasks = tableData.filter((task: any) => {
    const name = (task as any)?.name;
    if (typeof name !== "string") return true;
    return !name.endsWith(" - 自动标注");
  });

  const mergedTableData = [
    // 手动标注任务（过滤掉自动生成的映射任务）
    ...manualVisibleTasks.map((task) => ({
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
        datasetId: task.datasetId || task.dataset_id,
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
      title: t('dataAnnotation.home.columns.taskName'),
      dataIndex: "name",
      key: "name",
      fixed: "left" as const,
    },
    {
      title: t('dataAnnotation.home.columns.type'),
      key: "kind",
      width: 100,
      render: (_: any, record: any) =>
        record._kind === "auto" ? t('dataAnnotation.home.autoAnnotation') : t('dataAnnotation.home.manualAnnotation'),
    },
    {
      title: t('dataAnnotation.home.columns.taskId'),
      dataIndex: "id",
      key: "id",
    },
    {
      title: t('dataAnnotation.home.columns.dataset'),
      dataIndex: "datasetName",
      key: "datasetName",
      width: 180,
    },
    {
      title: t('dataAnnotation.home.columns.model'),
      key: "modelSize",
      width: 160,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const size = record.autoConfig?.modelSize;
        return t(`dataAnnotation.home.autoModelSizeLabels.${size}`) || size || "-";
      },
    },
    {
      title: t('dataAnnotation.home.columns.confidence'),
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
      title: t('dataAnnotation.home.columns.targetClasses'),
      key: "targetClasses",
      width: 160,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const classes: number[] = record.autoConfig?.targetClasses || [];
        if (!classes.length) return t('dataAnnotation.home.allCategories');
        const text = classes.join(", ");
        return (
          <Tooltip title={text}>
            <span>{t('dataAnnotation.home.categoriesCount', { count: classes.length })}</span>
          </Tooltip>
        );
      },
    },
    {
      title: t('dataAnnotation.home.columns.autoStatus'),
      key: "autoStatus",
      width: 130,
      render: (_: any, record: any) => {
        if (record._kind !== "auto") return "-";
        const status = record.autoStatus as string;
        const label = t(`dataAnnotation.home.autoStatusLabels.${status}`) || status || "-";
        return <Tag>{label}</Tag>;
      },
    },
    {
      title: t('dataAnnotation.home.columns.autoProgress'),
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
      title: t('dataAnnotation.home.columns.detectedObjects'),
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
      title: t('dataAnnotation.home.columns.createdAt'),
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
    },
    {
      title: t('dataAnnotation.home.columns.updatedAt'),
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 180,
    },
    {
      title: t('dataAnnotation.home.columns.actions'),
      key: "actions",
      fixed: "right" as const,
      width: 260,
      dataIndex: "actions",
      render: (_: any, task: any) => (
        <div className="flex items-center justify-center space-x-1">
          {task._kind === "manual" && (
            <>
              <Button
                type="text"
                icon={<EditOutlined style={{ color: "#52c41a" }} />}
                onClick={() => handleAnnotate(task)}
                title={t('dataAnnotation.home.actions.annotate')}
              >
                {t('dataAnnotation.home.actions.edit')}
              </Button>
              <Button
                type="text"
                icon={<SyncOutlined style={{ color: "#1890ff" }} />}
                onClick={() => handleSyncManualToDatabase(task)}
                title={t('dataAnnotation.home.actions.syncToDb')}
              >
                {t('dataAnnotation.home.actions.syncToDb')}
              </Button>

              <Dropdown
                menu={{
                  items: [
                    {
                      key: "export-result",
                      label: t('dataAnnotation.home.actions.exportResult'),
                      icon: <ExportOutlined />,
                      onClick: () => handleImportManualFromLabelStudio(task),
                    },
                    {
                      key: "edit-dataset",
                      label: t('dataAnnotation.home.editDataset'),
                      icon: <SettingOutlined />,
                      onClick: () => handleEditManualTaskDataset(task),
                    },
                    {
                      key: "delete",
                      label: t('dataAnnotation.home.actions.delete'),
                      icon: <DeleteOutlined />,
                      danger: true,
                      onClick: () => handleDelete(task),
                    },
                  ],
                }}
                trigger={["click"]}
              >
                <Button type="text" icon={<MoreOutlined />} title={t('dataAnnotation.home.actions.moreActions')} />
              </Dropdown>
            </>
          )}
          {task._kind === "auto" && (
            <>
              <Button
                type="text"
                icon={<EditOutlined style={{ color: "#52c41a" }} />}
                onClick={() => handleAnnotateAuto(task)}
                title={t('dataAnnotation.home.actions.annotate')}
              >
                {t('dataAnnotation.home.actions.edit')}
              </Button>

              <Button
                type="text"
                icon={<SyncOutlined style={{ color: "#1890ff" }} />}
                onClick={() => handleSyncAutoToDatabase(task)}
                title={t('dataAnnotation.home.actions.syncToDb')}
              >
                {t('dataAnnotation.home.actions.syncToDb')}
              </Button>

              {/* 二级功能：编辑任务数据集 + 删除任务（折叠菜单） */}
              <Dropdown
                menu={{
                  items: [
                    {
                      key: "export-result",
                      label: t('dataAnnotation.home.actions.exportResult'),
                      icon: <ExportOutlined />,
                      onClick: () => handleImportAutoFromLabelStudio(task),
                    },
                    {
                      key: "edit-dataset",
                      label: t('dataAnnotation.home.editDataset'),
                      icon: <SettingOutlined />,
                      onClick: () => handleEditAutoTaskDataset(task),
                    },
                    {
                      key: "delete",
                      label: t('dataAnnotation.home.actions.delete'),
                      icon: <DeleteOutlined />,
                      danger: true,
                      onClick: () => handleDeleteAuto(task),
                    },
                  ],
                }}
                trigger={["click"]}
              >
                <Button
                  type="text"
                  icon={<MoreOutlined />}
                  title={t('dataAnnotation.home.actions.moreActions')}
                />
              </Dropdown>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t('dataAnnotation.home.title')}</h1>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: "tasks",
            label: t('dataAnnotation.home.tabs.tasks'),
            children: (
              <div className="flex flex-col gap-4">
                {/* Search, Filters and Buttons in one row */}
                <div className="flex items-center justify-between gap-2">
                  {/* Left side: Search and view controls */}
                  <div className="flex items-center gap-2">
                    <SearchControls
                      searchTerm={searchParams.keyword}
                      onSearchChange={handleKeywordChange}
                      searchPlaceholder={t('dataAnnotation.home.searchPlaceholder')}
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
                      {t('dataAnnotation.home.batchSync')}
                    </Button>
                    <Button
                      danger
                      onClick={handleBatchDelete}
                      disabled={selectedRowKeys.length === 0}
                    >
                      {t('dataAnnotation.home.batchDelete')}
                    </Button>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setShowCreateDialog(true)}
                    >
                      {t('dataAnnotation.home.createTask')}
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
            label: t('dataAnnotation.home.tabs.templates'),
            children: <TemplateList />,
          },
        ]}
      />

      {editingAutoTask && (
        <EditAutoAnnotationDatasetDialog
          visible={showEditAutoDatasetDialog}
          task={editingAutoTask}
          onCancel={() => {
            setShowEditAutoDatasetDialog(false);
            setEditingAutoTask(null);
          }}
          onSuccess={() => {
            setShowEditAutoDatasetDialog(false);
            setEditingAutoTask(null);
            refreshAutoTasks();
          }}
        />
      )}

      {editingManualTask && (
        <EditManualAnnotationDatasetDialog
          visible={showEditManualDatasetDialog}
          task={editingManualTask}
          onCancel={() => {
            setShowEditManualDatasetDialog(false);
            setEditingManualTask(null);
          }}
          onSuccess={() => {
            setShowEditManualDatasetDialog(false);
            setEditingManualTask(null);
          }}
        />
      )}

      {importingManualTask && (
        <ManualImportFromLabelStudioDialog
          visible={showImportManualDialog}
          task={importingManualTask}
          onCancel={() => {
            setShowImportManualDialog(false);
            setImportingManualTask(null);
          }}
          onSuccess={() => {
            setShowImportManualDialog(false);
            setImportingManualTask(null);
          }}
        />
      )}

      {importingAutoTask && (
        <ImportFromLabelStudioDialog
          visible={showImportAutoDialog}
          // 这里直接透传自动标注任务结构（与 AutoAnnotation 页面保持一致字段）
          task={importingAutoTask as any}
          onCancel={() => {
            setShowImportAutoDialog(false);
            setImportingAutoTask(null);
          }}
          onSuccess={() => {
            setShowImportAutoDialog(false);
            setImportingAutoTask(null);
          }}
        />
      )}
    </div>
  );
}
