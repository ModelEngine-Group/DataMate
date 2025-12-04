import { get, post, del } from "@/utils/request";

// 创建数据合成任务
export function createSynthesisTaskUsingPost(data: unknown) {
  return post("/api/synthesis/gen/task", data);
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
  return get(`/api/synthesis/gen/tasks`, params as any);
}

// 删除整个数据合成任务
export function deleteSynthesisTaskByIdUsingDelete(taskId: string) {
  return del(`/api/synthesis/gen/task/${taskId}`);
}

// 分页查询某个任务下的文件任务列表
export function querySynthesisFileTasksUsingGet(taskId: string, params: { page?: number; page_size?: number }) {
  return get(`/api/synthesis/gen/task/${taskId}/files`, params as any);
}

// 获取不同合成类型对应的 Prompt
export function getPromptByTypeUsingGet(synthType: string) {
  return get(`/api/synthesis/gen/prompt`, { synth_type: synthType } as any);
}
