"use client"

import { useState } from "react"
import { Card, Button, Input, Badge, Table, Select, DatePicker } from "antd"
import { SearchOutlined, ReloadOutlined } from "@ant-design/icons"
import type { ColumnsType } from "antd/es/table"
import dayjs from "dayjs"

interface ExecutionLog {
    id: string
    taskName: string
    status: "success" | "failed" | "running" | "cancelled"
    triggerType: "manual" | "scheduled" | "api"
    startTime: string
    endTime: string
    duration: string
    retryCount: number
    processId: string
    errorMessage?: string
}

const mockLogs: ExecutionLog[] = [
    {
        id: "1",
        taskName: "用户数据同步",
        status: "success",
        triggerType: "scheduled",
        startTime: "2024-01-15 02:00:00",
        endTime: "2024-01-15 02:15:30",
        duration: "15分30秒",
        retryCount: 0,
        processId: "PID-20240115-001",
    },
    {
        id: "2",
        taskName: "订单数据归集",
        status: "failed",
        triggerType: "manual",
        startTime: "2024-01-15 10:30:00",
        endTime: "2024-01-15 10:32:15",
        duration: "2分15秒",
        retryCount: 2,
        processId: "PID-20240115-002",
        errorMessage: "连接数据库超时",
    },
    {
        id: "3",
        taskName: "日志数据清理",
        status: "running",
        triggerType: "scheduled",
        startTime: "2024-01-15 01:00:00",
        endTime: "-",
        duration: "1小时30分",
        retryCount: 0,
        processId: "PID-20240115-003",
    },
    {
        id: "4",
        taskName: "用户数据同步",
        status: "cancelled",
        triggerType: "manual",
        startTime: "2024-01-14 15:20:00",
        endTime: "2024-01-14 15:21:00",
        duration: "1分钟",
        retryCount: 0,
        processId: "PID-20240114-001",
    },
]

const statusOptions = [
    { value: "all", label: "全部状态" },
    { value: "success", label: "成功" },
    { value: "failed", label: "失败" },
    { value: "running", label: "运行中" },
    { value: "cancelled", label: "已取消" },
]

const getStatusBadge = (status: string) => {
    switch (status) {
        case "success":
            return <Badge color="green" text="成功" />
        case "failed":
            return <Badge color="red" text="失败" />
        case "running":
            return <Badge color="blue" text="运行中" />
        case "cancelled":
            return <Badge color="gray" text="已取消" />
        default:
            return <Badge text={status} />
    }
}

const getTriggerTypeBadge = (type: string) => {
    switch (type) {
        case "manual":
            return <Badge color="blue" text="手动触发" />
        case "scheduled":
            return <Badge color="purple" text="定时触发" />
        case "api":
            return <Badge color="gold" text="API触发" />
        default:
            return <Badge text={type} />
    }
}

export default function ExecutionLog() {
    const [logs] = useState<ExecutionLog[]>(mockLogs)
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [dateRange, setDateRange] = useState<[any, any] | null>(null)

    const filteredLogs = logs.filter((log) => {
        const matchesSearch = log.taskName.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === "all" || log.status === statusFilter

        let matchesDateRange = true
        if (dateRange && (dateRange[0] || dateRange[1])) {
            const logDate = dayjs(log.startTime)
            if (dateRange[0] && logDate.isBefore(dateRange[0], "day")) matchesDateRange = false
            if (dateRange[1] && logDate.isAfter(dateRange[1], "day")) matchesDateRange = false
        }

        return matchesSearch && matchesStatus && matchesDateRange
    })

    const handleReset = () => {
        setSearchTerm("")
        setStatusFilter("all")
        setDateRange(null)
    }

    const columns: ColumnsType<ExecutionLog> = [
        {
            title: "任务名称",
            dataIndex: "taskName",
            key: "taskName",
            render: (text: string) => <span style={{ fontWeight: 500 }}>{text}</span>,
        },
        {
            title: "状态",
            dataIndex: "status",
            key: "status",
            render: (status: string) => getStatusBadge(status),
        },
        {
            title: "触发类型",
            dataIndex: "triggerType",
            key: "triggerType",
            render: (type: string) => getTriggerTypeBadge(type),
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
            render: (text: string) => <span style={{ fontFamily: "monospace" }}>{text}</span>,
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
    ]

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Filter Controls */}
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 16 }}>
                <Input
                    prefix={<SearchOutlined />}
                    placeholder="搜索任务名称..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{ width: 240 }}
                />
                <Select
                    value={statusFilter}
                    onChange={setStatusFilter}
                    style={{ width: 120 }}
                    options={statusOptions}
                    placeholder="状态筛选"
                />
                <DatePicker.RangePicker
                    value={dateRange}
                    onChange={setDateRange}
                    style={{ width: 260 }}
                    allowClear
                    placeholder={["开始时间", "结束时间"]}
                />
                <Button icon={<ReloadOutlined />} onClick={handleReset}>
                    重置
                </Button>
            </div>

            {/* Execution Logs Table */}
            <Card>
                <Table
                    columns={columns}
                    dataSource={filteredLogs}
                    rowKey="id"
                    pagination={false}
                    locale={{ emptyText: "暂无执行日志" }}
                />
            </Card>
        </div>
    )
}
