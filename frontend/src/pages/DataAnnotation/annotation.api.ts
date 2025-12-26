import { get, post, put, del } from "@/utils/request";

// 标注任务管理相关接口
export function queryAnnotationTasksUsingGet(params?: any) {
  return get("/api/annotation/project", params);
}

export function createAnnotationTaskUsingPost(data: any) {
  return post("/api/annotation/project", data);
}

export function syncAnnotationTaskUsingPost(data: any) {
  return post(`/api/annotation/task/sync`, data);
}

export function deleteAnnotationTaskByIdUsingDelete(mappingId: string) {
  // Backend expects mapping UUID as path parameter
  return del(`/api/annotation/project/${mappingId}`);
}

export function loginAnnotationUsingGet(mappingId: string) {
  return get("/api/annotation/project/${mappingId}/login");
}

// 标签配置管理
export function getTagConfigUsingGet() {
  return get("/api/annotation/tags/config");
}

// 标注模板管理
export function queryAnnotationTemplatesUsingGet(params?: any) {
  return get("/api/annotation/template", params);
}

export function createAnnotationTemplateUsingPost(data: any) {
  return post("/api/annotation/template", data);
}

export function updateAnnotationTemplateByIdUsingPut(
  templateId: string | number,
  data: any
) {
  return put(`/api/annotation/template/${templateId}`, data);
}

export function deleteAnnotationTemplateByIdUsingDelete(
  templateId: string | number
) {
  return del(`/api/annotation/template/${templateId}`);
}
