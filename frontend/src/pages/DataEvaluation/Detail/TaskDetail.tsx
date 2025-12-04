import { Link, useParams } from "react-router";
import { Tabs, Spin, message, Breadcrumb } from 'antd';
import { LayoutList, Clock } from "lucide-react";
import { useEffect, useState } from 'react';
import { getEvaluationTaskByIdUsingGet, queryEvaluationItemsUsingGet } from '../evaluation.api';
import { EvaluationTask, EvaluationStatus } from '../evaluation.model';
import DetailHeader from "@/components/DetailHeader.tsx";
import {TaskStatusMap} from "@/pages/DataCleansing/cleansing.const.tsx";
import EvaluationItems from "@/pages/DataEvaluation/Detail/components/EvaluationItems.tsx";
import Overview from "@/pages/DataEvaluation/Detail/components/Overview.tsx";

const tabList = [
  {
    key: "overview",
    label: "概览",
  },
  {
    key: "evaluationItems",
    label: "评估详情",
  }
];

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
      setTask(response.data);
    } catch (error) {
      message.error('Failed to fetch task details');
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
      message.error('Failed to fetch evaluation items');
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
    return <div>Task not found</div>;
  }

  const breadItems = [
    {
      title: <Link to="/data/evaluation">数据评估</Link>,
    },
    {
      title: "数据评估详情",
    },
  ];

  const headerData = {
    ...task,
    icon: <LayoutList className="w-8 h-8" />,
    status: TaskStatusMap[task?.status],
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
