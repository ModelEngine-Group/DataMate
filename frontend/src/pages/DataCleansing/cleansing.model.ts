import { OperatorI } from "../OperatorMarket/operator.model";

export interface CleansingTask {
  id: string;
  name: string;
  description?: string;
  srcDatasetId: string;
  srcDatasetName: string;
  destDatasetId: string;
  destDatasetName: string;
  templateId: string;
  templateName: string;
  status: {
    label: string;
    value: TaskStatus;
    color: string;
  };
  startedAt: string;
  progress: {
    finishedFileNum: number;
    process: 100,
    totalFileNum: number;
  };
  operators: OperatorI[];
  createdAt: string;
  updatedAt: string;
  finishedAt: string;
  beforeSize?: number;
  afterSize?: number;
}

export interface CleansingTemplate {
  id: string;
  name: string;
  description?: string;
  instance: OperatorI[];
  createdAt: string;
  updatedAt: string;
}

export enum RuleCategory {
  DATA_VALIDATION = "DATA_VALIDATION",
  MISSING_VALUE_HANDLING = "MISSING_VALUE_HANDLING",
  OUTLIER_DETECTION = "OUTLIER_DETECTION",
  DEDUPLICATION = "DEDUPLICATION",
  FORMAT_STANDARDIZATION = "FORMAT_STANDARDIZATION",
  TEXT_CLEANING = "TEXT_CLEANING",
  CUSTOM = "CUSTOM",
}

export enum TaskStatus {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  STOPPED = "STOPPED",
}

export interface RuleCondition {
  field: string;
  operator: string;
  value: string;
  logicOperator?: "AND" | "OR";
}

export enum TemplateType {
  TEXT = "TEXT",
  IMAGE = "IMAGE",
  VIDEO = "VIDEO",
  AUDIO = "AUDIO",
  IMAGE2TEXT = "IMAGE2TEXT",
}
