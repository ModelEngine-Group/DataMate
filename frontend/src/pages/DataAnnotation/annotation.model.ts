import type { DatasetType } from "@/pages/DataManagement/dataset.model";

export enum AnnotationTaskStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  PROCESSING = "processing",
  COMPLETED = "completed",
  SKIPPED = "skipped",
}

export interface AnnotationTask {
  id: string;
  name: string;
  labelingProjId: string;
  datasetId: string;

  annotationCount: number;

  description?: string;
  assignedTo?: string;
  progress: number;
  statistics: {
    accuracy: number;
    averageTime: number;
    reviewCount: number;
  };
  status: AnnotationTaskStatus;
  totalDataCount: number;
  type: DatasetType;

  createdAt: string;
  updatedAt: string;
}

// 标注模板相关类型
export interface LabelDefinition {
  fromName: string;
  toName: string;
  type: string;
  options?: string[];
  labels?: string[];
  required?: boolean;
  description?: string;
}

export interface ObjectDefinition {
  name: string;
  type: string;
  value: string;
}

export interface TemplateConfiguration {
  labels: LabelDefinition[];
  objects: ObjectDefinition[];
  metadata?: Record<string, any>;
}

export interface AnnotationTemplate {
  id: string;
  name: string;
  description?: string;
  dataType: string;
  labelingType: string;
  configuration: TemplateConfiguration;
  labelConfig?: string;
  style: string;
  category: string;
  builtIn: boolean;
  version: string;
  createdAt: string;
  updatedAt?: string;
}

export interface AnnotationTemplateListResponse {
  content: AnnotationTemplate[];
  total: number;
  page: number;
  size: number;
  totalPages: number;
}

export enum DataType {
  TEXT = "text",
  IMAGE = "image",
  AUDIO = "audio",
  VIDEO = "video",
}

export enum Classification {
  COMPUTER_VERSION = "computer-vision",
  NLP = "nlp",
  AUDIO = "audio",
  QUALITY_CONTROL = "quality-control",
  CUSTOM = "custom"
}

export enum AnnotationType {
  CLASSIFICATION = "classification",
  OBJECT_DETECTION = "object-detection",
  SEGMENTATION = "segmentation",
  NER = "ner"
}

export enum TemplateType {
  SYSTEM = "true",
  CUSTOM = "false"
}

// 自动标注任务相关类型
export enum AutoAnnotationStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export interface AutoAnnotationConfig {
  modelSize: "n" | "s" | "m" | "l" | "x";
  confThreshold: number;
  targetClasses: number[];
}

export interface AutoAnnotationTask {
  id: string;
  name: string;
  datasetId: string;
  datasetName?: string;
  config: AutoAnnotationConfig;
  status: AutoAnnotationStatus;
  progress: number;
  totalImages: number;
  processedImages: number;
  detectedObjects: number;
  outputPath?: string;
  errorMessage?: string;
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
}

export interface AutoAnnotationResult {
  taskId: string;
  outputDatasetPath: string;
  annotationFiles: string[];
  statistics: {
    totalImages: number;
    successfulImages: number;
    failedImages: number;
    totalDetections: number;
    averageDetectionsPerImage: number;
  };
}
