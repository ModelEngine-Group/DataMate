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
export function updateOperatorByIdUsingPut(operatorId: string | number, data: any) {
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

// 扩展功能接口（基于常见需求）

// 收藏/取消收藏算子
export function starOperatorUsingPost(operatorId: string | number) {
  return post(`/api/operators/${operatorId}/star`);
}

// 下载算子
export function downloadOperatorUsingGet(operatorId: string | number, filename?: string) {
  return download(`/api/operators/${operatorId}/download`, null, filename);
}

// 算子评分
export function rateOperatorUsingPost(operatorId: string | number, data: { rating: number; comment?: string }) {
  return post(`/api/operators/${operatorId}/rating`, data);
}

// 获取算子统计信息
export function getOperatorStatisticsUsingGet(params?: any) {
  return get("/api/operators/statistics", params);
}

// 获取我的算子列表
export function queryMyOperatorsUsingPost(data: any) {
  return post("/api/operators/my-operators", data);
}

// 获取收藏的算子列表
export function queryFavoriteOperatorsUsingPost(data: any) {
  return post("/api/operators/favorites", data);
}

// 算子使用统计
export function getOperatorUsageStatsUsingGet(operatorId: string | number) {
  return get(`/api/operators/${operatorId}/usage-stats`);
}

// 算子依赖检查
export function checkOperatorDependenciesUsingPost(operatorId: string | number) {
  return post(`/api/operators/${operatorId}/check-dependencies`);
}

// 算子兼容性检查
export function checkOperatorCompatibilityUsingPost(operatorId: string | number, data: any) {
  return post(`/api/operators/${operatorId}/check-compatibility`, data);
}

// 克隆算子
export function cloneOperatorUsingPost(operatorId: string | number, data: any) {
  return post(`/api/operators/${operatorId}/clone`, data);
}

// 获取算子版本列表
export function queryOperatorVersionsUsingGet(operatorId: string | number, params?: any) {
  return get(`/api/operators/${operatorId}/versions`, params);
}

// 创建算子版本
export function createOperatorVersionUsingPost(operatorId: string | number, data: any) {
  return post(`/api/operators/${operatorId}/versions`, data);
}

// 切换算子版本
export function switchOperatorVersionUsingPut(operatorId: string | number, versionId: string | number) {
  return put(`/api/operators/${operatorId}/versions/${versionId}/switch`);
}

// 删除算子版本
export function deleteOperatorVersionUsingDelete(operatorId: string | number, versionId: string | number) {
  return del(`/api/operators/${operatorId}/versions/${versionId}`);
}

// 算子测试
export function testOperatorUsingPost(operatorId: string | number, data: any) {
  return post(`/api/operators/${operatorId}/test`, data);
}

// 获取算子测试结果
export function getOperatorTestResultUsingGet(operatorId: string | number, testId: string | number) {
  return get(`/api/operators/${operatorId}/test/${testId}/result`);
}

// 算子审核相关
export function submitOperatorForReviewUsingPost(operatorId: string | number) {
  return post(`/api/operators/${operatorId}/submit-review`);
}

export function approveOperatorUsingPost(operatorId: string | number, data?: any) {
  return post(`/api/operators/${operatorId}/approve`, data);
}

export function rejectOperatorUsingPost(operatorId: string | number, data: { reason: string }) {
  return post(`/api/operators/${operatorId}/reject`, data);
}

// 获取算子评论列表
export function queryOperatorCommentsUsingGet(operatorId: string | number, params?: any) {
  return get(`/api/operators/${operatorId}/comments`, params);
}

// 添加算子评论
export function addOperatorCommentUsingPost(operatorId: string | number, data: any) {
  return post(`/api/operators/${operatorId}/comments`, data);
}

// 删除算子评论
export function deleteOperatorCommentUsingDelete(operatorId: string | number, commentId: string | number) {
  return del(`/api/operators/${operatorId}/comments/${commentId}`);
}

// 搜索算子
export function searchOperatorsUsingPost(data: any) {
  return post("/api/operators/search", data);
}

// 获取热门算子
export function queryPopularOperatorsUsingGet(params?: any) {
  return get("/api/operators/popular", params);
}

// 获取推荐算子
export function queryRecommendedOperatorsUsingGet(params?: any) {
  return get("/api/operators/recommended", params);
}

// 获取最新算子
export function queryLatestOperatorsUsingGet(params?: any) {
  return get("/api/operators/latest", params);
}

// 算子使用示例
export function getOperatorExamplesUsingGet(operatorId: string | number) {
  return get(`/api/operators/${operatorId}/examples`);
}

// 创建算子使用示例
export function createOperatorExampleUsingPost(operatorId: string | number, data: any) {
  return post(`/api/operators/${operatorId}/examples`, data);
}

// 算子文档
export function getOperatorDocumentationUsingGet(operatorId: string | number) {
  return get(`/api/operators/${operatorId}/documentation`);
}

// 更新算子文档
export function updateOperatorDocumentationUsingPut(operatorId: string | number, data: any) {
  return put(`/api/operators/${operatorId}/documentation`, data);
}

// 批量操作
export function batchDeleteOperatorsUsingPost(data: { operatorIds: string[] }) {
  return post("/api/operators/batch-delete", data);
}

export function batchUpdateOperatorsUsingPost(data: any) {
  return post("/api/operators/batch-update", data);
}

export function batchPublishOperatorsUsingPost(data: { operatorIds: string[] }) {
  return post("/api/operators/batch-publish", data);
}

export function batchUnpublishOperatorsUsingPost(data: { operatorIds: string[] }) {
  return post("/api/operators/batch-unpublish", data);
}