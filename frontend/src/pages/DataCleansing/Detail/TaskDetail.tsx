import { useEffect, useState } from "react";
import { Card, Breadcrumb, App } from "antd";
import {
  Play,
  Pause,
  Clock,
  CheckCircle,
  AlertCircle,
  Database,
  Trash2,
  Download,
  Activity,
} from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import { Link, useNavigate, useParams } from "react-router";
import {
  deleteCleaningTaskByIdUsingDelete,
  executeCleaningTaskUsingPost,
  queryCleaningTaskByIdUsingGet,
  stopCleaningTaskUsingPost,
} from "../cleansing.api";
import { TaskStatusMap } from "../cleansing.const";
import { TaskStatus } from "@/pages/DataCleansing/cleansing.model";
import BasicInfo from "./components/BasicInfo";
import OperatorTable from "./components/OperatorTable";
import FileTable from "./components/FileTable";
import LogsTable from "./components/LogsTable";

// 任务详情页面组件
export default function CleansingTaskDetail() {
  const { id = "" } = useParams(); // 获取动态路由参数
  const { message } = App.useApp();
  const navigate = useNavigate();

  const fetchTaskDetail = async () => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTaskByIdUsingGet(id);
      setTask(data);
    } catch (error) {
      message.error("获取任务详情失败");
      navigate("/data/cleansing");
    }
  };

  const pauseTask = async () => {
    await stopCleaningTaskUsingPost(id);
    message.success("任务已暂停");
    fetchTaskDetail();
  };

  const startTask = async () => {
    await executeCleaningTaskUsingPost(id);
    message.success("任务已启动");
    fetchTaskDetail();
  };

  const deleteTask = async () => {
    await deleteCleaningTaskByIdUsingDelete(id);
    message.success("任务已删除");
    navigate("/data/cleansing");
  };

  useEffect(() => {
    fetchTaskDetail();
  }, [id]);

  const [task, setTask] = useState(null);
  const [activeTab, setActiveTab] = useState("basic");

  const headerData = {
    ...task,
    icon: <Database className="w-8 h-8" />,
    status: TaskStatusMap[task?.status],
    createdAt: task?.startTime,
    lastUpdated: task?.updatedAt,
  };

  const statistics = [
    {
      icon: <Clock className="w-4 h-4 text-blue-500" />,
      label: "总耗时",
      value: task?.duration || "--",
    },
    {
      icon: <CheckCircle className="w-4 h-4 text-green-500" />,
      label: "成功文件",
      value: task?.successFiles || "--",
    },
    {
      icon: <AlertCircle className="w-4 h-4 text-red-500" />,
      label: "失败文件",
      value: task?.failedFiles || "--",
    },
    {
      icon: <Activity className="w-4 h-4 text-purple-500" />,
      label: "成功率",
      value: `${task?.progress}%`,
    },
  ];

  const operations = [
    ...(task?.status === TaskStatus.RUNNING
      ? [
          {
            key: "pause",
            label: "暂停任务",
            icon: <Pause className="w-4 h-4" />,
            onClick: pauseTask,
          },
        ]
      : []),
    ...(task?.status === TaskStatus.PENDING
      ? [
          {
            key: "start",
            label: "执行任务",
            icon: <Play className="w-4 h-4" />,
            onClick: startTask,
          },
        ]
      : []),
    {
      key: "delete",
      label: "删除任务",
      icon: <Trash2 className="w-4 h-4" />,
      danger: true,
      onClick: deleteTask,
    },
  ];

  const tabList = [
    {
      key: "basic",
      tab: "基本信息",
      children: <BasicInfo task={task} />,
    },
    {
      key: "operators",
      tab: "处理算子",
      children: <OperatorTable task={task} />,
    },
    {
      key: "files",
      tab: "处理文件",
      children: <FileTable task={task} />,
    },
    { key: "logs", tab: "运行日志", children: <LogsTable task={task} /> },
  ];

  const breadItems = [
    {
      title: <Link to="/data/cleansing">数据清洗</Link>,
    },
    {
      title: "清洗任务详情",
    },
  ];

  return (
    <div className="min-h-screen">
      <Breadcrumb items={breadItems} />
      <div className="mb-4 mt-4">
        <DetailHeader
          data={headerData}
          statistics={statistics}
          operations={operations}
        />
      </div>
      <Card
        tabList={tabList}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      ></Card>
    </div>
  );
}
