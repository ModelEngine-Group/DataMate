import { useEffect, useMemo, useState, useCallback } from "react";
import {
  Breadcrumb,
  App,
  Tabs,
  Button,
  Card,
  Progress,
  Badge,
  Descriptions,
  DescriptionsProps,
} from "antd";
import { ReloadOutlined, DeleteOutlined } from "@ant-design/icons";
import DetailHeader from "@/components/DetailHeader";
import { Link, useNavigate, useParams } from "react-router";
import {
  getRatioTaskByIdUsingGet,
  deleteRatioTasksUsingDelete,
} from "@/pages/RatioTask/ratio.api";
import { post } from "@/utils/request";
import type { RatioTaskItem } from "@/pages/RatioTask/ratio.model";
import { mapRatioTask } from "../ratio.const";
import { Copy, Pause, PlayIcon } from "lucide-react";

const tabList = [
  {
    key: "overview",
    label: "概览",
  },
  {
    key: "analysis",
    label: "配比分析",
  },
  {
    key: "config",
    label: "配比配置",
  },
];

export default function RatioTaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const { message } = App.useApp();
  const [ratioTask, setRatioTask] = useState<RatioTaskItem>(
    {} as RatioTaskItem
  );

  const navigateItems = useMemo(
    () => [
      {
        title: <Link to="/data/synthesis/ratio-task">首页</Link>,
      },
      {
        title: ratioTask.name || "配比任务详情",
      },
    ],
    [ratioTask]
  );

  const fetchRatioTask = useCallback(async () => {
    const { data } = await getRatioTaskByIdUsingGet(id as string);
    setRatioTask(mapRatioTask(data));
  }, [id]);

  useEffect(() => {
    fetchRatioTask();
  }, []);

  const handleRefresh = useCallback(
    async (showMessage = true) => {
      await fetchRatioTask();
      if (showMessage) message.success({ content: "任务数据刷新成功" });
    },
    [fetchRatioTask, message]
  );

  const handleDelete = async () => {
    await deleteRatioTasksUsingDelete(id as string);
    navigate("/ratio/task");
    message.success("配比任务删除成功");
  };

  const handleExecute = async () => {
    await post(`/api/synthesis/ratio-task/${id}/execute`);
    handleRefresh();
    message.success("任务已启动");
  };

  const handleStop = async () => {
    await post(`/api/synthesis/ratio-task/${id}/stop`);
    handleRefresh();
    message.success("任务已停止");
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
      key: "execute",
      label: "启动",
      icon: <PlayIcon className="w-4 h-4 text-gray-500" />,
      onClick: handleExecute,
      disabled: ratioTask.status === "RUNNING",
    },
    {
      key: "stop",
      label: "停止",
      icon: <Pause className="w-4 h-4 text-gray-500" />,
      onClick: handleStop,
      disabled: ratioTask.status !== "RUNNING",
    },
    {
      key: "refresh",
      label: "刷新",
      icon: <ReloadOutlined />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: "删除",
      danger: true,
      confirm: {
        title: "确认删除该配比任务？",
        description: "删除后该任务将无法恢复，请谨慎操作。",
        okText: "删除",
        cancelText: "取消",
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
      label: "ID",
      children: ratioTask.id,
    },
    {
      key: "name",
      label: "名称",
      children: ratioTask.name,
    },
    {
      key: "dataset",
      label: "目标数据集",
      children: (
        <Link to={`/data/management/detail/${ratioTask.target_dataset_id}`}>
          {ratioTask.target_dataset_name}
        </Link>
      ),
    },
    {
      key: "status",
      label: "数据大小",
      children: (
        <Badge color={ratioTask.status?.color} text={ratioTask.status?.label} />
      ),
    },
    {
      key: "type",
      label: "类型",
      children: ratioTask.type || "未知",
    },
    {
      key: "status",
      label: "状态",
      children: ratioTask?.status?.label || "未知",
    },
    {
      key: "createdBy",
      label: "创建者",
      children: ratioTask.createdBy || "未知",
    },
    {
      key: "targetLocation",
      label: "输出路径",
      children: ratioTask.targetLocation || "未知",
    },
    {
      key: "createdAt",
      label: "创建时间",
      children: ratioTask.createdAt,
    },
    {
      key: "updatedAt",
      label: "更新时间",
      children: ratioTask.updatedAt,
    },
    {
      key: "description",
      label: "描述",
      children: ratioTask.description || "无",
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
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full overflow-auto">
          {activeTab === "overview" && (
            <>
              <Descriptions
                title="基本信息"
                layout="vertical"
                size="small"
                items={items}
                column={5}
              />
              <h2 className="text-base font-semibold mt-8 mb-4">配比详情</h2>
              <div className="grid grid-cols-2 gap-4">
                {/* 目标配比 */}
                <Card title="目标配比">
                  <div className="space-y-4">
                    {ratioTask.targetRatio &&
                      Object.entries(ratioTask.targetRatio).map(
                        ([category, ratio]) => (
                          <div key={category} className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-gray-700">
                                {category}
                              </span>
                              <span className="text-sm font-semibold text-blue-600">
                                {ratioTask.ratio}%
                              </span>
                            </div>
                            <Progress value={ratio} className="h-2" />
                          </div>
                        )
                      )}
                  </div>
                </Card>

                {/* 当前配比 */}
                <Card title="当前配比">
                  <div className="space-y-4">
                    {ratioTask.currentRatio &&
                    Object.entries(ratioTask.currentRatio).length > 0 ? (
                      Object.entries(ratioTask.currentRatio)?.map(
                        ([category, ratio]) => (
                          <div key={category} className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-gray-700">
                                {category}
                              </span>
                              <span className="text-sm font-semibold text-green-600">
                                {ratioTask.ratio}%
                              </span>
                            </div>
                            <Progress value={ratio} className="h-2" />
                          </div>
                        )
                      )
                    ) : (
                      <p className="text-sm text-gray-500">等待处理开始</p>
                    )}
                  </div>
                </Card>
              </div>
            </>
          )}
          {activeTab === "analysis" && (
            <div className="text-center py-20 text-gray-500">
              配比分析功能正在开发中，敬请期待！
            </div>
          )}
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
