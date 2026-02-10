import {
  CollectionTask,
  LogStatus,
  SyncMode,
  TaskExecution,
  TaskStatus,
  TriggerType,
} from "./collection.model";
import { formatDateTime } from "@/utils/unit.ts";

export function getStatusMap(
  t: (key: string) => string
): Record<TaskStatus, { label: string; color: string; value: TaskStatus }> {
  return {
    [TaskStatus.RUNNING]: {
      label: t("common.status.task.running"),
      color: "blue",
      value: TaskStatus.RUNNING,
    },
    [TaskStatus.STOPPED]: {
      label: t("common.status.task.stopped"),
      color: "gray",
      value: TaskStatus.STOPPED,
    },
    [TaskStatus.FAILED]: {
      label: t("common.status.task.failed"),
      color: "red",
      value: TaskStatus.FAILED,
    },
    [TaskStatus.COMPLETED]: {
      label: t("common.status.task.completed"),
      color: "green",
      value: TaskStatus.COMPLETED,
    },
    [TaskStatus.DRAFT]: {
      label: t("common.status.task.draft"),
      color: "orange",
      value: TaskStatus.DRAFT,
    },
    [TaskStatus.PENDING]: {
      label: t("common.status.task.pending"),
      color: "cyan",
      value: TaskStatus.PENDING,
    },
  };
}

export function getSyncModeMap(
  t: (key: string) => string
): Record<SyncMode, { label: string; value: SyncMode; color: string }> {
  return {
    [SyncMode.ONCE]: {
      label: t("dataCollection.createTask.syncConfig.syncMode.once"),
      value: SyncMode.ONCE,
      color: "orange",
    },
    [SyncMode.SCHEDULED]: {
      label: t("dataCollection.createTask.syncConfig.syncMode.scheduled"),
      value: SyncMode.SCHEDULED,
      color: "blue",
    },
  };
}

export function getLogStatusMap(
  t: (key: string) => string
): Record<LogStatus, { label: string; color: string; value: LogStatus }> {
  return {
    [LogStatus.SUCCESS]: {
      label: t("dataCollection.execution.filters.success"),
      color: "green",
      value: LogStatus.SUCCESS,
    },
    [LogStatus.FAILED]: {
      label: t("dataCollection.execution.filters.failed"),
      color: "red",
      value: LogStatus.FAILED,
    },
    [LogStatus.RUNNING]: {
      label: t("dataCollection.execution.filters.running"),
      color: "blue",
      value: LogStatus.RUNNING,
    },
  };
}

export function getLogTriggerTypeMap(
  t: (key: string) => string
): Record<TriggerType, { label: string; value: TriggerType }> {
  return {
    [TriggerType.MANUAL]: { label: t("dataCollection.execution.triggerType.manual"), value: TriggerType.MANUAL },
    [TriggerType.SCHEDULED]: { label: t("dataCollection.execution.triggerType.scheduled"), value: TriggerType.SCHEDULED },
    [TriggerType.API]: { label: t("dataCollection.execution.triggerType.api"), value: TriggerType.API },
  };
}

export function mapCollectionTask(task: CollectionTask, t: (key: string) => string): any {
  const statusMap = getStatusMap(t);
  const syncModeMap = getSyncModeMap(t);
  return {
    ...task,
    status: statusMap[task.status],
    syncMode: syncModeMap[task.syncMode],
    createdAt: formatDateTime(task.createdAt),
    updatedAt: formatDateTime(task.updatedAt),
  };
}

export function mapTaskExecution(execution: TaskExecution, t: (key: string) => string): any {
  const statusMap = getStatusMap(t);
  return {
    ...execution,
    status: statusMap[execution.status as TaskStatus],
    startedAt: formatDateTime(execution.startedAt),
    completedAt: formatDateTime(execution.completedAt),
  };
}
