import {Card, Badge, Button, Modal, Table, Tag} from "antd";
import type { ColumnsType } from "antd/es/table";
import { SearchControls } from "@/components/SearchControls";
import { queryExecutionLogUsingPost } from "../collection.apis";
import useFetchData from "@/hooks/useFetchData";
import { useEffect, useState } from "react";
import {TaskExecution} from "@/pages/DataCollection/collection.model.ts";
import {mapTaskExecution} from "@/pages/DataCollection/collection.const.ts";
import { queryExecutionLogFileByIdUsingGet } from "../collection.apis";
import { FileTextOutlined } from "@ant-design/icons";

const filterOptions = [
  {
    key: "status",
    label: "状态筛选",
    options: [
      { value: "all", label: "全部状态" },
      { value: "RUNNING", label: "运行中" },
      { value: "SUCCESS", label: "成功" },
      { value: "FAILED", label: "失败" },
      { value: "STOPPED", label: "停止" },
    ],
  },
];

export default function Execution({ taskId }: { taskId?: string }) {
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);
  const [logOpen, setLogOpen] = useState(false);
  const [logLoading, setLogLoading] = useState(false);
  const [logTitle, setLogTitle] = useState<string>("");
  const [logContent, setLogContent] = useState<string>("");
  const [logFilename, setLogFilename] = useState<string>("");
  const [logBlobUrl, setLogBlobUrl] = useState<string>("");

  const formatDuration = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return "-";
    const total = Math.max(0, Math.floor(seconds));
    if (total < 60) return `${total}s`;
    const min = Math.floor(total / 60);
    const sec = total % 60;
    return `${min}min${sec}s`;
  };

  const handleReset = () => {
    setSearchParams({
      keyword: "",
      filter: {
        type: [],
        status: [],
        tags: [],
      },
      current: 1,
      pageSize: 10,
    });
    setDateRange(null);
  };

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    handleFiltersChange,
    handleKeywordChange,
  } = useFetchData<TaskExecution>(
    (params) => {
      const { keyword, start_time, end_time, ...rest } = params || {};
      return queryExecutionLogUsingPost({
        ...rest,
        task_id: taskId || undefined,
        task_name: keyword || undefined,
        start_time,
        end_time,
      });
    },
    mapTaskExecution,
    30000,
    false,
    [],
    0
  );

  useEffect(() => {
    setSearchParams((prev) => ({
      ...prev,
      current: 1,
    }));
  }, [taskId, setSearchParams]);

  const handleViewLog = async (record: TaskExecution) => {
    setLogOpen(true);
    setLogLoading(true);
    setLogTitle(`${record.taskName} / ${record.id}`);
    setLogContent("");
    setLogFilename("");
    if (logBlobUrl) {
      URL.revokeObjectURL(logBlobUrl);
      setLogBlobUrl("");
    }
    try {
      const { blob, filename } = await queryExecutionLogFileByIdUsingGet(record.id);
      setLogFilename(filename);
      const url = URL.createObjectURL(blob);
      setLogBlobUrl(url);
      const text = await blob.text();
      setLogContent(text);
    } catch (e: any) {
      setLogContent(e?.data?.detail || e?.message || "Failed to load log");
    } finally {
      setLogLoading(false);
    }
  };

  const columns: ColumnsType<any> = [
    {
      title: "任务名称",
      dataIndex: "taskName",
      key: "taskName",
      fixed: "left",
      render: (text: string) => (
        <span style={{ fontWeight: 500 }}>{text}</span>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: any) => ((
          <Tag color={status.color}>{status.label}</Tag>
        )
      ),
    },
    {
      title: "开始时间",
      dataIndex: "startedAt",
      key: "startedAt",
    },
    {
      title: "结束时间",
      dataIndex: "completedAt",
      key: "completedAt",
    },
    {
      title: "执行时长",
      dataIndex: "durationSeconds",
      key: "durationSeconds",
      render: (v?: number) => formatDuration(v),
    },
    {
      title: "错误信息",
      dataIndex: "errorMessage",
      key: "errorMessage",
      render: (msg?: string) =>
        msg ? (
          <span style={{ color: "#f5222d" }} title={msg}>
            {msg}
          </span>
        ) : (
          <span style={{ color: "#bbb" }}>-</span>
        ),
    },
    {
      title: "操作",
      key: "action",
      fixed: "right",
      width: 120,
      render: (_: any, record: TaskExecution) => (
        <Button
          type="link"
          icon={<FileTextOutlined />}
          onClick={() => handleViewLog(record)}
        >
          查看日志
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      {/* Filter Controls */}
      <div className="flex items-center justify-between gap-4">
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={handleKeywordChange}
          filters={filterOptions}
          onFiltersChange={handleFiltersChange}
          showViewToggle={false}
          onClearFilters={() =>
            setSearchParams((prev) => ({
              ...prev,
              filter: { ...prev.filter, status: [] },
              current: 1,
            }))
          }
          showDatePicker
          dateRange={dateRange as any}
          onDateChange={(date) => {
            setDateRange(date as any);
            const start = (date?.[0] as any)?.toISOString?.() || undefined;
            const end = (date?.[1] as any)?.toISOString?.() || undefined;
            setSearchParams((prev) => ({
              ...prev,
              current: 1,
              start_time: start,
              end_time: end,
            }));
          }}
          onReload={handleReset}
          searchPlaceholder="搜索任务名称..."
          className="flex-1"
        />
      </div>
      <Card>
        <Table
          loading={loading}
          columns={columns}
          dataSource={tableData}
          rowKey="id"
          pagination={pagination}
          scroll={{ x: "max-content" }}
        />
      </Card>

      <Modal
        title={logTitle || "执行日志"}
        open={logOpen}
        onCancel={() => {
          setLogOpen(false);
          if (logBlobUrl) {
            URL.revokeObjectURL(logBlobUrl);
            setLogBlobUrl("");
          }
        }}
        footer={
          <div style={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
            <div style={{ color: "#6b7280", fontSize: 12 }}>{logFilename || ""}</div>
            <div style={{ display: "flex", gap: 8 }}>
              {logBlobUrl ? (
                <Button
                  onClick={() => {
                    const a = document.createElement("a");
                    a.href = logBlobUrl;
                    a.download = logFilename || "execution.log";
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                  }}
                >
                  下载日志
                </Button>
              ) : null}
              <Button
                type="primary"
                onClick={() => {
                  setLogOpen(false);
                  if (logBlobUrl) {
                    URL.revokeObjectURL(logBlobUrl);
                    setLogBlobUrl("");
                  }
                }}
              >
                关闭
              </Button>
            </div>
          </div>
        }
        width={900}
      >
        <div
          style={{
            background: "#0b1020",
            color: "#e5e7eb",
            borderRadius: 8,
            padding: 12,
            maxHeight: "60vh",
            overflow: "auto",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
            fontSize: 12,
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {logLoading ? "Loading..." : (logContent || "(empty)")}
        </div>
      </Modal>
    </div>
  );
}
