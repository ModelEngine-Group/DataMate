import { useEffect, useState } from "react";
import { Card, Button, Badge, Table, DatePicker, App } from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { SearchControls } from "@/components/SearchControls";
import type { CollectionLog } from "@/types/collection";
import { queryExecutionLogUsingPost } from "../../data-collection-apis";
import { LogStatusMap, LogTriggerTypeMap } from "../../collection-model";

const filterOptions = [
  {
    key: "status",
    label: "状态筛选",
    options: Object.values(LogStatusMap),
  },
  {
    key: "triggerType",
    label: "触发类型",
    options: Object.values(LogTriggerTypeMap),
  },
];

export default function ExecutionLog() {
  const { message } = App.useApp();
  const [loadingData, setLoadingData] = useState(false);
  const [logs, setLogs] = useState<CollectionLog[]>([]);
  const [pagination, setPagination] = useState({
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ["10", "15", "20", "50"],
    showTotal: (total: number) => `共 ${total} 条`,
    onChange: (current: number, pageSize?: number) => {
      setSearchParams((prev) => ({
        ...prev,
        current,
        pageSize: pageSize || prev.pageSize,
      }));
    },
  });

  const [searchParams, setSearchParams] = useState<{
    keyword: string;
    current: number;
    pageSize: number;
    dateRange: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null;
    filters: Record<string, string[]>;
  }>({
    keyword: "",
    filters: {},
    current: 1,
    pageSize: 10,
    dateRange: null,
  });

  const handleReset = () => {
    setSearchParams({
      keyword: "",
      filters: {},
      current: 1,
      pageSize: 10,
      dateRange: null,
    });
  };

  const fetchLogs = async () => {
    setLoadingData(true);
    try {
      const res = await queryExecutionLogUsingPost(searchParams);
      setLogs(res.data.results || []);
      setPagination((prev) => ({
        ...prev,
        total: res.data.totalElements || 0,
      }));
    } catch (error) {
      message.error("获取执行日志失败");
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [searchParams]);

  const columns: ColumnsType<CollectionLog> = [
    {
      title: "任务名称",
      dataIndex: "taskName",
      key: "taskName",
      fixed: "left",
      render: (text: string) => <span style={{ fontWeight: 500 }}>{text}</span>,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <Badge
          text={LogStatusMap[status]?.label}
          color={LogStatusMap[status]?.color}
        />
      ),
    },
    {
      title: "触发类型",
      dataIndex: "triggerType",
      key: "triggerType",
      render: (type: string) => LogTriggerTypeMap[type].label,
    },
    {
      title: "开始时间",
      dataIndex: "startTime",
      key: "startTime",
    },
    {
      title: "结束时间",
      dataIndex: "endTime",
      key: "endTime",
    },
    {
      title: "执行时长",
      dataIndex: "duration",
      key: "duration",
    },
    {
      title: "重试次数",
      dataIndex: "retryCount",
      key: "retryCount",
    },
    {
      title: "进程ID",
      dataIndex: "processId",
      key: "processId",
      render: (text: string) => (
        <span style={{ fontFamily: "monospace" }}>{text}</span>
      ),
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
  ];

  return (
    <div className="flex flex-col gap-4">
      {/* Filter Controls */}
      <div className="flex items-center justify-between gap-4">
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={(keyword: string) =>
            setSearchParams({
              ...searchParams,
              keyword,
            })
          }
          filters={filterOptions}
          onFiltersChange={(filters) =>
            setSearchParams({
              ...searchParams,
              filters,
            })
          }
          showViewToggle={false}
          onClearFilters={() =>
            setSearchParams((prev) => ({
              ...prev,
              filters: {},
            }))
          }
          showDatePicker
          dateRange={searchParams.dateRange}
          onDateChange={(date) =>
            setSearchParams((prev) => ({ ...prev, dateRange: date }))
          }
          onReload={handleReset}
          searchPlaceholder="搜索任务名称、进程ID或错误信息..."
          className="flex-1"
        />
      </div>
      <Card>
        <Table
          loading={loadingData}
          columns={columns}
          dataSource={logs}
          rowKey="id"
          pagination={pagination}
          scroll={{ x: "max-content" }}
        />
      </Card>
    </div>
  );
}
