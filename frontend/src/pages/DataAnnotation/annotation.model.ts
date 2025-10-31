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
