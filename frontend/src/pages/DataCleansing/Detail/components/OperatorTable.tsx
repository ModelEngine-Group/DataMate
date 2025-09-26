import { Button, Input, Table, Badge } from "antd";

const operators = [
  {
    name: "格式转换",
    startTime: "09:30:15",
    endTime: "09:58:42",
    duration: "28分27秒",
    status: "成功",
    processedFiles: 1250,
    successRate: 100,
  },
  {
    name: "噪声去除",
    startTime: "09:58:42",
    endTime: "10:35:18",
    duration: "36分36秒",
    status: "成功",
    processedFiles: 1250,
    successRate: 98.2,
  },
  {
    name: "尺寸标准化",
    startTime: "10:35:18",
    endTime: "11:12:05",
    duration: "36分47秒",
    status: "成功",
    processedFiles: 1228,
    successRate: 99.5,
  },
  {
    name: "质量检查",
    startTime: "11:12:05",
    endTime: "11:45:32",
    duration: "33分27秒",
    status: "成功",
    processedFiles: 1222,
    successRate: 97.8,
  },
];
export default function OperatorTable({ task }: { task: any }) {
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
      filterDropdown: ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
      }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索算子名称"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              搜索
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              重置
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) =>
        record.name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: "开始时间",
      dataIndex: "startTime",
      key: "startTime",
      sorter: (a: any, b: any) =>
        new Date(a.startTime).getTime() - new Date(b.startTime).getTime(),
    },
    {
      title: "结束时间",
      dataIndex: "endTime",
      key: "endTime",
      sorter: (a: any, b: any) =>
        new Date(a.endTime).getTime() - new Date(b.endTime).getTime(),
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
        { text: "成功", value: "成功" },
        { text: "失败", value: "失败" },
        { text: "运行中", value: "运行中" },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === "成功"
              ? "success"
              : status === "失败"
              ? "error"
              : "processing"
          }
          text={status}
        />
      ),
    },
  ];

  console.log("task?.rules");

  return (
    <Table
      columns={operatorColumns}
      dataSource={task?.rules || operators}
      pagination={false}
      size="middle"
    />
  );
}
