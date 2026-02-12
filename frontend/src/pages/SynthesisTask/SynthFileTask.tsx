import { App } from "antd";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import { Badge, Breadcrumb, Button, Table, Tabs, Progress, Tooltip } from "antd";
import type { BadgeProps } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import { useTranslation } from "react-i18next";

import DetailHeader from "@/components/DetailHeader";
import {
  querySynthesisFileTasksUsingGet,
  querySynthesisTaskByIdUsingGet,
  deleteSynthesisTaskByIdUsingDelete,
} from "@/pages/SynthesisTask/synthesis-api";
import { formatDateTime } from "@/utils/unit";
import { Folder, Sparkles, Trash2 } from "lucide-react";

interface SynthesisFileTaskItem {
  id: string;
  synthesis_instance_id: string;
  file_name: string;
  source_file_id: string;
  target_file_location: string;
  status?: string;
  total_chunks: number;
  processed_chunks: number;
  created_at?: string;
  updated_at?: string;
}

interface PagedResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  page: number;
  size: number;
}

interface SynthesisTaskInfo {
  id: string;
  name: string;
  synthesis_type: string;
  status: string;
  created_at: string;
  updated_at?: string;
  model_id: string;
  total_files?: number;
  total_synthesis_data?: number;
  description?: string;
}

