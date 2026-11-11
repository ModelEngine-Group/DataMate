import { get, post, put, del, download } from "@/utils/request";

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
  return download(`/api/cleaning/tasks/${taskId}/result/download`, null, `task_${taskId}_files.zip`);
}

export function queryCleaningTaskLogByIdUsingGet(taskId: string | number, retryCount: number) {
  return get(`/api/cleaning/tasks/${taskId}/log/${retryCount}`);
}

export interface CleaningTaskLogStream {
  onmessage: ((event: { data: string }) => void) | null;
  onerror: ((error: unknown) => void) | null;
  close: () => void;
}

export function streamCleaningTaskLog(taskId: string | number, retryCount: number = 0): CleaningTaskLogStream {
  const url = `/api/cleaning/tasks/${taskId}/log/stream?retry_count=${retryCount}`;
  const controller = new AbortController();
  const stream: CleaningTaskLogStream = {
    onmessage: null,
    onerror: null,
    close: () => controller.abort(),
  };

  // Fetch supports the Authorization header supplied by the request interceptor.
  void (async () => {
    try {
      const response = await get(url, null, {
        responseType: "stream",
        headers: { Accept: "text/event-stream" },
        signal: controller.signal,
      });
      if (!response.headers.get("content-type")?.includes("text/event-stream") || !response.body) {
        throw new Error("Invalid log stream response");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let data: string[] = [];
      try {
        while (!controller.signal.aborted) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let end: number;
          while (!controller.signal.aborted && (end = buffer.indexOf("\n")) !== -1) {
            const line = buffer.slice(0, end).replace(/\r$/, "");
            buffer = buffer.slice(end + 1);
            if (line === "") {
              if (data.length) stream.onmessage?.({ data: data.join("\n") });
              data = [];
            } else if (line === "data" || line.startsWith("data:")) {
              data.push(line.slice(5).replace(/^ /, ""));
            }
          }
        }
      } finally {
        await reader.cancel();
        reader.releaseLock();
      }
      if (!controller.signal.aborted) {
        throw new Error("Log stream ended");
      }
    } catch (error) {
      if (!controller.signal.aborted) stream.onerror?.(error);
    }
  })();

  return stream;
}

export async function downloadCleaningTaskLog(taskId: string | number, retryCount: number = 0): Promise<Blob> {
  const url = `/api/cleaning/tasks/${taskId}/log/${retryCount}/download`;
  return get(url, null, { responseType: "blob" });
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
