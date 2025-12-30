import { useEffect, useState } from "react";
import { Button, Tabs } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import TaskManagement from "./TaskManagement";
import Execution from "./Execution.tsx";
import TemplateManagement from "./TemplateManagement";
import { useLocation, useNavigate } from "react-router";

export default function DataCollection() {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("task-management");
  const [taskId, setTaskId] = useState<string | undefined>(undefined);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get("tab") || undefined;
    const nextTaskId = params.get("taskId") || undefined;

    if (tab === "task-execution" || tab === "task-management" || tab === "task-template") {
      setActiveTab(tab);
    }
    setTaskId(nextTaskId);
  }, [location.search]);

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
          { label: "执行记录", key: "task-execution" },
          { label: "模板管理", key: "task-template" },
        ]}
        onChange={(tab) => {
          setActiveTab(tab);
          setTaskId(undefined);
          const params = new URLSearchParams();
          params.set("tab", tab);
          navigate({ pathname: location.pathname, search: params.toString() }, { replace: true });
        }}
      />
      {activeTab === "task-management" ? <TaskManagement /> : null}
      {activeTab === "task-execution" ? <Execution taskId={taskId} /> : null}
      {activeTab === "task-template" ? <TemplateManagement /> : null}
    </div>
  );
}
