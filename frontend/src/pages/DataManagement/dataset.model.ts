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
  type: DatasetType;
  status: DatasetStatus;
  size?: string;
  itemCount?: number;
  createdBy: string;
  createdAt: string;
  updatedBy: string;
  updatedAt: string;
  lastModified: string;
  tags: string[];
  quality: number;
  isFavorited?: boolean;
  files?: DatasetFile[];
  annotations?: {
    total: number;
    completed: number;
    accuracy: number;
  };
  lineage?: {
    source: string;
    processing: string[];
    training?: {
      model: string;
      accuracy: number;
      f1Score: number;
    };
  };
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
