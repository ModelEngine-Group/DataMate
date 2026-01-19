import {Badge, Button, Input, Table, Typography} from "antd";
import {useNavigate} from "react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/Card"
import { GitBranch } from "lucide-react";

export default function OperatorTable({ task }: { task: any }) {
  const navigate = useNavigate();

  const operatorColumns = [
    {
      title: "序号",
      dataIndex: "index",
      key: "index",
      width: 80,
      render: (text: any, record: any, index: number) => index + 1,
    },
    {
      title: "算子名称",
      dataIndex: "name",
      key: "name",
      render: (text, record) => (
        <Typography.Link
          onClick={() => navigate(`/data/operator-market/plugin-detail/${record.id}`)}
        >
          {text}
        </Typography.Link>
      ),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索算子名称"
            value={selectedKeys[0]}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={() => confirm()}>
              搜索
            </Button>
            <Button size="sm" onClick={() => clearFilters()}>
              重置
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) => record.name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: "开始时间",
      dataIndex: "startTime",
      key: "startTime",
      sorter: (a: any, b: any) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime(),
    },
    {
      title: "结束时间",
      dataIndex: "endTime",
      key: "endTime",
      sorter: (a: any, b: any) => new Date(a.endTime).getTime() - new Date(b.endTime).getTime(),
    },
    {
      title: "执行时长",
      dataIndex: "duration",
      key: "duration",
    },
    {
      title: "处理文件数",
      dataIndex: "processedFiles",
      key: "processedFiles",
      sorter: (a: any, b: any) => a.processedFiles - b.processedFiles,
    },
    {
      title: "成功率",
      dataIndex: "successRate",
      key: "successRate",
      sorter: (a: any, b: any) => a.successRate - b.successRate,
      render: (rate: number) => `${rate}%`,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      filters: [
        { text: "已完成", value: "已完成" },
        { text: "失败", value: "失败" },
        { text: "运行中", value: "运行中" },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === "已完成"
              ? "success"
              : status === "运行中"
              ? "processing"
              : "error"
          }
          text={status}
        />
      ),
    },
  ]

  return task?.instance?.length > 0 && (
    <>
        <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-purple-600" />
              算子执行报告
            </CardTitle>
            <CardDescription>每个算子的详细执行情况</CardDescription>
          </CardHeader>
          <CardContent>
            <Table columns={operatorColumns} dataSource={Object.values(task?.instance).map((item) => ({
              id: item?.id,
              name: item?.name,
              startTime: new Date(task?.startedAt).toLocaleTimeString(),
              endTime: task?.finishedAt
                ? new Date(task.finishedAt).toLocaleTimeString()
                : '-',
              duration: task.duration,
              status: task.status.label,
              processedFiles: task.progress.finishedFileNum,
              successRate: task?.progress.successRate,
            }))} pagination={false} size="middle" />
          </CardContent>
        </Card>
    </>
  );
}
