export interface OperatorI {
  id: string;
  name: string;
  type: string;
  category: keyof typeof OPERATOR_CATEGORIES;
  icon: React.ReactNode;
  description: string;
  tags: string[];
  isPopular?: boolean;
  params: {
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

export enum RuleCategory {
  DATA_VALIDATION = "DATA_VALIDATION",
  MISSING_VALUE_HANDLING = "MISSING_VALUE_HANDLING",
  OUTLIER_DETECTION = "OUTLIER_DETECTION",
  DEDUPLICATION = "DEDUPLICATION",
  FORMAT_STANDARDIZATION = "FORMAT_STANDARDIZATION",
  TEXT_CLEANING = "TEXT_CLEANING",
  CUSTOM = "CUSTOM",
}

export enum JobStatus {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
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
