import { get, post, del } from "@/utils/request";

// 创建数据合成任务
export function createSynthesisTaskUsingPost(data: Record<string, unknown>) {
  return post("/api/synthesis/gen/task", data as unknown as Record<string, never>);
}

// 获取数据合成任务详情
export function querySynthesisTaskByIdUsingGet(taskId: string) {
  return get(`/api/synthesis/gen/task/${taskId}`);
}

// 分页查询数据合成任务列表
export function querySynthesisTasksUsingGet(params: {
  page?: number;
  page_size?: number;
  synthesis_type?: string;
  status?: string;
  name?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params.page !== undefined) searchParams.append("page", String(params.page));
  if (params.page_size !== undefined) searchParams.append("page_size", String(params.page_size));
  if (params.synthesis_type) searchParams.append("synthesis_type", params.synthesis_type);
  if (params.status) searchParams.append("status", params.status);
  if (params.name) searchParams.append("name", params.name);
  const qs = searchParams.toString();
  return get(`/api/synthesis/gen/tasks${qs ? `?${qs}` : ""}`);
}

// 删除整个数据合成任务
export function deleteSynthesisTaskByIdUsingDelete(taskId: string) {
  return del(`/api/synthesis/gen/task/${taskId}`);
}

// 分页查询某个任务下的文件任务列表
export function querySynthesisFileTasksUsingGet(taskId: string, params: { page?: number; page_size?: number }) {
  const searchParams = new URLSearchParams();
  if (params.page !== undefined) searchParams.append("page", String(params.page));
  if (params.page_size !== undefined) searchParams.append("page_size", String(params.page_size));
  const qs = searchParams.toString();
  return get(`/api/synthesis/gen/task/${taskId}/files${qs ? `?${qs}` : ""}`);
}

// 根据文件任务 ID 分页查询 chunk 记录
export function queryChunksByFileUsingGet(fileId: string, params: { page?: number; page_size?: number }) {
  const searchParams = new URLSearchParams();
  if (params.page !== undefined) searchParams.append("page", String(params.page));
  if (params.page_size !== undefined) searchParams.append("page_size", String(params.page_size));
  const qs = searchParams.toString();
  return get(`/api/synthesis/gen/file/${fileId}/chunks${qs ? `?${qs}` : ""}`);
}

// 根据 chunk ID 查询所有合成结果数据
export function querySynthesisDataByChunkUsingGet(chunkId: string) {
  return get(`/api/synthesis/gen/chunk/${chunkId}/data`);
}

// 获取不同合成类型对应的 Prompt
export function getPromptByTypeUsingGet(synthType: string) {
  const searchParams = new URLSearchParams();
  searchParams.append("synth_type", synthType);
  const qs = searchParams.toString();
  return get(`/api/synthesis/gen/prompt${qs ? `?${qs}` : ""}`);
}

// 将合成任务数据归档到已存在的数据集中
export function archiveSynthesisTaskToDatasetUsingPost(taskId: string, datasetId: string) {
  return post(`/api/synthesis/gen/task/${taskId}/export-dataset/${datasetId}`);
}

// ---------------- 数据记录级别：chunk 与 synthesis data ----------------

// 根据 chunkId 删除单个 chunk 及其下所有合成数据
export function deleteChunkWithDataUsingDelete(chunkId: string) {
  return del(`/api/synthesis/gen/chunk/${chunkId}`);
}

// 删除某个 chunk 下的所有合成数据，返回删除条数
export function deleteSynthesisDataByChunkUsingDelete(chunkId: string) {
  return del(`/api/synthesis/gen/chunk/${chunkId}/data`);
}

// 批量删除合成数据记录
export function batchDeleteSynthesisDataUsingDelete(body: { ids: string[] }) {
  return del(`/api/synthesis/gen/data/batch`, null, { body: JSON.stringify(body) });
}

// 更新单条合成数据的完整 JSON 内容
export function updateSynthesisDataUsingPatch(dataId: string, body: { data: Record<string, unknown> }) {
  return post(`/api/synthesis/gen/data/${dataId}`, body, { method: "PATCH" });
}
