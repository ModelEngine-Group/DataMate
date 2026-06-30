import { get, post, put, del, download } from "@/utils/request";

// 算子列表查询
export function queryOperatorsUsingPost(data: any) {
  return post("/api/operators/list", data);
}

// 获取算子分类树
export function queryCategoryTreeUsingGet() {
  return get("/api/categories/tree");
}

// 根据ID获取算子详情
export function queryOperatorByIdUsingGet(operatorId: string | number) {
  return get(`/api/operators/${operatorId}`);
}

// 创建算子
export function createOperatorUsingPost(data: any) {
  return post("/api/operators/create", data);
}

// 更新算子
export function updateOperatorByIdUsingPut(
  operatorId: string | number,
  data: any
) {
  return put(`/api/operators/${operatorId}`, data);
}

// 删除算子
export function deleteOperatorByIdUsingDelete(operatorId: string | number) {
  return del(`/api/operators/${operatorId}`);
}

// 上传算子
export function uploadOperatorUsingPost(data: any) {
  return post("/api/operators/upload", data);
}

export function preUploadOperatorUsingPost(_, data: any) {
  return post("/api/operators/upload/pre-upload", data);
}

export function uploadOperatorChunkUsingPost(_, data: FormData, config?: any) {
  return post("/api/operators/upload/chunk", data, {
    showLoading: false,
    ...config,
  });
}

export function downloadExampleOperatorUsingGet(fileName: string) {
  return download("/api/operators/examples/download", null, fileName);
}

// 发布算子
export function publishOperatorUsingPost(operatorId: string | number) {
  return post(`/api/operators/${operatorId}/publish`);
}

// 下架算子
export function unpublishOperatorUsingPost(operatorId: string | number) {
  return post(`/api/operators/${operatorId}/unpublish`);
}

// 算子标签管理
export function queryLabelsUsingGet(params?: any) {
  return get("/api/labels", params);
}

// 创建算子标签
export function createLabelUsingPost(data: any) {
  return post("/api/operators/labels", data);
}

// 更新算子标签
export function updateLabelByIdUsingPut(labelId: string | number, data: any) {
  return put(`/api/labels/${labelId}`, data);
}

// 删除算子标签
export function deleteLabelsUsingDelete(labelIds: string[]) {
  return del("/api/labels", labelIds);
}

// 创建算子分类
export function createCategoryUsingPost(data: any) {
  return post("/api/category", data);
}

// 删除算子分类
export function deleteCategoryUsingDelete(data: { id: string | number }) {
  return del("/api/category", data);
}

