import { get, post, put, del } from "@/utils/request";

// 数据源任务相关接口
export function queryTasksUsingGet(params?: any) {
  return get("/api/data-collection/tasks", params);
}

export function createTaskUsingPost(data: any) {
  return post("/api/data-collection/tasks", data);
}

export function queryTaskByIdUsingGet(id: string | number) {
  return get(`/api/data-collection/tasks/${id}`);
}

export function updateTaskByIdUsingPut(
  id: string | number,
  data: any
) {
  return put(`/api/data-collection/tasks/${id}`, data);
}

export function deleteTaskByIdUsingDelete(id: string | number) {
  return del(`/api/data-collection/tasks/${id}`);
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
  return post("/api/data-collection/executions", params);
}

export function queryExecutionLogByIdUsingGet(id: string | number) {
  return get(`/api/data-collection/executions/${id}`);
}

// 监控统计相关接口
export function queryCollectionStatisticsUsingGet(params?: any) {
  return get("/api/data-collection/monitor/statistics", params);
}
