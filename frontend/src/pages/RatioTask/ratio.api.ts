import { get, post, put, del, download } from "@/utils/request";

// 查询配比任务列表（分页）
export function queryRatioTasksUsingGet(params?: any) {
  return get("/api/synthesis/ratio-task", params);
}

// 创建配比任务
export function createRatioTaskUsingPost(data: any) {
  return post("/api/synthesis/ratio-task", data);
}

// 删除配比任务（支持批量）
export function deleteRatioTasksUsingDelete(ids: string[]) {
  const qs = (ids || []).map((id) => `ids=${encodeURIComponent(id)}`).join("&");
  const url = qs ? `/api/synthesis/ratio-task?${qs}` : "/api/synthesis/ratio-task";
  return del(url);
}
