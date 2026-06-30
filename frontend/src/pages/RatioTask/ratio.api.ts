import { get, post, put, del, download } from "@/utils/request";

// 查询配比任务列表（分页）
export function queryRatioTasksUsingGet(params?: any) {
  return get("/api/synthesis/ratio-task", params);
}

// 查询配比任务详情
export function getRatioTaskByIdUsingGet(id: string) {
  return get(`/api/synthesis/ratio-task/${id}`);
}

// 创建配比任务
export function createRatioTaskUsingPost(data: any) {
  return post("/api/synthesis/ratio-task", data);
}

// 删除配比任务（支持批量）
export function deleteRatioTasksUsingDelete(id: string) {
  const url = `/api/synthesis/ratio-task?ids=${id}`;
  return del(url);
}
