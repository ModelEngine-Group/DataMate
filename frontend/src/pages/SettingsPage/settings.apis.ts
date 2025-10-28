import { get, post, put, del } from "@/utils/request";

// 模型相关接口
export function queryModelProvidersUsingGet(params?: any) {
  return get("/api/models/providers", params);
}

export function queryModelListUsingGet(data: any) {
  return get("/api/models/list", data);
}

export function queryModelDetailByIdUsingGet(id: string | number) {
  return get(`/api/models/${id}`);
}

export function updateModelByIdUsingPut(
  id: string | number,
  data: any
) {
  return put(`/api/models/${id}`, data);
}

export function createModelUsingPost(data: any) {
  return post("/api/models/create", data);
}

export function deleteModelByIdUsingDelete(id: string | number) {
  return del(`/api/models/${id}`);
}

