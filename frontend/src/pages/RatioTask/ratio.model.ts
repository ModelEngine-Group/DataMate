// Ratio module models aligned with scripts/db/data-ratio-init.sql

// enums
export type RatioMethod = "TAG" | "DATASET";

export enum RatioStatus {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  PAUSED = "PAUSED",
}

// interfaces

// t_st_ratio_instances
export interface RatioInstance {
  id: string;
  name: string;
  description?: string;
  targetDatasetId?: string;
  ratioMethod?: RatioMethod;
  ratioParameters?: any;
  mergeMethod?: string;
  status?: RatioStatus | string;
  totals?: number;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

// t_st_ratio_relations
export interface RatioRelation {
  id: string;
  ratioInstanceId: string;
  sourceDatasetId?: string;
  ratioValue?: string;
  counts?: number;
  filterConditions?: string;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

// API DTOs
export interface RatioConfigItem {
  datasetId: string;
  counts: string;
  filter_conditions: string;
}

export interface CreateRatioTaskRequest {
  name: string;
  description?: string;
  totals: string;
  ratio_method: RatioMethod;
  config: RatioConfigItem[];
}

export interface TargetDatasetInfo {
  id: string;
  name: string;
  datasetType: string;
  status: string;
}

export interface CreateRatioTaskResponse {
  id: string;
  name: string;
  description?: string;
  totals: number;
  ratio_method: RatioMethod;
  status: string;
  config: RatioConfigItem[];
  targetDataset: TargetDatasetInfo;
}

export interface RatioTaskItem {
  id: string
  name: string
  description?: string
  status?: string
  totals?: number
  ratio_method?: RatioMethod
  target_dataset_id?: string
  target_dataset_name?: string
  config: RatioConfigItem[]
  created_at?: string
  updated_at?: string
}
