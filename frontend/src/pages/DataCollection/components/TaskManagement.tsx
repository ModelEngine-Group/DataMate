import { useState } from "react";
import { Card, Button, Badge, Table, Dropdown } from "antd";
import { EllipsisOutlined } from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";

interface Task {
  id: string;
  name: string;
  description: string;
  cronExpression: string;
  status: "running" | "stopped" | "error";
  retryCount: number;
  timeout: number;
  incrementalField: string;
  createdAt: string;
}

const mockTasks: Task[] = [
  {
    id: "1",
    name: "用户数据同步",
    description: "从MySQL同步用户表数据到数据仓库",
    cronExpression: "0 0 2 * * ?",
    status: "running",
    retryCount: 3,
    timeout: 3600,
    incrementalField: "updated_at",
    createdAt: "2024-01-15 10:30:00",
  },
  {
    id: "2",
    name: "订单数据归集",
    description: "归集各渠道订单数据",
    cronExpression: "0 */30 * * * ?",
    status: "stopped",
    retryCount: 2,
    timeout: 1800,
    incrementalField: "create_time",
    createdAt: "2024-01-14 14:20:00",
  },
  {
    id: "3",
    name: "日志数据清理",
    description: "清理过期的系统日志数据",
    cronExpression: "0 0 1 * * ?",
    status: "error",
    retryCount: 1,
    timeout: 7200,
    incrementalField: "log_time",
    createdAt: "2024-01-13 09:15:00",
  },
];

export default function TaskManagement() {
  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || task.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return <Badge color="green" text="运行中" />;
      case "stopped":
        return <Badge color="gray" text="已停止" />;
      case "error":
        return <Badge color="red" text="错误" />;
      default:
        return <Badge text={status} />;
    }
  };

  const handleStartTask = (taskId: string) => {
    setTasks(
      tasks.map((task) =>
        task.id === taskId ? { ...task, status: "running" as const } : task
      )
    );
  };

  const handleStopTask = (taskId: string) => {
    setTasks(
      tasks.map((task) =>
        task.id === taskId ? { ...task, status: "stopped" as const } : task
      )
    );
  };

  const handleDeleteTask = (taskId: string) => {
    setTasks(tasks.filter((task) => task.id !== taskId));
  };

  const columns = [
    {
      title: "任务名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      render: (text: string) => <span style={{ fontWeight: 500 }}>{text}</span>,
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
    {
      title: "Cron表达式",
      dataIndex: "cronExpression",
      key: "cronExpression",
      render: (text: string) => (
        <span style={{ fontFamily: "monospace" }}>{text}</span>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => getStatusBadge(status),
    },
    {
      title: "重试次数",
      dataIndex: "retryCount",
      key: "retryCount",
    },
    {
      title: "超时时间(s)",
      dataIndex: "timeout",
      key: "timeout",
    },
    {
      title: "增量字段",
      dataIndex: "incrementalField",
      key: "incrementalField",
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
    },
    {
      title: "操作",
      key: "action",
      fixed: "right" as const,
      render: (_: any, record: Task) => (
        <Dropdown
          menu={{
            items: [
              {
                key: "edit",
                label: "编辑",
              },
              record.status === "stopped"
                ? {
                    key: "start",
                    label: "启动",
                  }
                : {
                    key: "stop",
                    label: "停止",
                  },
              {
                key: "delete",
                label: "删除",
                danger: true,
                onClick: () => handleDeleteTask(record.id),
              },
            ],
          }}
          trigger={["click"]}
        >
          <Button
            type="text"
            icon={<EllipsisOutlined style={{ fontSize: 20 }} />}
          />
        </Dropdown>
      ),
    },
  ];

  // 新增：SearchControls filters 配置
  const searchFilters = [
    {
      key: "status",
      label: "状态筛选",
      options: [
        { value: "all", label: "全部状态" },
        { value: "running", label: "运行中" },
        { value: "stopped", label: "已停止" },
        { value: "error", label: "错误" },
      ],
    },
  ];

  // 新增：SearchControls 筛选变化处理
  const handleSearchControlsFiltersChange = (
    filters: Record<string, string[]>
  ) => {
    setStatusFilter(filters.status?.[0] || "all");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Header Actions */}
      <SearchControls
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        searchPlaceholder="搜索任务名称或描述..."
        filters={searchFilters}
        onFiltersChange={handleSearchControlsFiltersChange}
        showViewToggle={false}
      />

      {/* Tasks Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredTasks}
          rowKey="id"
          pagination={false}
          scroll={{ x: "max-content" }}
        />
      </Card>
    </div>
  );
}
