export interface SynthesisTask {
  id: number;
  name: string;
  type: "qa" | "distillation" | "text" | "multimodal";
  status: "pending" | "running" | "completed" | "failed" | "paused";
  progress: number;
  sourceDataset: string;
  targetCount: number;
  generatedCount: number;
  createdAt: string;
  template: string;
  estimatedTime?: string;
  quality?: number;
  errorMessage?: string;
}

export interface Template {
  id: number;
  name: string;
  type: "preset" | "custom";
  category: string;
  prompt: string;
  variables: string[];
  description: string;
  usageCount: number;
  lastUsed?: string;
  quality?: number;
}

interface File {
  id: string;
  name: string;
  size: string;
  type: string;
}
