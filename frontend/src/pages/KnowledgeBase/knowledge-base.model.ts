export enum KBFileStatus {
  UNPROCESSED = "UNPROCESSED",
  PROCESSING = "PROCESSING",
  PROCESSED = "PROCESSED",
  PROCESS_FAILED = "PROCESS_FAILED",
}

export enum KBType {
  DOCUMENT = "DOCUMENT",
  GRAPH = "GRAPH",
}

export interface KnowledgeBaseItem {
  id: string;
  name: string;
  description: string;
  type: KBType;
  createdAt: string;
  updatedAt: string;
  embeddingModel: string;
  chatModel: string;
  fileCount: number;
  chunkCount: number;
  embedding: never;
  chat: never;
  customEntities?: string[];
}

export interface KBFile {
  id: string;
  fileName: string;
  name?: string;
  createdAt: string;
  updatedAt: string;
  status: KBFileStatus;
  chunkCount: number;
  metadata: Record<string, any>;
  knowledgeBaseId: string;
  fileId: string;
  updatedBy: string;
  createdBy: string;
}

export interface KnowledgeGraphNodeProperties {
  entity_id: string;
  entity_type: string;
  description: string;
  source_id: string;
  file_path: string;
  created_at: number;
  truncate: string;
  [key: string]: unknown;
}

export interface KnowledgeGraphNode {
  id: string;
  labels: string[];
  properties: KnowledgeGraphNodeProperties;
}

export interface KnowledgeGraphEdgeProperties {
  weight: number;
  description: string;
  keywords: string;
  source_id: string;
  file_path: string;
  created_at: number;
  truncate: string;
  [key: string]: unknown;
}

export interface KnowledgeGraphEdge {
  id: string;
  type: string;
  source: string;
  target: string;
  properties: KnowledgeGraphEdgeProperties;
}

export interface KnowledgeGraphResponse {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  is_truncated: boolean;
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
