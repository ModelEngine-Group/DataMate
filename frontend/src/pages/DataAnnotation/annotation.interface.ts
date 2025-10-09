import type { DatasetType } from "@/pages/DataManagement/dataset.model";

export enum AnnotationTaskStatus {
  ACTIVE = "active",
  PROCESSING = "processing",
  INACTIVE = "inactive",
}

export interface AnnotationTask {
  id: string;
  name: string;
  annotationCount: number;
  createdAt: string;
  datasetId: string;
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
  updatedAt: string;
}
