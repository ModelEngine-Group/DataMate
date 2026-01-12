import { get, post, put, del } from "@/utils/request";

// 获取知识库列表
export function queryKnowledgeBasesUsingPost(params: object) {
  return post("/api/knowledge-base/list", params);
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
export function queryKnowledgeBaseFilesUsingGet(baseId: string, params?: Record<string, string>) {
  return get(`/api/knowledge-base/${baseId}/files${params ? `?${new URLSearchParams(params).toString()}` : ""}`);
}

// 添加文件到知识库
export function addKnowledgeBaseFilesUsingPost(baseId: string, data: object) {
  return post(`/api/knowledge-base/${baseId}/files`, data);
}

// 删除知识生成文件
export function deleteKnowledgeBaseFileByIdUsingDelete(baseId: string, data: object | null) {
  return (del as unknown as (url: string, data?: object | null) => Promise<unknown>)(`/api/knowledge-base/${baseId}/files`, data ?? null);
}

// 检索知识库内容
export function retrieveKnowledgeBaseContent(data: {
  query: string;
  topK?: number;
  threshold?: number;
  knowledgeBaseIds: string[];
}) {
  return post("/api/knowledge-base/retrieve", data);
}

// 新增：获取知识库文件详情（分页的切片数据）
export function queryKnowledgeBaseFileDetailUsingGet(
  knowledgeBaseId: string,
  ragFileId: string,
  params: { page?: number; size?: number } = { page: 1, size: 20 }
) {
  const page = params.page ?? 1;
  const size = params.size ?? 20;
  return get(`/api/knowledge-base/${knowledgeBaseId}/files/${ragFileId}?page=${page}&size=${size}`);
}
