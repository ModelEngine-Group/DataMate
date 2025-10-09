export interface Operator {
  id: number;
  name: string;
  version: string;
  description: string;
  author: string;
  category: string;
  modality: string[];
  type: "preprocessing" | "training" | "inference" | "postprocessing";
  tags: string[];
  createdAt: string;
  lastModified: string;
  status: "active" | "deprecated" | "beta";
  isFavorited?: boolean;
  downloads: number;
  usage: number;
  framework: string;
  language: string;
  size: string;
  dependencies: string[];
  inputFormat: string[];
  outputFormat: string[];
  performance: {
    accuracy?: number;
    speed: string;
    memory: string;
  };
}