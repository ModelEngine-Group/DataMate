import { get, post, put, del, download } from "@/utils/request";

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

// 自动标注任务管理
export function queryAutoAnnotationTasksUsingGet(params?: any) {
  return get("/api/annotation/auto", params);
}

export function createAutoAnnotationTaskUsingPost(data: any) {
  return post("/api/annotation/auto", data);
}

export function deleteAutoAnnotationTaskByIdUsingDelete(taskId: string) {
  return del(`/api/annotation/auto/${taskId}`);
}

export function getAutoAnnotationTaskStatusUsingGet(taskId: string) {
  return get(`/api/annotation/auto/${taskId}/status`);
}

export function downloadAutoAnnotationResultUsingGet(taskId: string) {
  return download(`/api/annotation/auto/${taskId}/download`);
}
