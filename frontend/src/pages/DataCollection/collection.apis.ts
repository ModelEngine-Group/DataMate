import {get, post, put, del, download} from "@/utils/request";

// 数据源任务相关接口
export function queryTasksUsingGet(params?: any) {
  return get("/api/data-collection/tasks", params);
}

export function createTaskUsingPost(data: any) {
  return post("/api/data-collection/tasks", data);
}

export function queryDataXTemplatesUsingGet(params?: any) {
  return get("/api/data-collection/templates", params);
}
export function deleteTaskByIdUsingDelete(id: string | number) {
  return del("/api/data-collection/tasks", { ids: [id] });
}

export function executeTaskByIdUsingPost(
  id: string | number,
  data?: any
) {
  return post(`/api/data-collection/tasks/${id}/execute`, data);
}

export function stopTaskByIdUsingPost(
  id: string | number,
  data?: any
) {
  return post(`/api/data-collection/tasks/${id}/stop`, data);
}

// 执行日志相关接口
export function queryExecutionLogUsingPost(params?: any) {
  return get("/api/data-collection/executions", params);
}

export async function queryExecutionLogFileByIdUsingGet(id: string | number) {
  return await download(`/api/data-collection/executions/${id}/log`, null, undefined, "preview");
}
