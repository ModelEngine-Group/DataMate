import { formatDate } from "@/utils/unit";
import { BarChart3 } from "lucide-react";
import { EvaluationStatus, EvaluationTask } from "@/pages/DataEvaluation/evaluation.model.ts";

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
    createdAt: formatDate(task.createdAt),
    updatedAt: formatDate(task.updatedAt),
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
