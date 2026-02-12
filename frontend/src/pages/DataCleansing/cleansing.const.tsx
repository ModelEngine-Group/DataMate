import {
  CleansingTask,
  CleansingTemplate,
  TaskStatus,
} from "@/pages/DataCleansing/cleansing.model";
import {
  formatBytes,
  formatDateTime,
  formatExecutionDuration,
} from "@/utils/unit";
import {
  ClockCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  PauseCircleOutlined,
} from "@ant-design/icons";
import { BrushCleaning, Layout } from "lucide-react";

export function getTaskStatusMap(t: (key: string) => string) {
  return {
    [TaskStatus.PENDING]: {
      label: t("dataCleansing.status.pending"),
      value: TaskStatus.PENDING,
      color: "gray",
      icon: <ClockCircleOutlined />,
    },
    [TaskStatus.RUNNING]: {
      label: t("dataCleansing.status.running"),
      value: TaskStatus.RUNNING,
      color: "blue",
      icon: <PlayCircleOutlined />,
    },
    [TaskStatus.COMPLETED]: {
      label: t("dataCleansing.status.completed"),
      value: TaskStatus.COMPLETED,
      color: "green",
      icon: <CheckCircleOutlined />,
    },
    [TaskStatus.FAILED]: {
      label: t("dataCleansing.status.failed"),
      value: TaskStatus.FAILED,
      color: "red",
      icon: <AlertOutlined />,
    },
    [TaskStatus.STOPPED]: {
      label: t("dataCleansing.status.stopped"),
      value: TaskStatus.STOPPED,
      color: "orange",
      icon: <PauseCircleOutlined />,
    },
  };
}

export const mapTask = (task: CleansingTask, t: (key: string) => string) => {
  const duration = formatExecutionDuration(task.startedAt, task.finishedAt);
  const before = formatBytes(task.beforeSize);
  const after = formatBytes(task.afterSize);
  const status = getTaskStatusMap(t)[task.status];
  const finishedAt = formatDateTime(task.finishedAt);
  const startedAt = formatDateTime(task.startedAt);
  const createdAt = formatDateTime(task.createdAt);
  return {
    ...task,
    ...task.progress,
    createdAt,
    startedAt,
    finishedAt,
    updatedAt: formatDateTime(
      new Date(Math.max(...[
        new Date(task.finishedAt).getTime(),
        new Date(task.startedAt).getTime(),
        new Date(task.createdAt).getTime()])).toISOString()),
    icon: <BrushCleaning className="w-full h-full" />,
    status,
    duration,
    before,
    after,
    statistics: [
      { label: t("dataCleansing.task.columns.progress"), value: `${task?.progress?.process || 0}%` },
      {
        label: t("dataCleansing.task.columns.duration"),
        value: duration,
      },
      {
        label: t("dataCleansing.task.columns.processedFiles"),
        value: task?.progress?.finishedFileNum || 0,
      },
      {
        label: t("dataCleansing.task.columns.totalFiles"),
        value: task?.progress?.totalFileNum || 0,
      },
    ],
    lastModified: formatDateTime(task.createdAt),
  };
};

export const mapTemplate = (template: CleansingTemplate, t: (key: string) => string) => {
  return {
      ...template,
      createdAt: formatDateTime(template.createdAt),
      updatedAt: formatDateTime(template.updatedAt),
      icon: <Layout className="w-full h-full" />,
      statistics: [{ label: t("dataCleansing.template.columns.operatorCount"), value: template.instance?.length ?? 0 }],
      lastModified: formatDateTime(template.updatedAt),
    }
};
