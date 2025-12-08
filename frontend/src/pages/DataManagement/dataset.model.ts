export enum DatasetType {
  TEXT = "TEXT",
  IMAGE = "IMAGE",
  AUDIO = "AUDIO",
  VIDEO = "VIDEO",
}

export enum DatasetSubType {
  TEXT_DOCUMENT = "TEXT_DOCUMENT",
  TEXT_WEB = "TEXT_WEB",
  TEXT_DIALOG = "TEXT_DIALOG",
  IMAGE_IMAGE = "IMAGE_IMAGE",
  IMAGE_CAPTION = "IMAGE_CAPTION",
  AUDIO_AUDIO = "AUDIO_AUDIO",
  AUDIO_JSONL = "AUDIO_JSONL",
  VIDEO_VIDEO = "VIDEO_VIDEO",
  VIDEO_JSONL = "VIDEO_JSONL",
}

export enum DatasetStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  PROCESSING = "PROCESSING",
  DRAFT = "DRAFT",
}

export enum DataSource {
  UPLOAD = "UPLOAD",
  COLLECTION = "COLLECTION",
  DATABASE = "DATABASE",
  NAS = "NAS",
  OBS = "OBS",
}

export interface DatasetFile {
  id: number;
  fileName: string;
  size: string;
  uploadDate: string;
  path: string;
}

export interface Dataset {
  id: number;
  name: string;
  description: string;
  parentId?: number;
  datasetType: DatasetType;
  status: DatasetStatus;
  size?: string;
  itemCount?: number;
  fileCount?: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  targetLocation?: string;
  distribution?: Record<string, Record<string, number>>;
}

export interface TagItem {
  id: string;
  name: string;
  color: string;
  description: string;
}

export interface ScheduleConfig {
  type: "immediate" | "scheduled";
  scheduleType?: "daily" | "weekly" | "monthly" | "custom";
  time?: string;
  dayOfWeek?: string;
  dayOfMonth?: string;
  cronExpression?: string;
  maxExecutions?: number;
  executionCount?: number;
}

export interface DatasetTask {
  id: number;
  name: string;
  description: string;
  type: string;
  status: "importing" | "waiting" | "completed" | "failed";
  progress: number;
  createdAt: string;
  importConfig: any;
  scheduleConfig: ScheduleConfig;
  nextExecution?: string;
  lastExecution?: string;
  executionHistory?: { time: string; status: string }[];
}

export interface TaskItem {
  key: string;
  title: string;
  percent: number;
  reqId: number;
  isCancel?: boolean;
  controller: AbortController;
  cancelFn?: () => void;
  updateEvent?: string;
  size?: number;
  hasArchive?: boolean;
}
