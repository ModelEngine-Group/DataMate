import { useState } from 'react';
import { Descriptions, Empty, DescriptionsProps, Table, Button } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import PreviewPromptModal from "@/pages/DataEvaluation/Create/PreviewPrompt.tsx";
import { formatDateTime } from "@/utils/unit.ts";
import { evalTaskStatusMap, getEvalMethod, getEvalType, getSource } from "@/pages/DataEvaluation/evaluation.const.tsx";

const Overview = ({ task }) => {
  const [previewVisible, setPreviewVisible] = useState(false);
  if (!task) {
    return <Empty description="未找到评估任务信息" />;
  }

  const generateEvaluationPrompt = () => {
    setPreviewVisible(true);
  };

  // 基本信息
  const items: DescriptionsProps["items"] = [
    {
      key: "id",
      label: "ID",
      children: task.id,
    },
    {
      key: "name",
      label: "名称",
      children: task.name,
    },
    {
      key: "evalType",
      label: "评估类型",
      children: getEvalType(task.taskType),
    },
    {
      key: "evalMethod",
      label: "评估方式",
      children: getEvalMethod(task.evalMethod),
    },
    {
      key: "status",
      label: "状态",
      children: evalTaskStatusMap[task.status]?.label || "未知",
    },
    {
      key: "source",
      label: "评估数据",
      children: getSource(task.sourceType) + task.sourceName,
    },
    {
      key: "evalConfig.modelName",
      label: "模型",
      children: task.evalConfig?.modelName || task.evalConfig?.modelId,
    },
    {
      key: "createdBy",
      label: "创建者",
      children: task.createdBy || "未知",
    },
    {
      key: "createdAt",
      label: "创建时间",
      children: formatDateTime(task.createdAt),
    },
    {
      key: "updatedAt",
      label: "更新时间",
      children: formatDateTime(task.updatedAt),
    },
    {
      key: "description",
      label: "描述",
      children: task.description || "无",
    },
  ];

  const columns = [
    {
      title: '维度',
      dataIndex: 'dimension',
      key: 'dimension',
      width: '30%',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: '60%',
    },
  ];

  return (
    <>
      <div className=" flex flex-col gap-4">
        {/* 基本信息 */}
        <Descriptions
          title="基本信息"
          layout="vertical"
          size="small"
          items={items}
          column={5}
        />
        <h2 className="text-base font-semibold mt-8">评估维度</h2>
        <div className="overflow-x-auto">
          <Table
            size="middle"
            rowKey="id"
            columns={columns}
            dataSource={task?.evalConfig?.dimensions}
            scroll={{ x: "max-content", y: 600 }}
          />
        </div>
        <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={generateEvaluationPrompt}
          >
            查看评估提示词
          </Button>
        </div>
        <PreviewPromptModal
          previewVisible={previewVisible}
          onCancel={() => setPreviewVisible(false)}
          evaluationPrompt={task?.evalPrompt}
        />
      </div>
    </>
  );
};

export default Overview;
