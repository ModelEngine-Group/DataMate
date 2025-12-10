import { formatDateTime } from "@/utils/unit";
import { BarChart3 } from "lucide-react";
import { EvaluationStatus, EvaluationTask } from "@/pages/DataEvaluation/evaluation.model.ts";

export const TASK_TYPES = [
  { label: 'QA评估', value: 'QA' },
  { label: 'COT评估', value: 'COT' },
];

export const EVAL_METHODS = [
  { label: '模型自动评估', value: 'AUTO' },
];

export const getEvalType = (type: string) => {
  return TASK_TYPES.find((item) => item.value === type)?.label;
};

export const getEvalMethod = (type: string) => {
  return EVAL_METHODS.find((item) => item.value === type)?.label;
};

export const getSource = (type: string) => {
  switch (type) {
    case "DATASET":
      return "数据集 - ";
    case "SYNTHESIS":
      return "合成任务 - ";
    default:
      return "-";
  }
};

export const evalTaskStatusMap: Record<
  string,
  {
    value: EvaluationStatus;
    label: string;
    color: string;
  }
> = {
  [EvaluationStatus.PENDING]: {
    value: EvaluationStatus.PENDING,
    label: "等待中",
    color: "gray",
  },
  [EvaluationStatus.RUNNING]: {
    value: EvaluationStatus.RUNNING,
    label: "运行中",
    color: "blue",
  },
  [EvaluationStatus.COMPLETED]: {
    value: EvaluationStatus.COMPLETED,
    label: "已完成",
    color: "green",
  },
  [EvaluationStatus.FAILED]: {
    value: EvaluationStatus.FAILED,
    label: "失败",
    color: "red",
  },
  [EvaluationStatus.PAUSED]: {
    value: EvaluationStatus.PAUSED,
    label: "已暂停",
    color: "orange",
  },
};

export function mapEvaluationTask(task: Partial<EvaluationTask>): EvaluationTask {
  return {
    ...task,
    status: evalTaskStatusMap[task.status || EvaluationStatus.PENDING],
    createdAt: formatDateTime(task.createdAt),
    updatedAt: formatDateTime(task.updatedAt),
    description: task.description,
    icon: <BarChart3 />,
    iconColor: task.ratio_method === "DATASET" ? "bg-blue-100" : "bg-green-100",
    statistics: [
      {
        label: "任务类型",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: (task.taskType ?? 0).toLocaleString(),
      },
      {
        label: "评估方式",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: (task.evalMethod ?? 0).toLocaleString(),
      },
      {
        label: "数据源",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: (task.sourceName ?? 0).toLocaleString(),
      },
    ],
  };
}
