import { useState } from "react";
import { Button, Tabs } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import TaskManagement from "./TaskManagement";
import ExecutionLog from "./ExecutionLog";
import { useNavigate } from "react-router";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

export default function DataCollection() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("task-management");

  // return <DevelopmentInProgress showTime="2025.10.30" />;

  return (
    <div className="gap-4 h-full flex flex-col">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">数据归集</h1>
        </div>
        <div>
          <Button
            type="primary"
            onClick={() => navigate("/data/collection/create-task")}
            icon={<PlusOutlined />}
          >
            创建任务
          </Button>
        </div>
      </div>
      <Tabs
        activeKey={activeTab}
        items={[
          { label: "任务管理", key: "task-management" },
          { label: "执行日志", key: "execution-log" },
        ]}
        onChange={(tab) => {
          setActiveTab(tab);
        }}
      />
      {activeTab === "task-management" ? <TaskManagement /> : <ExecutionLog />}
    </div>
  );
}
