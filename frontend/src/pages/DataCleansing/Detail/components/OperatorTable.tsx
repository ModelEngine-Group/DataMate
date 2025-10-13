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
      title: "算子名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      width: 200,
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
      title: "版本",
      dataIndex: "version",
      key: "version",
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
    },
  ];

  return (
    <Table
      columns={operatorColumns}
      dataSource={task?.instance || operators}
      pagination={false}
      size="middle"
    />
  );
}
