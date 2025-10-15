interface KnowledgeBase {
  id: number;
  name: string;
  description: string;
  type: "unstructured" | "structured";
  status: "processing" | "ready" | "error" | "importing" | "vectorizing";
  fileCount: number;
  chunkCount: number;
  vectorCount: number;
  size: string;
  progress: number;
  createdAt: string;
  lastUpdated: string;
  vectorDatabase: string;
  config: {
    embeddingModel: string;
    llmModel?: string;
    chunkSize: number;
    overlap: number;
    sliceMethod: "paragraph" | "length" | "delimiter" | "semantic";
    delimiter?: string;
    enableQA: boolean;
    vectorDimension: number;
    sliceOperators: string[];
  };
  files: KBFile[];
  vectorizationHistory: VectorizationRecord[];
}

interface KBFile {
  id: number;
  name: string;
  type: string;
  size: string;
  status: "processing" | "completed" | "error" | "disabled" | "vectorizing";
  chunkCount: number;
  progress: number;
  uploadedAt: string;
  source: "upload" | "dataset";
  datasetId?: string;
  chunks?: Chunk[];
  vectorizationStatus?: "pending" | "processing" | "completed" | "failed";
}

interface Chunk {
  id: number;
  content: string;
  position: number;
  tokens: number;
  embedding?: number[];
  similarity?: string;
  createdAt?: string;
  updatedAt?: string;
  vectorId?: string;
  sliceOperator?: string;
  parentChunkId?: number;
  metadata?: {
    source: string;
    page?: number;
    section?: string;
  };
}

interface VectorizationRecord {
  id: number;
  timestamp: string;
  operation: "create" | "update" | "delete" | "reprocess";
  fileId: number;
  fileName: string;
  chunksProcessed: number;
  vectorsGenerated: number;
  status: "success" | "failed" | "partial";
  duration: string;
  config: {
    embeddingModel: string;
    chunkSize: number;
    sliceMethod: string;
  };
  error?: string;
}

interface SliceOperator {
  id: string;
  name: string;
  description: string;
  type: "text" | "semantic" | "structure" | "custom";
  icon: string;
  params: Record<string, any>;
}
