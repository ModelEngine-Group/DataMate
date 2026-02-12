import { useEffect, useMemo, useState, useCallback } from "react";
import {
  Breadcrumb,
  App,
  Tabs,
  Badge,
  Descriptions,
  DescriptionsProps,
} from "antd";
import { ReloadOutlined, DeleteOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import DetailHeader from "@/components/DetailHeader";
import { Link, useNavigate, useParams } from "react-router";
import {
  getRatioTaskByIdUsingGet,
  deleteRatioTasksUsingDelete,
} from "@/pages/RatioTask/ratio.api";
import { post } from "@/utils/request";
import type { RatioTaskItem } from "@/pages/RatioTask/ratio.model";
import { mapRatioTask } from "../ratio.const";
import DataRatioChart from "./DataRatioChart";
import RatioDisplay from "./RatioDisplay";
import DataMetrics from "./DataMetrics";

export default function RatioTaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("overview");
  const { message } = App.useApp();
  const [ratioTask, setRatioTask] = useState<RatioTaskItem>(
    {} as RatioTaskItem
  );

  const tabList = useMemo(
    () => [
      {
        key: "overview",
        label: t("ratioTask.detail.tabs.overview"),
      },
    ],
    [t]
  );

  const navigateItems = useMemo(
    () => [
      {
        title: <Link to="/data/synthesis/ratio-task">{t("ratioTask.detail.homeLink")}</Link>,
      },
      {
        title: ratioTask.name || t("ratioTask.detail.detailTitle"),
      },
    ],
    [ratioTask, t]
  );

  const fetchRatioTask = useCallback(async () => {
    const { data } = await getRatioTaskByIdUsingGet(id as string);
    setRatioTask(mapRatioTask(data, t));
  }, [id, t]);

  useEffect(() => {
    fetchRatioTask();
  }, [t]);

  const handleRefresh = useCallback(
    async (showMessage = true) => {
      await fetchRatioTask();
      if (showMessage) message.success({ content: t("ratioTask.detail.messages.refreshSuccess") });
    },
    [fetchRatioTask, message, t]
  );

  const handleDelete = async () => {
    await deleteRatioTasksUsingDelete(id as string);
    navigate("/ratio/task");
    message.success(t("ratioTask.detail.messages.deleteSuccess"));
  };

  const handleExecute = async () => {
    await post(`/api/synthesis/ratio-task/${id}/execute`);
    handleRefresh();
    message.success(t("ratioTask.detail.messages.taskStarted"));
  };

  const handleStop = async () => {
    await post(`/api/synthesis/ratio-task/${id}/stop`);
    handleRefresh();
    message.success(t("ratioTask.detail.messages.taskStopped"));
  };

  useEffect(() => {
    const refreshData = () => {
      handleRefresh(false);
    };
    window.addEventListener("update:ratio-task", refreshData);
    return () => {
      window.removeEventListener("update:ratio-task", refreshData);
    };
  }, [handleRefresh]);

  // 操作列表
  const operations = [
    {
      key: "refresh",
      label: t("ratioTask.detail.operations.refresh"),
      icon: <ReloadOutlined />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: t("ratioTask.detail.operations.delete"),
      danger: true,
      confirm: {
        title: t("ratioTask.detail.confirm.deleteTitle"),
        description: t("ratioTask.detail.confirm.deleteDesc"),
        okText: t("ratioTask.detail.confirm.okText"),
        cancelText: t("ratioTask.detail.confirm.cancelText"),
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDelete,
    },
  ];

  // 基本信息
  const items: DescriptionsProps["items"] = [
    {
      key: "id",
      label: t("ratioTask.detail.labels.id"),
      children: ratioTask.id,
    },
    {
      key: "name",
      label: t("ratioTask.detail.labels.name"),
      children: ratioTask.name,
    },
    {
      key: "totals",
      label: t("ratioTask.detail.labels.targetCount"),
      children: ratioTask.totals,
    },
    {
      key: "dataset",
      label: t("ratioTask.detail.labels.targetDataset"),
      children: (
        ratioTask.target_dataset_name ? (
          <Link to={`/data/management/detail/${ratioTask.target_dataset_id}`}>
            {ratioTask.target_dataset_name}
          </Link>
        ) : (
          ratioTask?.target_dataset && ratioTask?.target_dataset.name ? (
            <Link to={`/data/management/detail/${ratioTask?.target_dataset.id}`}>
              {ratioTask?.target_dataset.name}
            </Link>
          ) : (
            t("dataManagement.defaults.none")
          )
        )
      ),
    },
    {
      key: "status",
      label: t("ratioTask.detail.labels.status"),
      children: (
        <Badge color={ratioTask.status?.color} text={ratioTask.status?.label} />
      ),
    },
    {
      key: "createdBy",
      label: t("ratioTask.detail.labels.createdBy"),
      children: ratioTask.createdBy || t("dataManagement.defaults.unknown"),
    },
    {
      key: "createdAt",
      label: t("ratioTask.detail.labels.createdAt"),
      children: ratioTask.createdAt,
    },
    {
      key: "updatedAt",
      label: t("ratioTask.detail.labels.updatedAt"),
      children: ratioTask.updatedAt,
    },
    {
      key: "description",
      label: t("ratioTask.detail.labels.description"),
      children: ratioTask.description || t("dataManagement.defaults.none"),
    },
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <Breadcrumb items={navigateItems} />
      {/* Header */}
      <DetailHeader
        data={ratioTask}
        statistics={ratioTask?.statistics || []}
        operations={operations}
      />
      {/* <DataMetrics /> */}
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full overflow-auto">
          {activeTab === "overview" && (
            <>
              <Descriptions
                title={t("ratioTask.detail.labels.basicInfo")}
                layout="vertical"
                size="small"
                items={items}
                column={5}
              />
              {/* <RatioDisplay /> */}
            </>
          )}
          {activeTab === "analysis" && <DataRatioChart />}
          {activeTab === "config" && (
            <div className="bg-gray-50 rounded-lg p-4 font-mono text-xs overflow-x-auto">
              <pre className="text-gray-700 whitespace-pre-wrap break-words">
                {JSON.stringify(
                  {
                    id: ratioTask.id,
                    name: ratioTask.name,
                    type: ratioTask.type,
                    status: ratioTask.status,
                    strategy: ratioTask.strategy,
                    sourceDatasets: ratioTask.sourceDatasets,
                    targetRatio: ratioTask.targetRatio,
                    outputPath: ratioTask.outputPath,
                    createdAt: ratioTask.createdAt,
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
