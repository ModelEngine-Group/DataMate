import { useState } from "react";
import { Tabs, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { Plus, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router";
import InstructionTemplateTab from "./components/InstructionTemplateTab";
import SynthesisTaskTab from "./components/SynthesisTaskTab";

export default function DataSynthesisPage() {
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
          <h2 className="text-xl font-bold text-gray-900">数据合成</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => {
              navigate("/data/synthesis/task/create-template");
            }}
            icon={<PlusOutlined />}
          >
            创建模板
          </Button>
          <Button
            type="primary"
            onClick={() => navigate("/data/synthesis/task/create")}
            icon={<PlusOutlined />}
          >
            创建合成任务
          </Button>
        </div>
      </div>

      <Tabs
        items={[
          { key: "tasks", label: "合成任务", children: <SynthesisTaskTab /> },
          {
            key: "templates",
            label: "指令模板",
            children: <InstructionTemplateTab />,
          },
        ]}
        activeKey={activeTab}
        onChange={setActiveTab}
      ></Tabs>
    </div>
  );
}
