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

export type TFunction = (key: string, options?: any) => string;

export function getTaskTypes(t: TFunction) {
  return [
    { label: t("dataEvaluation.create.taskTypes.qa"), value: "QA" },
    { label: t("dataEvaluation.create.taskTypes.cot"), value: "COT" },
  ];
}

export function getEvalMethods(t: TFunction) {
  return [
    { label: t("dataEvaluation.create.evalMethods.auto"), value: "AUTO" },
    { label: t("dataEvaluation.create.evalMethods.manual"), value: "MANUAL" },
  ];
}

export const getEvalType = (type: string, t?: TFunction) => {
  if (t) return getTaskTypes(t).find((item) => item.value === type)?.label;
  return TASK_TYPES.find((item) => item.value === type)?.label;
};

export const getEvalMethod = (type: string, t?: TFunction) => {
  if (t) return getEvalMethods(t).find((item) => item.value === type)?.label;
  return EVAL_METHODS.find((item) => item.value === type)?.label;
};

export const getSource = (type: string, t?: TFunction) => {
  if (t) {
    switch (type) {
      case "DATASET":
        return t("dataEvaluation.create.source.dataset");
      case "SYNTHESIS":
        return t("dataEvaluation.create.source.synthesis");
      default:
        return t("dataEvaluation.create.source.default");
    }
  }
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
  STOPPED: {
    value: EvaluationStatus.COMPLETED as unknown as EvaluationStatus,
    label: "已停止",
    color: "default",
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

export function getEvalTaskStatusMap(
  t: TFunction
): Record<
  string,
  {
    value: string;
    label: string;
    color: string;
  }
> {
  return {
    PENDING: { value: "PENDING", label: t("common.status.task.pending"), color: "gray" },
    RUNNING: { value: "RUNNING", label: t("common.status.task.running"), color: "blue" },
    COMPLETED: { value: "COMPLETED", label: t("common.status.task.completed"), color: "green" },
    FAILED: { value: "FAILED", label: t("common.status.task.failed"), color: "red" },
    STOPPED: { value: "STOPPED", label: t("common.status.task.stopped"), color: "default" },
    PAUSED: { value: "PAUSED", label: t("common.status.task.paused"), color: "orange" },
  };
}

export function mapEvaluationTask(
  task: Partial<EvaluationTask>,
  t?: TFunction
): EvaluationTask {
  const statusMap = t ? getEvalTaskStatusMap(t) : evalTaskStatusMap;
  return {
    ...task,
    status: statusMap[task.status || EvaluationStatus.PENDING],
    createdAt: formatDateTime(task.createdAt),
    updatedAt: formatDateTime(task.updatedAt),
    description: task.description,
    icon: <BarChart3 />,
    iconColor: "#A78BFA",
    statistics: [
      {
        label: t ? t("dataEvaluation.detail.labels.taskType") : "任务类型",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: t ? getEvalType(task.taskType, t) : (task.taskType ?? 0).toLocaleString(),
      },
      {
        label: t ? t("dataEvaluation.detail.labels.evalMethod") : "评估方式",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: t ? getEvalMethod(task.evalMethod, t) : (task.evalMethod ?? 0).toLocaleString(),
      },
      {
        label: t ? t("dataEvaluation.detail.labels.evalData") : "数据源",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: t ? `${getSource(task.sourceType, t)}${task.sourceName || ""}` : (task.sourceName ?? 0).toLocaleString(),
      },
    ],
  };
}
