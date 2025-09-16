import { get, post, put, del, download } from "@/utils/request";

// 数据集统计接口
export function getDatasetStatisticsUsingGet() {
  return get("/api/datasets/statistics");
}

// 查询数据集列表
export function queryDatasetsUsingGet(params?: any) {
  return post("/api/datasets", params);
}

// 创建数据集
export function createDatasetUsingPost(data: any) {
  return post("/api/datasets/create", data);
}

// 根据ID获取数据集详情
export function queryDatasetByIdUsingGet(id: string | number) {
  return get(`/api/datasets/${id}`);
}

// 更新数据集
export function updateDatasetByIdUsingPut(id: string | number, data: any) {
  return put(`/api/datasets/${id}`, data);
}

// 删除数据集
export function deleteDatasetByIdUsingDelete(id: string | number) {
  return del(`/api/datasets/${id}`);
}

// 下载数据集
export function downloadDatasetUsingGet(
  id: string | number,
  filename?: string
) {
  return download(`/api/datasets/${id}/download`, null, filename);
}

// 验证数据集
export function validateDatasetUsingPost(id: string | number, data?: any) {
  return post(`/api/datasets/${id}/validate`, data);
}

// 获取数据集文件列表
export function queryDatasetFilesUsingGet(id: string | number, params?: any) {
  return get(`/api/datasets/${id}/files`, params);
}

// 上传数据集文件
export function uploadDatasetFileUsingPost(id: string | number, data: any) {
  return post(`/api/datasets/${id}/files`, data);
}

export function downloadFile(
  id: string | number,
  fileId: string | number,
  filename?: string
) {
  return download(
    `/api/datasets/${id}/files/${fileId}/download`,
    null,
    filename
  );
}

// 删除数据集文件
export function deleteDatasetFileUsingDelete(
  datasetId: string | number,
  fileId: string | number
) {
  return del(`/api/datasets/${datasetId}/files/${fileId}`);
}

// 文件预览
export function previewDatasetUsingGet(id: string | number, params?: any) {
  return get(`/api/datasets/${id}/preview`, params);
}

// 获取数据集标签
export function queryDatasetTagsUsingGet(params?: any) {
  return get("/api/dataset-tags", params);
}

// 创建数据集标签
export function createDatasetTagUsingPost(data: any) {
  return post("/api/dataset-tags", data);
}

// 更新数据集标签
export function updateDatasetTagByIdUsingPut(id: string | number, data: any) {
  return put(`/api/dataset-tags/${id}`, data);
}

// 删除数据集标签
export function deleteDatasetTagByIdUsingDelete(id: string | number) {
  return del(`/api/datasets-tags/${id}`);
}

// 数据集质量检查
export function checkDatasetQualityUsingPost(id: string | number, data?: any) {
  return post(`/api/datasets/${id}/quality-check`, data);
}

// 获取数据集质量报告
export function getDatasetQualityReportUsingGet(id: string | number) {
  return get(`/api/datasets/${id}/quality-report`);
}

// 数据集分析
export function analyzeDatasetUsingPost(id: string | number, data?: any) {
  return post(`/api/datasets/${id}/analyze`, data);
}

// 获取数据集分析结果
export function getDatasetAnalysisUsingGet(id: string | number) {
  return get(`/api/datasets/${id}/analysis`);
}

// 导出数据集
export function exportDatasetUsingPost(id: string | number, data: any) {
  return post(`/api/datasets/${id}/export`, data);
}

// 复制数据集
export function copyDatasetUsingPost(id: string | number, data: any) {
  return post(`/api/datasets/${id}/copy`, data);
}

// 获取数据集版本列表
export function queryDatasetVersionsUsingGet(
  id: string | number,
  params?: any
) {
  return get(`/api/datasets/${id}/versions`, params);
}

// 创建数据集版本
export function createDatasetVersionUsingPost(id: string | number, data: any) {
  return post(`/api/datasets/${id}/versions`, data);
}

// 切换数据集版本
export function switchDatasetVersionUsingPut(
  id: string | number,
  versionId: string | number
) {
  return put(`/api/datasets/${id}/versions/${versionId}/switch`);
}

// 删除数据集版本
export function deleteDatasetVersionUsingDelete(
  id: string | number,
  versionId: string | number
) {
  return del(`/api/datasets/${id}/versions/${versionId}`);
}
