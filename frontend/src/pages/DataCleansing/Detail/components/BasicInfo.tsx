import type {
  CleansingTask,
  OperatorI,
} from "@/pages/DataCleansing/cleansing.model";
import { Button, Card, Descriptions, Progress, Badge, Tag } from "antd";
import { Activity, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { useNavigate } from "react-router";

export default function BasicInfo({ task }: { task: CleansingTask }) {
  const navigate = useNavigate();

  const descriptionItems = [
    {
      key: "id",
      label: "任务ID",
      children: <span className="font-mono">#{task?.id}</span>,
    },
    { key: "name", label: "任务名称", children: task?.name },
    {
      key: "dataset",
      label: "源数据集",
      children: (
        <Button
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
      label: "目标数据集",
      children: (
        <Button
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
    { key: "template", label: "使用模板", children: task?.template },
    { key: "startTime", label: "开始时间", children: task?.startedAt },
    { key: "estimatedTime", label: "预计用时", children: task?.estimatedTime },
    {
      key: "description",
      label: "任务描述",
      children: (
        <span className="text-gray-600">{task?.description || "暂无描述"}</span>
      ),
      span: 2,
    },
    {
      key: "rules",
      label: "处理算子",
      children: (
        <div className="flex flex-wrap gap-1">
          {task?.instance?.map?.((op: OperatorI) => (
            <Tag key={op.id}>{op.name}</Tag>
          ))}
        </div>
      ),
      span: 2,
    },
  ];

  return (
    <>
      {/* 执行摘要 */}
      <Card className="mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <Clock className="w-8 h-8 text-blue-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-blue-500">
              {task?.duration || "--"}
            </div>
            <div className="text-sm text-gray-600">总耗时</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
            <CheckCircle className="w-8 h-8 text-green-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-green-500">
              {task?.successFiles || "--"}
            </div>
            <div className="text-sm text-gray-600">成功文件</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg">
            <AlertCircle className="w-8 h-8 text-red-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-red-500">
              {task?.failedFiles || "--"}
            </div>
            <div className="text-sm text-gray-600">失败文件</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <Activity className="w-8 h-8 text-purple-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-purple-500">
              {task?.progress || "--"}
            </div>
            <div className="text-sm text-gray-600">成功率</div>
          </div>
        </div>
      </Card>
      {/* 基本信息 */}
      <Card>
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
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
          <h3 className="text-lg font-semibold text-gray-900 mb-4">处理进度</h3>
          <Progress percent={task?.progress} showInfo />
          <div className="grid grid-cols-2 gap-4 text-sm mt-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full inline-block" />
              <span>已完成: {task?.processedFiles || "--"}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full inline-block" />
              <span>处理中: {task?.processingFiles || "--"}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-gray-300 rounded-full inline-block" />
              <span>
                待处理: {task?.totalFiles - task?.processedFiles || "--"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-red-500 rounded-full inline-block" />
              <span>失败: {task?.failedFiles || "--"}</span>
            </div>
          </div>
        </div>
      </Card>
    </>
  );
}
