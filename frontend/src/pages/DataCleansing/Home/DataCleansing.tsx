import { useState } from "react";
import { Tabs, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router";
import TaskList from "./components/TaskList";
import TemplateList from "./components/TemplateList";
import ProcessFlowDiagram from "./components/ProcessFlowDiagram";

export default function DataProcessingPage() {
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState<"tasks" | "templates">(
    "tasks"
  );

  return (
    <div className="h-full flex flex-col">
      <div style={{ marginBottom: 24 }}>
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold">数据清洗</h1>
          <div className="flex gap-2">
            <Button
              icon={<PlusOutlined />}
              onClick={() => navigate("/data/cleansing/create-template")}
            >
              创建清洗模板
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate("/data/cleansing/create-task")}
            >
              创建清洗任务
            </Button>
          </div>
        </div>
      </div>
      <ProcessFlowDiagram />
      <Tabs
        activeKey={currentView}
        onChange={(key) => setCurrentView(key as any)}
        items={[
          {
            key: "tasks",
            label: "任务列表",
          },
          {
            key: "templates",
            label: "模板管理",
          },
        ]}
      />
      {currentView === "tasks" && <TaskList />}
      {currentView === "templates" && <TemplateList />}
    </div>
  );
}
