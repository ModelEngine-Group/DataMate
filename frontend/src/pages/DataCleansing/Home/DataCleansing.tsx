import { useEffect, useState } from "react";
import { Tabs, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import TaskList from "./components/TaskList";
import TemplateList from "./components/TemplateList";
import ProcessFlowDiagram from "./components/ProcessFlowDiagram";
import { useSearchParams } from "@/hooks/useSearchParams";

export default function DataProcessingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const urlParams = useSearchParams();
  const [currentView, setCurrentView] = useState<"task" | "template">("task");

  useEffect(() => {
    if (urlParams.view) {
      setCurrentView(urlParams.view);
    }
  }, [urlParams]);

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">{t("dataCleansing.title")}</h1>
        <div className="flex gap-2">
          <Button
            icon={<PlusOutlined />}
            onClick={() => navigate("/data/cleansing/create-template")}
          >
            {t("dataCleansing.actions.createTemplate")}
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate("/data/cleansing/create-task")}
          >
            {t("dataCleansing.actions.createTask")}
          </Button>
        </div>
      </div>
      <ProcessFlowDiagram />
      <Tabs
        activeKey={currentView}
        onChange={(key) => setCurrentView(key as any)}
        items={[
          {
            key: "task",
            label: t("dataCleansing.tabs.taskList"),
          },
          {
            key: "template",
            label: t("dataCleansing.tabs.templateManagement"),
          },
        ]}
      />
      {currentView === "task" && <TaskList />}
      {currentView === "template" && <TemplateList />}
    </div>
  );
}
