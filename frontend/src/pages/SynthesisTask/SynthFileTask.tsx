import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { Table, Badge, Button } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import { querySynthesisFileTasksUsingGet, deleteSynthesisFileTaskByIdUsingDelete } from "./synthesis-api";

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

export default function SynthFileTask() {
  const { id: taskId = "" } = useParams();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SynthesisFileTaskItem[]>([]);
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  const fetchData = async (page = 1, pageSize = 10) => {
    if (!taskId) return;
    setLoading(true);
    try {
      const res = await querySynthesisFileTasksUsingGet(taskId, {
        page,
        page_size: pageSize,
      });
      const payload: PagedResponse<SynthesisFileTaskItem> = res.data.data;
      setData(payload.content || []);
      setPagination({
        current: payload.page,
        pageSize: payload.size,
        total: payload.totalElements,
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

  const handleDelete = async (record: SynthesisFileTaskItem) => {
    if (!taskId) return;
    await deleteSynthesisFileTaskByIdUsingDelete(taskId, record.id);
    fetchData(pagination.current || 1, pagination.pageSize || 10);
  };

  const columns: ColumnsType<SynthesisFileTaskItem> = [
    {
      title: "文件名",
      dataIndex: "file_name",
      key: "file_name",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status?: string) => {
        let badgeStatus: any = "default";
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
      title: "操作",
      key: "action",
      render: (_text, record) => (
        <Button type="link" danger onClick={() => handleDelete(record)}>
          删除
        </Button>
      ),
    },
  ];

  return (
    <div className="p-4 bg-white rounded-lg h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium">文件任务列表</h2>
      </div>
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
