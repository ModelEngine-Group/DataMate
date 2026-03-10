import { get, post, put, del } from "@/utils/request";

// 清洗任务相关接口
export function queryCleaningTasksUsingGet(params?: any) {
  return get("/api/cleaning/tasks", params);
}

export function createCleaningTaskUsingPost(data: any) {
  return post("/api/cleaning/tasks", data);
}

export function queryCleaningTaskByIdUsingGet(taskId: string | number) {
  return get(`/api/cleaning/tasks/${taskId}`);
}

export function queryCleaningTaskResultByIdUsingGet(taskId: string | number) {
  return get(`/api/cleaning/tasks/${taskId}/result`);
}

export function downloadCleaningTaskFiles(taskId: string | number) {
  const url = `/api/cleaning/tasks/${taskId}/result/download`;
  const link = document.createElement('a');
  link.href = url;
  link.download = `task_${taskId}_files.zip`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function queryCleaningTaskLogByIdUsingGet(taskId: string | number, retryCount: number) {
  return get(`/api/cleaning/tasks/${taskId}/log/${retryCount}`);
}

export function streamCleaningTaskLog(taskId: string | number, retryCount: number = 0): EventSource {
  const url = `/api/cleaning/tasks/${taskId}/log/stream?retry_count=${retryCount}`;
  return new EventSource(url);
}

export async function downloadCleaningTaskLog(taskId: string | number, retryCount: number = 0): Promise<Blob> {
  const url = `/api/cleaning/tasks/${taskId}/log/${retryCount}/download`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to download log file');
  }
  return response.blob();
}

export function updateCleaningTaskByIdUsingPut(taskId: string | number, data: any) {
  return put(`/api/cleaning/tasks/${taskId}`, data);
}

export function deleteCleaningTaskByIdUsingDelete(taskId: string | number) {
  return del(`/api/cleaning/tasks/${taskId}`);
}

export function executeCleaningTaskUsingPost(taskId: string | number, data?: any) {
  return post(`/api/cleaning/tasks/${taskId}/execute`, data);
}

export function stopCleaningTaskUsingPost(taskId: string | number, data?: any) {
  return post(`/api/cleaning/tasks/${taskId}/stop`, data);
}

// 清洗模板相关接口
export function queryCleaningTemplatesUsingGet(params?: any) {
  return get("/api/cleaning/templates", params);
}

export function createCleaningTemplateUsingPost(data: any) {
  return post("/api/cleaning/templates", data);
}

export function queryCleaningTemplateByIdUsingGet(templateId: string | number) {
  return get(`/api/cleaning/templates/${templateId}`);
}

export function updateCleaningTemplateByIdUsingPut(templateId: string | number, data: any) {
  return put(`/api/cleaning/templates/${templateId}`, data);
}

export function deleteCleaningTemplateByIdUsingDelete(templateId: string | number) {
  return del(`/api/cleaning/templates/${templateId}`);
}
