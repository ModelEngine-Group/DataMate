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
  return get(`/api/synthesis/gen/tasks`, params);
}

// 删除整个数据合成任务
export function deleteSynthesisTaskByIdUsingDelete(taskId: string) {
  return del(`/api/synthesis/gen/task/${taskId}`);
}

// 分页查询某个任务下的文件任务列表
export function querySynthesisFileTasksUsingGet(taskId: string, params: { page?: number; page_size?: number }) {
  return get(`/api/synthesis/gen/task/${taskId}/files`, params);
}

// 根据文件任务 ID 分页查询 chunk 记录
export function queryChunksByFileUsingGet(fileId: string, params: { page?: number; page_size?: number }) {
  return get(`/api/synthesis/gen/file/${fileId}/chunks`, params);
}

// 根据 chunk ID 查询所有合成结果数据
export function querySynthesisDataByChunkUsingGet(chunkId: string) {
  return get(`/api/synthesis/gen/chunk/${chunkId}/data`);
}

// 获取不同合成类型对应的 Prompt
export function getPromptByTypeUsingGet(synthType: string) {
  return get(`/api/synthesis/gen/prompt`, { synth_type: synthType });
}

// 将合成任务数据归档到已存在的数据集中
export function archiveSynthesisTaskToDatasetUsingPost(taskId: string, datasetId: string) {
  return post(`/api/synthesis/gen/task/${taskId}/export-dataset/${datasetId}`);
}
