import {Badge, Button, Input, Table, Typography} from "antd";
import {useNavigate} from "react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/Card"
import { GitBranch } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function OperatorTable({ task }: { task: any }) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const operatorColumns = [
    {
      title: t("dataCleansing.detail.operatorTable.serialNumber"),
      dataIndex: "index",
      key: "index",
      width: 80,
      render: (text: any, record: any, index: number) => index + 1,
    },
    {
      title: t("dataCleansing.detail.operatorTable.operatorName"),
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
            placeholder={t("dataCleansing.detail.operatorTable.searchOperatorName")}
            value={selectedKeys[0]}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={() => confirm()}>
              {t("dataCleansing.actions.search")}
            </Button>
            <Button size="sm" onClick={() => clearFilters()}>
              {t("dataCleansing.actions.reset")}
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) => record.name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: t("dataCleansing.detail.operatorTable.startTime"),
      dataIndex: "startTime",
      key: "startTime",
      sorter: (a: any, b: any) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime(),
    },
    {
      title: t("dataCleansing.detail.operatorTable.endTime"),
      dataIndex: "endTime",
      key: "endTime",
      sorter: (a: any, b: any) => new Date(a.endTime).getTime() - new Date(b.endTime).getTime(),
    },
    {
      title: t("dataCleansing.detail.operatorTable.duration"),
      dataIndex: "duration",
      key: "duration",
    },
    {
      title: t("dataCleansing.detail.operatorTable.processedFiles"),
      dataIndex: "processedFiles",
      key: "processedFiles",
      sorter: (a: any, b: any) => a.processedFiles - b.processedFiles,
    },
    {
      title: t("dataCleansing.detail.operatorTable.successRate"),
      dataIndex: "successRate",
      key: "successRate",
      sorter: (a: any, b: any) => a.successRate - b.successRate,
      render: (rate: number) => `${rate}%`,
    },
    {
      title: t("dataCleansing.detail.operatorTable.status"),
      dataIndex: "status",
      key: "status",
      filters: [
        { text: t("dataCleansing.detail.operatorTable.completed"), value: t("dataCleansing.detail.operatorTable.completed") },
        { text: t("dataCleansing.detail.operatorTable.failed"), value: t("dataCleansing.detail.operatorTable.failed") },
        { text: t("dataCleansing.detail.operatorTable.running"), value: t("dataCleansing.detail.operatorTable.running") },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === t("dataCleansing.detail.operatorTable.completed")
              ? "success"
              : status === t("dataCleansing.detail.operatorTable.running")
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
              {t("dataCleansing.detail.operatorTable.title")}
            </CardTitle>
            <CardDescription>{t("dataCleansing.detail.operatorTable.description")}</CardDescription>
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
