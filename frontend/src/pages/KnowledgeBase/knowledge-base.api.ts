import { get, post, put, del } from "@/utils/request";

// 获取知识库列表
export function queryKnowledgeBasesUsingPost(params: any) {
  return post("/api/knowledge-base/list", params);
}

// 创建知识库
export function createKnowledgeBaseUsingPost(data: any) {
  return post("/api/knowledge-base/create", data);
}

// 获取知识库详情
export function queryKnowledgeBaseByIdUsingGet(baseId: string) {
  return get(`/api/knowledge-base/${baseId}`);
}

// 更新知识库
export function updateKnowledgeBaseByIdUsingPut(baseId: string, data: any) {
  return put(`/api/knowledge-base/${baseId}`, data);
}

// 删除知识库
export function deleteKnowledgeBaseByIdUsingDelete(baseId: string) {
  return del(`/api/knowledge-base/${baseId}`);
}

// 获取知识生成文件列表
export function queryKnowledgeBaseFilesUsingGet(baseId: string, data) {
  return get(`/api/knowledge-base/${baseId}/files`, data);
}

// 添加文件到知识库
export function addKnowledgeBaseFilesUsingPost(baseId: string, data: any) {
  return post(`/api/knowledge-base/${baseId}/files`, data);
}

// 获取知识生成文件详情
export function queryKnowledgeBaseFilesByIdUsingGet(
  baseId: string,
  fileId: string
) {
  return get(`/api/knowledge-base/${baseId}/files/${fileId}`);
}

// 删除知识生成文件
export function deleteKnowledgeBaseFileByIdUsingDelete(baseId: string, data: any) {
  return del(`/api/knowledge-base/${baseId}/files`, data);
}
