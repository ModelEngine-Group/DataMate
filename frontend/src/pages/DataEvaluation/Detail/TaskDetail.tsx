import { Link, useParams } from "react-router";
import { Tabs, Spin, message, Breadcrumb } from 'antd';
import { LayoutList, Clock } from "lucide-react";
import { useEffect, useState } from 'react';
import { getEvaluationTaskByIdUsingGet, queryEvaluationItemsUsingGet } from '../evaluation.api';
import { EvaluationTask, EvaluationStatus } from '../evaluation.model';
import DetailHeader from "@/components/DetailHeader.tsx";
import EvaluationItems from "@/pages/DataEvaluation/Detail/components/EvaluationItems.tsx";
import Overview from "@/pages/DataEvaluation/Detail/components/Overview.tsx";
import { useTranslation } from "react-i18next";
import { mapEvaluationTask } from "@/pages/DataEvaluation/evaluation.const.tsx";

interface EvaluationItem {
  id: string;
  content: string;
  status: EvaluationStatus;
  score?: number;
  dimensions: {
    id: string;
    name: string;
    score: number;
  }[];
  createdAt: string;
}

const EvaluationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(true);
  const [task, setTask] = useState<EvaluationTask | null>(null);
  const [items, setItems] = useState<EvaluationItem[]>([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  const fetchTaskDetail = async () => {
    try {
      const response = await getEvaluationTaskByIdUsingGet(id);
      setTask(mapEvaluationTask(response.data, t));
    } catch (error) {
      message.error(t("dataEvaluation.detail.messages.fetchTaskFailed"));
      console.error('Error fetching task detail:', error);
    }
  };

  const fetchEvaluationItems = async (page = 1, pageSize = 10) => {
    try {
      const response = await queryEvaluationItemsUsingGet({
        taskId: id,
        page: page,
        size: pageSize,
      });
      setItems(response.data.content || []);
      setPagination({
        ...pagination,
        current: page,
        total: response.data.totalElements || 0,
      });
    } catch (error) {
      message.error(t("dataEvaluation.detail.messages.fetchItemsFailed"));
      console.error('Error fetching evaluation items:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      setLoading(true);
      Promise.all([
        fetchTaskDetail(),
        fetchEvaluationItems(1, pagination.pageSize),
      ]).finally(() => setLoading(false));
    }
  }, [id]);

  if (loading && !task) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!task) {
    return <div>{t("dataEvaluation.detail.taskNotFound")}</div>;
  }

  const tabList = [
    {
      key: "overview",
      label: t("dataEvaluation.detail.tabs.overview"),
    },
    {
      key: "evaluationItems",
      label: t("dataEvaluation.detail.tabs.evaluationItems"),
    },
  ];

  const breadItems = [
    {
      title: <Link to="/data/evaluation">{t("dataEvaluation.detail.breadcrumb.home")}</Link>,
    },
    {
      title: t("dataEvaluation.detail.breadcrumb.detail"),
    },
  ];

  const headerData = {
    ...task,
    icon: <LayoutList className="w-8 h-8" />,
    status: task?.status,
    createdAt: task?.createdAt,
    lastUpdated: task?.updatedAt,
  };

  // 基本信息描述项
  const statistics = [
    {
      icon: <Clock className="text-blue-400 w-4 h-4" />,
      key: "time",
      value: task?.updatedAt,
    },
  ];

  const operations = []

  return (
    <>
      <Breadcrumb items={breadItems} />
      <div className="mb-4 mt-4">
        <div className="mb-4 mt-4">
          <DetailHeader
            data={headerData}
            statistics={statistics}
            operations={operations}
          />
        </div>
      </div>
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full overflow-auto">
          {activeTab === "overview" && <Overview task={task} />}
          {activeTab === "evaluationItems" && <EvaluationItems task={task} />}
        </div>
      </div>
    </>
  );
};

export default EvaluationDetailPage;
