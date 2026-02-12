import { useState } from "react";
import { Tabs, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { Plus, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import InstructionTemplateTab from "./components/InstructionTemplateTab";
import SynthesisTaskTab from "./components/SynthesisTaskTab";

export default function DataSynthesisPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("tasks");
  const [showAnnotatePage, setShowAnnotatePage] = useState(false);

  if (showAnnotatePage) {
    return (
      <div>
        <div className="flex">
          <Button
            onClick={() => setShowAnnotatePage(false)}
            className="hover:bg-white/70"
          >
            <ArrowRight className="w-4 h-4 rotate-180 mr-2" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-gray-900">{t('synthesisTask.title')}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => {
              navigate("/data/synthesis/task/create-template");
            }}
            icon={<PlusOutlined />}
          >
            {t('synthesisTask.actions.createTemplate')}
          </Button>
          <Button
            type="primary"
            onClick={() => navigate("/data/synthesis/task/create")}
            icon={<PlusOutlined />}
          >
            {t('synthesisTask.actions.createSynthesisTask')}
          </Button>
        </div>
      </div>

      <Tabs
        items={[
          { key: "tasks", label: t('synthesisTask.tabs.tasks'), children: <SynthesisTaskTab /> },
          {
            key: "templates",
            label: t('synthesisTask.tabs.templates'),
            children: <InstructionTemplateTab />,
          },
        ]}
        activeKey={activeTab}
        onChange={setActiveTab}
      ></Tabs>
    </div>
  );
}
