import { LogStatus, SyncMode, TaskStatus, TriggerType } from "./collection.model";

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
  [TaskStatus.SUCCESS]: {
    label: "成功",
    color: "green",
    value: TaskStatus.SUCCESS,
  },
  [TaskStatus.DRAFT]: {
    label: "草稿",
    color: "orange",
    value: TaskStatus.DRAFT,
  },
  [TaskStatus.READY]: { label: "就绪", color: "cyan", value: TaskStatus.READY },
};

export const SyncModeMap: Record<SyncMode, { label: string; value: SyncMode }> =
  {
    [SyncMode.ONCE]: { label: "立即同步", value: SyncMode.ONCE },
    [SyncMode.SCHEDULED]: { label: "定时同步", value: SyncMode.SCHEDULED },
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
