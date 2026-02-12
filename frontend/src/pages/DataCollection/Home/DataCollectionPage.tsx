import { useEffect, useState } from "react";
import { Button, Tabs } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import TaskManagement from "./TaskManagement";
import Execution from "./Execution.tsx";
import TemplateManagement from "./TemplateManagement";
import { useLocation, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";

export default function DataCollection() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
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
          <h1 className="text-xl font-bold text-gray-900 mb-2">{t("dataCollection.title")}</h1>
        </div>
        <div>
          <Button
            type="primary"
            onClick={() => navigate("/data/collection/create-task")}
            icon={<PlusOutlined />}
          >
            {t("common.actions.createTask")}
          </Button>
        </div>
      </div>
      <Tabs
        activeKey={activeTab}
        items={[
          { label: t("dataCollection.tabs.taskManagement"), key: "task-management" },
          { label: t("dataCollection.tabs.taskExecution"), key: "task-execution" },
          { label: t("dataCollection.tabs.taskTemplate"), key: "task-template" },
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
