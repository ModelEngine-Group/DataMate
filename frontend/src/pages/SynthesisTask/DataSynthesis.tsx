import { useState } from "react";
import { Tabs, Button } from "antd";
import { Plus, ArrowRight } from "lucide-react";
import DataAnnotation from "../DataAnnotation/Annotate/components/TextAnnotation";
import { useNavigate } from "react-router";
import InstructionTemplateTab from "./components/InstructionTemplateTab";
import SynthesisTaskTab from "./components/SynthesisTaskTab";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

export default function DataSynthesisPage() {
  return <DevelopmentInProgress showTime="2025.11.30" />;
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
        <DataAnnotation
          task={undefined}
          currentFileIndex={0}
          onSaveAndNext={function (): void {
            throw new Error("Function not implemented.");
          }}
          onSkipAndNext={function (): void {
            throw new Error("Function not implemented.");
          }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className=" p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-gray-900">数据合成</h2>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={() => {
                navigate("/data/synthesis/task/create-template");
              }}
            >
              <Plus className="w-3 h-3 mr-1" />
              创建模板
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/data/synthesis/task/create")}
            >
              <Plus className="w-3 h-3 mr-1" />
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
    </div>
  );
}
