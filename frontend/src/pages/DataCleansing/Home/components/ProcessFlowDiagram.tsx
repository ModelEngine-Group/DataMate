import {
  ArrowRight,
  CheckCircle,
  Database,
  Play,
  Settings,
  Workflow,
  Zap,
} from "lucide-react";
import { useTranslation } from "react-i18next";

// 流程图组件
export default function ProcessFlowDiagram() {
  const { t } = useTranslation();
  const flowSteps = [
    {
      id: "start",
      label: t("dataCleansing.processFlow.start"),
      type: "start",
      icon: Play,
      color: "bg-green-500",
    },
    {
      id: "select",
      label: t("dataCleansing.processFlow.selectDataset"),
      type: "process",
      icon: Database,
      color: "bg-blue-500",
    },
    {
      id: "config",
      label: t("dataCleansing.steps.basicInfo"),
      type: "process",
      icon: Settings,
      color: "bg-purple-500",
    },
    {
      id: "operators",
      label: t("dataCleansing.steps.operatorOrchestration"),
      type: "process",
      icon: Workflow,
      color: "bg-orange-500",
    },
    {
      id: "execute",
      label: t("dataCleansing.actions.startTask"),
      type: "process",
      icon: Zap,
      color: "bg-red-500",
    },
    {
      id: "end",
      label: t("dataCleansing.processFlow.complete"),
      type: "end",
      icon: CheckCircle,
      color: "bg-green-500",
    },
  ];

  return (
    <div className="border-card p-6">
      <div className="w-full flex items-center justify-center">
        <div className="w-full flex items-center space-x-12">
          {flowSteps.map((step, index) => {
            const IconComponent = step.icon;
            return (
              <div key={step.id} className="flex-1 flex items-center">
                <div className="flex flex-col items-center w-full">
                  <div
                    className={`w-12 h-12 ${step.color} rounded-full flex items-center justify-center text-white shadow-lg`}
                  >
                    <IconComponent className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-medium text-gray-700 mt-2 text-center max-w-16">
                    {step.label}
                  </span>
                </div>
                {index < flowSteps.length - 1 && (
                  <ArrowRight className="w-6 h-6 text-gray-400 mx-3" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
