import { get, post, put, del } from "@/utils/request";
import type { UnifiedSearchResult } from "./knowledge-base.model";

// 获取知识库列表
export function queryKnowledgeBasesUsingPost(params: any) {
  // 将前端的 size 参数映射为后端的 page_size
  const { size, ...rest } = params;
  return post("/api/knowledge-base/list", {
    ...rest,
    page_size: size
  });
}

// 创建知识库
export function createKnowledgeBaseUsingPost(data: object) {
  return post("/api/knowledge-base/create", data);
}

// 获取知识库详情
export function queryKnowledgeBaseByIdUsingGet(baseId: string) {
  return get(`/api/knowledge-base/${baseId}`);
}

// 更新知识库
export function updateKnowledgeBaseByIdUsingPut(baseId: string, data: object) {
  return (put as unknown as (url: string, data?: object) => Promise<unknown>)(`/api/knowledge-base/${baseId}`, data);
}

// 删除知识库
export function deleteKnowledgeBaseByIdUsingDelete(baseId: string) {
  return del(`/api/knowledge-base/${baseId}`);
}

// 获取知识生成文件列表
export function queryKnowledgeBaseFilesUsingGet(baseId: string, params?: Record<string, any>) {
  if (!params) {
    return get(`/api/knowledge-base/${baseId}/files`);
  }
  // 将前端的 size 参数映射为后端的 page_size
  const { size, page, ...rest } = params;
  const queryParams = {
    page: page || 1,
    page_size: size || 10,
    ...rest
  };
  return get(`/api/knowledge-base/${baseId}/files?${new URLSearchParams(
    Object.entries(queryParams)
      .filter(([_, v]) => v !== undefined && v !== null)
      .reduce((acc, [k, v]) => ({ ...acc, [k]: String(v) }), {})
  ).toString()}`);
}

// 添加文件到知识库
export function addKnowledgeBaseFilesUsingPost(baseId: string, data: object) {
  return post(`/api/knowledge-base/${baseId}/files`, data);
}

// 删除知识生成文件
export function deleteKnowledgeBaseFileByIdUsingDelete(baseId: string, data: object | null) {
  return (del as unknown as (url: string, data?: object | null) => Promise<unknown>)(`/api/knowledge-base/${baseId}/files`, data ?? null);
}

// 检索知识库内容（统一检索接口）
export function retrieveKnowledgeBaseContent(data: {
  query: string;
  topK?: number;
  threshold?: number;
  knowledgeBaseIds: string[];
}): Promise<UnifiedSearchResult[]> {
  return post("/api/knowledge-base/v2/retrieve", data);
}

// 获取知识库文件详情（分页的切片数据）
export function queryKnowledgeBaseFileDetailUsingGet(
  knowledgeBaseId: string,
  ragFileId: string,
  params: { page?: number; size?: number; expr?: string } = { page: 1, size: 20 }
) {
  const page = params.page ?? 1;
  const size = params.size ?? 20;
  const queryParams = [`page=${page}`, `page_size=${size}`];
  if (params.expr) {
    queryParams.push(`expr=${encodeURIComponent(params.expr)}`);
  }
  return get(`/api/knowledge-base/${knowledgeBaseId}/files/${ragFileId}?${queryParams.join('&')}`);
}

export function queryKnowledgeBase(data: {
  knowledge_base_id: string;
  query: string;
}) {
  return post("/api/knowledge-base/query", data);
}

export function updateKnowledgeBaseChunk(
  knowledgeBaseId: string,
  chunkId: string,
  data: { text: string; metadata?: Record<string, any> }
) {
  return (put as unknown as (url: string, data?: object) => Promise<unknown>)(
    `/api/knowledge-base/${knowledgeBaseId}/chunks/${chunkId}`,
    data
  );
}

export function deleteKnowledgeBaseChunk(
  knowledgeBaseId: string,
  chunkId: string
) {
  return del(`/api/knowledge-base/${knowledgeBaseId}/chunks/${chunkId}`);
}