export default function SynthFileTask() {
  const { t } = useTranslation();
  const { id: taskId = "" } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SynthesisFileTaskItem[]>([]);
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [taskInfo, setTaskInfo] = useState<SynthesisTaskInfo | null>(null);
  const [activeTab, setActiveTab] = useState("files");

  // 查询总任务详情
  const fetchTaskDetail = async () => {
    if (!taskId) return;
    try {
      const res = await querySynthesisTaskByIdUsingGet(taskId);
      const raw = res?.data?.data ?? res?.data;
      if (!raw) return;
      setTaskInfo(raw);
    } catch {
      message.error(t('synthesisTask.fileTask.messages.fetchFailed'));
      navigate("/data/synthesis/task");
    }
  };

  useEffect(() => {
    fetchTaskDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const fetchData = async (page = 1, pageSize = 10, withTopLoading = false) => {
    if (!taskId) return;

    if (withTopLoading) {
      window.dispatchEvent(new Event("loading:show"));
    }

    setLoading(true);
    try {
      const res = await querySynthesisFileTasksUsingGet(taskId, {
        page,
        page_size: pageSize,
      });
      const payload: PagedResponse<SynthesisFileTaskItem> =
        res?.data?.data ?? res?.data ?? {
          content: [],
          totalElements: 0,
          totalPages: 0,
          page,
          size: pageSize,
        };
      setData(payload.content || []);
      setPagination({
        current: payload.page ?? page,
        pageSize: payload.size ?? pageSize,
        total: payload.totalElements ?? payload.content?.length ?? 0,
      });
    } finally {
      setLoading(false);
      if (withTopLoading) {
        window.dispatchEvent(new Event("loading:hide"));
      }
    }
  };

  useEffect(() => {
    // 首次进入或任务切换时，不触发顶部 loading，只用表格自带的 loading
    fetchData(1, pagination.pageSize || 10, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const handleTableChange = (pag: TablePaginationConfig) => {
    // 分页切换时，也只用表格 loading，不闪顶部条
    fetchData(pag.current || 1, pag.pageSize || 10, false);
  };

  const columns: ColumnsType<SynthesisFileTaskItem> = [
    {
      title: t('synthesisTask.fileTask.columns.file'),
      key: "file",
      render: (_text, record) => (
        <div className="flex items-center gap-2">
          <Folder className="w-4 h-4 text-blue-500" />
          <Button
            type="link"
            onClick={() =>
              navigate(`/data/synthesis/task/file/${record.id}/detail`, {
                state: { fileName: record.file_name, taskId },
              })
            }
          >
            {record.file_name}
          </Button>
        </div>
      ),
    },
    {
      title: t('synthesisTask.fileTask.columns.status'),
      dataIndex: "status",
      key: "status",
      render: (status?: string) => {
        let badgeStatus: BadgeProps["status"] = "default";
        let text = status || t('synthesisTask.fileTask.status.unknown');
        if (status === "pending" || status === "PROCESSING" || status === "processing") {
          badgeStatus = "processing";
          text = t('synthesisTask.fileTask.status.processing');
        } else if (status === "COMPLETED" || status === "completed") {
          badgeStatus = "success";
          text = t('synthesisTask.fileTask.status.completed');
        } else if (status === "FAILED" || status === "failed") {
          badgeStatus = "error";
          text = t('synthesisTask.fileTask.status.failed');
        }
        return <Badge status={badgeStatus} text={text} />;
      },
    },
    {
      title: t('synthesisTask.fileTask.columns.totalChunks'),
      dataIndex: "total_chunks",
      key: "total_chunks",
    },
    {
      title: t('synthesisTask.fileTask.columns.progress'),
      key: "progress",
      render: (_text, record) => {
        const total = record.total_chunks || 0;
        const processed = record.processed_chunks || 0;
        const percent = total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : 0;
        return (
          <div style={{ minWidth: 160 }}>
            <Progress
              percent={percent}
              size="small"
              status={percent === 100 ? "success" : undefined}
              format={() => `${processed}/${total}`}
            />
          </div>
        );
      },
    },
    {
      title: t('synthesisTask.fileTask.columns.createdAt'),
      dataIndex: "created_at",
      key: "created_at",
      render: (val?: string) => (val ? formatDateTime(val) : "-"),
    },
    {
      title: t('synthesisTask.fileTask.columns.updatedAt'),
      dataIndex: "updated_at",
      key: "updated_at",
      render: (val?: string) => (val ? formatDateTime(val) : "-"),
    },
    {
      title: t('synthesisTask.fileTask.columns.actions'),
      key: "actions",
      render: () => (
        <Tooltip title={t('synthesisTask.fileTask.operations.delete')}>
          <Button
            type="text"
            danger
            disabled
            icon={<Trash2 className="w-4 h-4" />}
          />
        </Tooltip>
      ),
    },
  ];

  const handleRefresh = async () => {
    // 刷新按钮：明确触发一次顶部 loading，让用户看到“闪一下”的效果
    window.dispatchEvent(new Event("loading:show"));
    try {
      await fetchTaskDetail();
      await fetchData(pagination.current || 1, pagination.pageSize || 10, false);
    } finally {
      window.dispatchEvent(new Event("loading:hide"));
    }
  };

  const handleDelete = async () => {
    if (!taskId) return;
    try {
      await deleteSynthesisTaskByIdUsingDelete(taskId);
      message.success(t('synthesisTask.fileTask.messages.deleteSuccess'));
      navigate("/data/synthesis/task");
    } catch {
      message.error(t('synthesisTask.fileTask.messages.deleteFailed'));
    }
  };

  // 头部统计与操作
  const headerData: Record<string, unknown> = taskInfo
    ? {
        name: taskInfo.name,
        id: taskInfo.id,
        icon: <Sparkles className="w-8 h-8" />,
        description: taskInfo.description,
        createdAt: taskInfo.created_at ? formatDateTime(taskInfo.created_at) : "--",
      }
    : {};

  const statistics = [
    {
      key: "type",
      icon: <Sparkles className="w-4 h-4 text-blue-500" />,
      label: t('synthesisTask.fileTask.statistics.type'),
      value:
        taskInfo?.synthesis_type === "QA"
          ? t('synthesisTask.fileTask.typeMap.qa')
          : taskInfo?.synthesis_type === "COT"
          ? t('synthesisTask.fileTask.typeMap.cot')
          : taskInfo?.synthesis_type || "--",
    },
    {
      key: "fileCount",
      icon: <Folder className="w-4 h-4 text-purple-500" />,
      label: t('synthesisTask.fileTask.statistics.fileCount'),
      value: taskInfo?.total_files ?? "--",
    },
  ];

  const operations = [
    {
      key: "refresh",
      label: t('synthesisTask.fileTask.operations.refresh'),
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: t('synthesisTask.fileTask.operations.delete'),
      icon: <DeleteOutlined className="w-4 h-4" />,
      danger: true,
      confirm: {
        title: t('synthesisTask.fileTask.confirm.deleteTitle'),
        description: t('synthesisTask.fileTask.confirm.deleteDescription'),
        okText: t('synthesisTask.fileTask.confirm.okText'),
        cancelText: t('synthesisTask.fileTask.confirm.cancelText'),
        onConfirm: handleDelete,
        placement: "top",
        overlayStyle: {
          marginTop: 40,
        },
      },
    },
  ];

  const tabList = [
    {
      key: "files",
      label: t('synthesisTask.fileTask.tabs.files'),
    },
  ];

  const breadItems = [
    {
      title: <Link to="/data/synthesis/task">{t('synthesisTask.fileTask.breadcrumb.tasks')}</Link>,
    },
    {
      title: taskInfo?.name || t('synthesisTask.fileTask.breadcrumb.taskDetail'),
    },
  ];

  return (
    <>
      <Breadcrumb items={breadItems} />
      <div className="mb-4 mt-4">
        <DetailHeader data={headerData} statistics={statistics} operations={operations} />
      </div>
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full flex-1 overflow-auto">
          {activeTab === "files" && (
            <Table<SynthesisFileTaskItem>
              rowKey="id"
              loading={loading}
              dataSource={data}
              columns={columns}
              pagination={pagination}
              onChange={handleTableChange}
            />
          )}
        </div>
      </div>
    </>
  );
}
