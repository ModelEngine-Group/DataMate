export interface OperatorI {
  id: string;
  name: string;
  type: string;
  category: keyof typeof OPERATOR_CATEGORIES;
  icon: React.ReactNode;
  description: string;
  tags: string[];
  isStar?: boolean;
  originalId?: string; // 用于标识原始算子ID，便于去重
  settings: {
    [key: string]: {
      type: "input" | "select" | "radio" | "checkbox" | "range";
      label: string;
      value: any;
      options?: string[] | { label: string; value: any }[];
      min?: number;
      max?: number;
      step?: number;
    };
  };
}

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
  progress: number;
  operators: OperatorI[];
  createdAt: string;
  updatedAt: string;
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
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
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
