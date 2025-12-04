import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router";
import { Table, Badge, Button } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import { querySynthesisFileTasksUsingGet, querySynthesisTaskByIdUsingGet } from "@/pages/SynthesisTask/synthesis-api";
import type { BadgeProps } from "antd";
import { formatDateTime } from "@/utils/unit";

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
  model_id: string;
}

export default function SynthFileTask() {
  const { id: taskId = "" } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SynthesisFileTaskItem[]>([]);
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [taskInfo, setTaskInfo] = useState<SynthesisTaskInfo | null>(null);

  // 查询总任务详情
  useEffect(() => {
    if (!taskId) return;
    querySynthesisTaskByIdUsingGet(taskId).then((res) => {
      setTaskInfo(res?.data?.data || null);
    });
  }, [taskId]);

  const fetchData = async (page = 1, pageSize = 10) => {
    if (!taskId) return;
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
    }
  };

  useEffect(() => {
    fetchData(1, pagination.pageSize || 10);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const handleTableChange = (pag: TablePaginationConfig) => {
    fetchData(pag.current || 1, pag.pageSize || 10);
  };

  const columns: ColumnsType<SynthesisFileTaskItem> = [
    {
      title: "文件名",
      dataIndex: "file_name",
      key: "file_name",
      render: (text: string, record) => (
        <Button
          type="link"
          onClick={() => navigate(`/data/synthesis/task/file/${record.id}/detail`, { state: { fileName: record.file_name, taskId } })}
        >
          {text}
        </Button>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status?: string) => {
        let badgeStatus: BadgeProps["status"] = "default";
        let text = status || "未知";
        if (status === "pending" || status === "processing") {
          badgeStatus = "processing";
          text = "处理中";
        } else if (status === "completed") {
          badgeStatus = "success";
          text = "已完成";
        } else if (status === "failed") {
          badgeStatus = "error";
          text = "失败";
        }
        return <Badge status={badgeStatus} text={text} />;
      },
    },
    {
      title: "切片进度",
      key: "chunks",
      render: (_text, record) => (
        <span>
          {record.processed_chunks}/{record.total_chunks}
        </span>
      ),
    },
    {
      title: "目标文件路径",
      dataIndex: "target_file_location",
      key: "target_file_location",
      ellipsis: true,
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (val?: string) => (val ? formatDateTime(val) : "-"),
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      key: "updated_at",
      render: (val?: string) => (val ? formatDateTime(val) : "-"),
    },
  ];

  return (
    <div className="p-4 bg-white rounded-lg h-full flex flex-col">
      {/* 顶部任务信息和返回按钮 */}
      <div className="flex items-center justify-between mb-4">
        <div className="space-y-1">
          {taskInfo && (
            <>
              <div className="text-lg font-medium flex items-center gap-2">
                <span>{taskInfo.name}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  {taskInfo.synthesis_type === "QA" ? "问答对生成" : taskInfo.synthesis_type === "COT" ? "链式推理生成" : taskInfo.synthesis_type}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-gray-50 text-gray-700 border border-gray-200">
                  状态：{taskInfo.status === "pending" ? "等待中" : taskInfo.status === "completed" ? "已完成" : taskInfo.status === "failed" ? "失败" : taskInfo.status}
                </span>
              </div>
              <div className="text-xs text-gray-500 flex gap-4">
                <span>创建时间：{formatDateTime(taskInfo.created_at)}</span>
                <span>模型ID：{taskInfo.model_id}</span>
              </div>
            </>
          )}
        </div>
        <Button type="default" onClick={() => navigate("/data/synthesis/task")}>返回任务首页</Button>
      </div>
      {/* 文件任务表格 */}
      <Table<SynthesisFileTaskItem>
        rowKey="id"
        loading={loading}
        dataSource={data}
        columns={columns}
        pagination={pagination}
        onChange={handleTableChange}
      />
    </div>
  );
}
