import {CleansingTask, TaskStatus} from "@/pages/DataCleansing/cleansing.model";
import { Button, Card, Descriptions, Progress } from "antd";
import { Activity, AlertCircle, BookOpen, CheckCircle, Clock } from "lucide-react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import {formatExecutionDuration} from "@/utils/unit.ts";
import {CardHeader, CardTitle} from "@/components/Card.tsx";

export default function BasicInfo({ task }: { task: CleansingTask }) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const descriptionItems = [
    {
      key: "id",
      label: t("dataCleansing.detail.basicInfo.taskId"),
      children: <span className="font-mono">{task?.id}</span>,
    },
    { key: "name", label: t("dataCleansing.detail.basicInfo.taskName"), children: task?.name },
    {
      key: "dataset",
      label: t("dataCleansing.detail.basicInfo.srcDataset"),
      children: (
        <Button
          style={{ paddingLeft: 0, marginLeft: 0 }}
          type="link"
          size="small"
          onClick={() =>
            navigate("/data/management/detail/" + task?.srcDatasetId)
          }
        >
          {task?.srcDatasetName}
        </Button>
      ),
    },
    {
      key: "targetDataset",
      label: t("dataCleansing.detail.basicInfo.destDataset"),
      children: (
        <Button
          style={{ paddingLeft: 0, marginLeft: 0 }}
          type="link"
          size="small"
          onClick={() =>
            navigate("/data/management/detail/" + task?.destDatasetId)
          }
        >
          {task?.destDatasetName}
        </Button>
      ),
    },
    { key: "startTime", label: t("dataCleansing.detail.basicInfo.startTime"), children: task?.startedAt },
    {
      key: "description",
      label: t("dataCleansing.detail.basicInfo.description"),
      children: (
        <span className="text-gray-600">{task?.description || "--"}</span>
      ),
      span: 2,
    },
    { key: "finishedTime", label: t("dataCleansing.detail.basicInfo.endTime"), children: task?.finishedAt },
    { key: "retryCount", label: t("dataCleansing.detail.basicInfo.retryCount"), children: task?.retryCount },
  ];

  return (
    <>
      {/* 执行摘要 */}
      <Card className="mb-6">
        <CardHeader className="p-1 pb-4">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w h text-blue-600" />
            {t("dataCleansing.detail.basicInfo.executionSummary")}
          </CardTitle>
        </CardHeader>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <Clock className="w-8 h-8 text-blue-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-blue-500">
              {formatExecutionDuration(task?.startedAt, task?.finishedAt) || "--"}
            </div>
            <div className="text-sm text-gray-600">{t("dataCleansing.detail.statistics.totalDuration")}</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
            <CheckCircle className="w-8 h-8 text-green-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-green-500">
              {task?.progress?.succeedFileNum || "0"}
            </div>
            <div className="text-sm text-gray-600">{t("dataCleansing.detail.statistics.successFiles")}</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg">
            <AlertCircle className="w-8 h-8 text-red-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-red-500">
              {(task?.status.value === TaskStatus.RUNNING || task?.status.value === TaskStatus.PENDING)  ?
                task?.progress.failedFileNum :
                task?.progress?.totalFileNum - task?.progress.succeedFileNum}
            </div>
            <div className="text-sm text-gray-600">{t("dataCleansing.detail.statistics.failedFiles")}</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <Activity className="w-8 h-8 text-purple-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-purple-500">
              {task?.progress?.successRate ? task?.progress?.successRate + "%" : "--"}
            </div>
            <div className="text-sm text-gray-600">{t("dataCleansing.detail.statistics.successRate")}</div>
          </div>
        </div>
      </Card>
      {/* 基本信息 */}
      <Card>
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("dataCleansing.detail.basicInfo.basicInformation")}</h3>
          <Descriptions
            column={2}
            bordered={false}
            size="middle"
            labelStyle={{ fontWeight: 500, color: "#555" }}
            contentStyle={{ fontSize: 14 }}
            items={descriptionItems}
          ></Descriptions>
        </div>
        {/* 处理进度 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("dataCleansing.detail.basicInfo.processingProgress")}</h3>
          { task?.status?.value === TaskStatus.FAILED ?
            <Progress percent={task?.progress?.process} size="small" status="exception" />
            : <Progress percent={task?.progress?.process} size="small"/>
          }
          <div className="grid grid-cols-2 gap-4 text-sm mt-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full inline-block" />
              <span>{t("dataCleansing.detail.basicInfo.completed", { count: task?.progress?.succeedFileNum || "0" })}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full inline-block" />
              <span>{t("dataCleansing.detail.basicInfo.processing", { count: (task?.status.value === TaskStatus.RUNNING || task?.status.value === TaskStatus.PENDING)  ?
                  task?.progress?.totalFileNum - task?.progress.succeedFileNum : 0 })}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-red-500 rounded-full inline-block" />
              <span>{t("dataCleansing.detail.basicInfo.failed", { count: (task?.status.value === TaskStatus.RUNNING || task?.status.value === TaskStatus.PENDING)  ?
                  task?.progress.failedFileNum :
                  task?.progress?.totalFileNum - task?.progress.succeedFileNum })}</span>
            </div>
          </div>
        </div>
      </Card>
    </>
  );
}
