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






