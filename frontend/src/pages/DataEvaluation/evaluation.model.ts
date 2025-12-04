export enum EvaluationStatus {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  PAUSED = "PAUSED",
}

export interface EvaluationTask {
  id: string;
  name: string;
  description?: string;
  taskType: string;
  sourceType: string;
  sourceId: string;
  sourceName: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'STOPPED' | 'FAILED';
  evalProcess: number;
  evalMethod: 'AUTO' | 'MANUAL';
  createdAt: string;
  updatedAt: string;
}

interface EvaluationDimension {
    id: string
    name: string
    description: string
    category: "quality" | "accuracy" | "completeness" | "consistency" | "bias" | "custom"
    isCustom?: boolean
    isEnabled?: boolean
}

interface EvaluationSlice {
    id: string
    content: string
    sourceFile: string
    sliceIndex: number
    sliceType: string
    metadata: {
        startPosition?: number
        endPosition?: number
        pageNumber?: number
        section?: string
        processingMethod: string
    }
    scores?: { [dimensionId: string]: number }
    comment?: string
}

interface QAPair {
    id: string
    question: string
    answer: string
    sliceId: string
    score: number
    feedback?: string
}
