import {
  CollectionTask,
  LogStatus,
  SyncMode, TaskExecution,
  TaskStatus,
  TriggerType,
} from "./collection.model";
import {formatDateTime} from "@/utils/unit.ts";

export const StatusMap: Record<
  TaskStatus,
  { label: string; color: string; value: TaskStatus }
> = {
  [TaskStatus.RUNNING]: {
    label: "运行",
    color: "blue",
    value: TaskStatus.RUNNING,
  },
  [TaskStatus.STOPPED]: {
    label: "停止",
    color: "gray",
    value: TaskStatus.STOPPED,
  },
  [TaskStatus.FAILED]: {
    label: "错误",
    color: "red",
    value: TaskStatus.FAILED,
  },
  [TaskStatus.COMPLETED]: {
    label: "成功",
    color: "green",
    value: TaskStatus.COMPLETED,
  },
  [TaskStatus.DRAFT]: {
    label: "草稿",
    color: "orange",
    value: TaskStatus.DRAFT,
  },
  [TaskStatus.PENDING]: {
    label: "就绪",
    color: "cyan",
    value: TaskStatus.PENDING
  },
};

export const SyncModeMap: Record<SyncMode, { label: string; value: SyncMode, color: string }> =
  {
    [SyncMode.ONCE]: { label: "立即同步", value: SyncMode.ONCE, color: "orange" },
    [SyncMode.SCHEDULED]: { label: "定时同步", value: SyncMode.SCHEDULED, color: "blue" },
  };

export const LogStatusMap: Record<
  LogStatus,
  { label: string; color: string; value: LogStatus }
> = {
  [LogStatus.SUCCESS]: {
    label: "成功",
    color: "green",
    value: LogStatus.SUCCESS,
  },
  [LogStatus.FAILED]: {
    label: "失败",
    color: "red",
    value: LogStatus.FAILED,
  },
  [LogStatus.RUNNING]: {
    label: "运行中",
    color: "blue",
    value: LogStatus.RUNNING,
  },
};

export const LogTriggerTypeMap: Record<
  TriggerType,
  { label: string; value: TriggerType }
> = {
  [TriggerType.MANUAL]: { label: "手动", value: TriggerType.MANUAL },
  [TriggerType.SCHEDULED]: { label: "定时", value: TriggerType.SCHEDULED },
  [TriggerType.API]: { label: "API", value: TriggerType.API },
};

export function mapCollectionTask(task: CollectionTask): any {
  return {
    ...task,
    status: StatusMap[task.status],
    syncMode: SyncModeMap[task.syncMode],
    createdAt: formatDateTime(task.createdAt),
    updatedAt: formatDateTime(task.updatedAt)
  };
}

export function mapTaskExecution(execution: TaskExecution): any {
  return {
    ...execution,
    status: StatusMap[execution.status],
    startedAt: formatDateTime(execution.startedAt),
    completedAt: formatDateTime(execution.completedAt)
  };
}
