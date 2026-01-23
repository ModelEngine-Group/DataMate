import { useEffect, useState } from "react";
import {Breadcrumb, App, Tabs} from "antd";
import {
  Play,
  Pause,
  Clock,
  CheckCircle,
  AlertCircle,
  Trash2,
  Activity, LayoutList,
} from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import { Link, useNavigate, useParams } from "react-router";
import {
  deleteCleaningTaskByIdUsingDelete,
  executeCleaningTaskUsingPost,
  queryCleaningTaskByIdUsingGet, queryCleaningTaskLogByIdUsingGet, queryCleaningTaskResultByIdUsingGet,
  stopCleaningTaskUsingPost,
} from "../cleansing.api";
import {mapTask, TaskStatusMap} from "../cleansing.const";
import {CleansingResult, TaskStatus} from "@/pages/DataCleansing/cleansing.model";
import BasicInfo from "./components/BasicInfo";
import OperatorTable from "./components/OperatorTable";
import FileTable from "./components/FileTable";
import LogsTable from "./components/LogsTable";
import {formatExecutionDuration} from "@/utils/unit.ts";
import {ReloadOutlined} from "@ant-design/icons";

// 任务详情页面组件
export default function CleansingTaskDetail() {
  const { id = "" } = useParams(); // 获取动态路由参数
  const { message } = App.useApp();
  const navigate = useNavigate();

  const fetchTaskDetail = async () => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTaskByIdUsingGet(id);
      setTask(mapTask(data));
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

  const [result, setResult] = useState<CleansingResult[]>();

  const fetchTaskResult = async () => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTaskResultByIdUsingGet(id);
      setResult(data);
    } catch (error) {
      message.error("获取清洗结果失败");
      navigate("/data/cleansing/task-detail/" + id);
    }
  };

  const [taskLog, setTaskLog] = useState();

  const fetchTaskLog = async (retryCount: number) => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTaskLogByIdUsingGet(id, retryCount);
      setTaskLog(data);
    } catch (error) {
      message.error("获取清洗日志失败");
      navigate("/data/cleansing/task-detail/" + id);
    }
  };

  const handleRefresh = async () => {
    fetchTaskDetail();
    {activeTab === "files" && await fetchTaskResult()}
    {activeTab === "logs" && await fetchTaskLog(task.retryCount)}
  };

  useEffect(() => {
    fetchTaskDetail();
  }, [id]);

  const [task, setTask] = useState(null);
  const [activeTab, setActiveTab] = useState("basic");

  const headerData = {
    ...task,
    icon: <LayoutList className="w-8 h-8" />,
    status: TaskStatusMap[task?.status],
    createdAt: task?.createdAt,
    lastUpdated: task?.updatedAt,
  };

  const statistics = [
    {
      icon: <Clock className="w-4 h-4 text-blue-500" />,
      label: "总耗时",
      value: formatExecutionDuration(task?.startedAt, task?.finishedAt) || "--",
    },
    {
      icon: <CheckCircle className="w-4 h-4 text-green-500" />,
      label: "成功文件",
      value: task?.progress?.succeedFileNum || "0",
    },
    {
      icon: <AlertCircle className="w-4 h-4 text-red-500" />,
      label: "失败文件",
      value: (task?.status.value === TaskStatus.RUNNING || task?.status.value === TaskStatus.PENDING)  ?
        task?.progress.failedFileNum :
        task?.progress?.totalFileNum - task?.progress.succeedFileNum,
    },
    {
      icon: <Activity className="w-4 h-4 text-purple-500" />,
      label: "成功率",
      value: task?.progress?.successRate ? task?.progress?.successRate + "%" : "--",
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
    ...([TaskStatus.PENDING, TaskStatus.STOPPED, TaskStatus.FAILED].includes(task?.status?.value)
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
      key: "refresh",
      label: "更新任务",
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: handleRefresh,
    },
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
      label: "基本信息",
    },
    {
      key: "operators",
      label: "处理算子",
    },
    {
      key: "files",
      label: "处理文件",
    },
    {
      key: "logs",
      label: "运行日志",
    },
  ];

  const breadItems = [
    {
      title: <Link to="/data/cleansing">数据处理</Link>,
    },
    {
      title: "清洗任务详情",
    },
  ];

  return (
    <>
      <Breadcrumb items={breadItems} />
      <div className="mb-4 mt-4">
        <DetailHeader
          data={headerData}
          statistics={statistics}
          operations={operations}
        />
      </div>
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full flex-1 overflow-auto">
          {activeTab === "basic" && (
            <BasicInfo task={task} />
          )}
          {activeTab === "operators" && <OperatorTable task={task} />}
          {activeTab === "files" && <FileTable result={result} fetchTaskResult={fetchTaskResult} />}
          {activeTab === "logs" && <LogsTable taskLog={taskLog} fetchTaskLog={fetchTaskLog} retryCount={task.retryCount} />}
        </div>
      </div>
    </>
  );
}
