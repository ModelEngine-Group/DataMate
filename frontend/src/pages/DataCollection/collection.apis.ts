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

export function queryTaskDetailsByIdUsingGet(id: string | number) {
  return get(`/api/data-collection/tasks/${id}`);
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

export function queryExecutionLogByIdUsingGet(id: string | number) {
  return get(`/api/data-collection/executions/${id}`);
}

export function queryExecutionLogContentByIdUsingGet(id: string | number) {
  return get(`/api/data-collection/executions/${id}/log`);
}

export async function queryExecutionLogFileByIdUsingGet(id: string | number) {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  const resp = await fetch(`/api/data-collection/executions/${id}/log`, {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: "include",
  });

  if (!resp.ok) {
    let detail = "";
    try {
      detail = await resp.text();
    } catch {
      detail = resp.statusText;
    }
    const err: any = new Error(detail || `HTTP error ${resp.status}`);
    err.status = resp.status;
    err.data = detail;
    throw err;
  }

  const contentDisposition = resp.headers.get("content-disposition") || "";
  const filenameMatch = contentDisposition.match(/filename\*?=(?:UTF-8''|\")?([^;\"\n]+)/i);
  const filename = filenameMatch?.[1] ? decodeURIComponent(filenameMatch[1].replace(/\"/g, "").trim()) : `execution_${id}.log`;
  const blob = await resp.blob();
  return { blob, filename };
}

// 监控统计相关接口
export function queryCollectionStatisticsUsingGet(params?: any) {
  return get("/api/data-collection/monitor/statistics", params);
}
