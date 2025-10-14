export enum TaskStatus {
  DRAFT = "DRAFT",
  READY = "READY",
  RUNNING = "RUNNING",
  SUCCESS = "SUCCESS",
  FAILED = "FAILED",
  STOPPED = "STOPPED",
}

export enum SyncMode {
  ONCE = "ONCE",
  SCHEDULED = "SCHEDULED",
}

export interface CollectionTask {
  id: string;
  name: string;
  description: string;
  config: object; // 具体配置结构根据实际需求定义
  status: TaskStatus;
  syncMode: SyncMode;
  scheduleExpression?: string; // 仅当 syncMode 为 SCHEDULED 时存在
  lastExecutionId: string;
  createdAt: string; // ISO date string
  updatedAt: string; // ISO date string
}

export enum LogStatus {
  RUNNING = "RUNNING",
  SUCCESS = "SUCCESS",
  FAILED = "FAILED",
}

export enum TriggerType {
  MANUAL = "MANUAL",
  SCHEDULED = "SCHEDULED",
  API = "API",
}

export interface CollectionLog {
  id: string;
  taskId: string;
  taskName: string;
  status: TaskStatus; // 任务执行状态
  triggerType: TriggerType; // 触发类型，如手动触发、定时触发等
  startTime: string; // ISO date string
  endTime: string; // ISO date string
  duration: string; // 格式化的持续时间字符串
  retryCount: number;
  processId: string;
  errorMessage?: string; // 可选，错误信息
}
