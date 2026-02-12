import { useState } from 'react';
import { Descriptions, Empty, DescriptionsProps, Table, Button } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import PreviewPromptModal from "@/pages/DataEvaluation/Create/PreviewPrompt.tsx";
import { formatDateTime } from "@/utils/unit.ts";
import { evalTaskStatusMap, getEvalMethod, getEvalType, getSource } from "@/pages/DataEvaluation/evaluation.const.tsx";
import { useTranslation } from "react-i18next";

const Overview = ({ task }) => {
  const { t } = useTranslation();
  const [previewVisible, setPreviewVisible] = useState(false);
  if (!task) {
    return <Empty description={t("dataEvaluation.detail.taskNotFound")} />;
  }

  const generateEvaluationPrompt = () => {
    setPreviewVisible(true);
  };

  // 基本信息
  const items: DescriptionsProps["items"] = [
    {
      key: "id",
      label: t("dataEvaluation.detail.labels.id"),
      children: task.id,
    },
    {
      key: "name",
      label: t("dataEvaluation.detail.labels.name"),
      children: task.name,
    },
    {
      key: "evalType",
      label: t("dataEvaluation.detail.labels.taskType"),
      children: getEvalType(task.taskType, t),
    },
    {
      key: "evalMethod",
      label: t("dataEvaluation.detail.labels.evalMethod"),
      children: getEvalMethod(task.evalMethod, t),
    },
    {
      key: "status",
      label: t("dataEvaluation.detail.labels.status"),
      children: task.status?.label || t("dataManagement.defaults.unknown"),
    },
    {
      key: "source",
      label: t("dataEvaluation.detail.labels.evalData"),
      children: getSource(task.sourceType, t) + task.sourceName,
    },
    {
      key: "evalConfig.modelName",
      label: t("dataEvaluation.detail.labels.model"),
      children: task.evalConfig?.modelName || task.evalConfig?.modelId,
    },
    {
      key: "createdBy",
      label: t("dataEvaluation.detail.labels.createdBy"),
      children: task.createdBy || t("dataManagement.defaults.unknown"),
    },
    {
      key: "createdAt",
      label: t("dataEvaluation.detail.labels.createdAt"),
      children: formatDateTime(task.createdAt),
    },
    {
      key: "updatedAt",
      label: t("dataEvaluation.detail.labels.updatedAt"),
      children: formatDateTime(task.updatedAt),
    },
    {
      key: "description",
      label: t("dataEvaluation.detail.labels.description"),
      children: task.description || t("dataManagement.defaults.none"),
    },
  ];

  const columns = [
    {
      title: t("dataEvaluation.detail.labels.dimension"),
      dataIndex: 'dimension',
      key: 'dimension',
      width: '30%',
    },
    {
      title: t("dataEvaluation.detail.labels.dimensionDesc"),
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
          title={t("dataEvaluation.detail.basicInfo")}
          layout="vertical"
          size="small"
          items={items}
          column={5}
        />
        <h2 className="text-base font-semibold mt-8">
          {t("dataEvaluation.detail.labels.dimensions")}
        </h2>
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
            {t("dataEvaluation.create.viewPrompt")}
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
