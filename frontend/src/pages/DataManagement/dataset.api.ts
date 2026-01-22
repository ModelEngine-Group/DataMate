import { get, post, put, del, download } from "@/utils/request";

// 数据集统计接口
export function getDatasetStatisticsUsingGet() {
  return get("/api/data-management/datasets/statistics");
}

export function queryDatasetStatisticsByIdUsingGet(id: string | number) {
  return get(`/api/data-management/datasets/${id}/statistics`);
}

// 查询数据集列表
export function queryDatasetsUsingGet(params?: any) {
  return get("/api/data-management/datasets", params);
}

// 创建数据集
export function createDatasetUsingPost(data: any) {
  return post("/api/data-management/datasets", data);
}

// 根据ID获取数据集详情
export function queryDatasetByIdUsingGet(id: string | number) {
  return get(`/api/data-management/datasets/${id}`);
}

// 更新数据集
export function updateDatasetByIdUsingPut(id: string | number, data: any) {
  return put(`/api/data-management/datasets/${id}`, data);
}

// 删除数据集
export function deleteDatasetByIdUsingDelete(id: string | number) {
  return del(`/api/data-management/datasets/${id}`);
}

// 下载数据集
export function downloadDatasetUsingGet(id: string | number) {
  return download(`/api/data-management/datasets/${id}/files/download`);
}

// 验证数据集
export function validateDatasetUsingPost(id: string | number, data?: any) {
  return post(`/api/data-management/datasets/${id}/validate`, data);
}

// 获取数据集文件列表
export function queryDatasetFilesUsingGet(id: string | number, params?: any) {
  return get(`/api/data-management/datasets/${id}/files`, params);
}

// 根据ID获取单个数据集文件详情
export function getDatasetFileByIdUsingGet(
  datasetId: string | number,
  fileId: string | number
) {
  return get(
    `/api/data-management/datasets/${datasetId}/files/${fileId}`
  );
}

// 上传数据集文件
export function uploadDatasetFileUsingPost(id: string | number, data: any) {
  return post(`/api/data-management/datasets/${id}/files`, data);
}

// 新建数据集文件夹
export function createDatasetDirectoryUsingPost(
  id: string | number,
  data: { parentPrefix?: string; directoryName: string }
) {
  return post(`/api/data-management/datasets/${id}/files/directories`, data);
}

// 下载文件夹（打包为zip）
export function downloadDirectoryUsingGet(
  id: string | number,
  directoryPath: string
) {
  const dirName = directoryPath.split('/').filter(Boolean).pop() || 'folder';
  return download(
    `/api/data-management/datasets/${id}/files/directories/download?prefix=${encodeURIComponent(directoryPath)}`,
    null,
    `${dirName}.zip`
  );
}

// 删除文件夹（递归删除）
export function deleteDirectoryUsingDelete(
  id: string | number,
  directoryPath: string
) {
  return del(`/api/data-management/datasets/${id}/files/directories?prefix=${encodeURIComponent(directoryPath)}`);
}

// 重命名文件夹
export function renameDirectoryUsingPut(
  id: string | number,
  data: { prefix: string; newName: string }
) {
  return put(`/api/data-management/datasets/${id}/files/directories/rename`, data);
}

export function downloadFileByIdUsingGet(
  id: string | number,
  fileId: string | number,
  fileName: string,
  action: string = "download"
) {
  return download(
    `/api/data-management/datasets/${id}/files/${fileId}/download`,
    null,
    fileName,
    action
  );
}

// 删除数据集文件
export function deleteDatasetFileUsingDelete(
  datasetId: string | number,
  fileId: string | number
) {
  return del(`/api/data-management/datasets/${datasetId}/files/${fileId}`);
}

// 重命名数据集文件（仅修改主名称，后缀保持不变）
export function renameDatasetFileUsingPut(
  datasetId: string | number,
  fileId: string | number,
  data: { newName: string }
) {
  return put(
    `/api/data-management/datasets/${datasetId}/files/${fileId}/rename`,
    data
  );
}

// 文件预览
export function previewDatasetUsingGet(id: string | number, params?: any) {
  return get(`/api/data-management/datasets/${id}/preview`, params);
}

// 获取数据集标签
export function queryDatasetTagsUsingGet(params?: any) {
  return get("/api/data-management/tags", params);
}

// 创建数据集标签
export function createDatasetTagUsingPost(data: any) {
  return post("/api/data-management/tags", data);
}

// 更新数据集标签
export function updateDatasetTagUsingPut(data: any) {
  return put(`/api/data-management/tags`, data);
}

// 删除数据集标签
export function deleteDatasetTagUsingDelete(data: any) {
  return del(`/api/data-management/tags`, data);
}

// 数据集质量检查
export function checkDatasetQualityUsingPost(id: string | number, data?: any) {
  return post(`/api/data-management/datasets/${id}/quality-check`, data);
}

// 获取数据集质量报告
export function getDatasetQualityReportUsingGet(id: string | number) {
  return get(`/api/data-management/datasets/${id}/quality-report`);
}

// 数据集分析
export function analyzeDatasetUsingPost(id: string | number, data?: any) {
  return post(`/api/data-management/datasets/${id}/analyze`, data);
}

// 获取数据集分析结果
export function getDatasetAnalysisUsingGet(id: string | number) {
  return get(`/api/data-management/datasets/${id}/analysis`);
}

// 导出数据集
export function exportDatasetUsingPost(id: string | number, data: any) {
  return post(`/api/data-management/datasets/${id}/export`, data);
}

// 复制数据集
export function copyDatasetUsingPost(id: string | number, data: any) {
  return post(`/api/data-management/datasets/${id}/copy`, data);
}

// 获取数据集版本列表
export function queryDatasetVersionsUsingGet(
  id: string | number,
  params?: any
) {
  return get(`/api/data-management/datasets/${id}/versions`, params);
}

// 创建数据集版本
export function createDatasetVersionUsingPost(id: string | number, data: any) {
  return post(`/api/data-management/datasets/${id}/versions`, data);
}

// 切换数据集版本
export function switchDatasetVersionUsingPut(
  id: string | number,
  versionId: string | number
) {
  return put(
    `/api/data-management/datasets/${id}/versions/${versionId}/switch`
  );
}

// 删除数据集版本
export function deleteDatasetVersionUsingDelete(
  id: string | number,
  versionId: string | number
) {
  return del(`/api/data-management/datasets/${id}/versions/${versionId}`);
}

/**
 * 文件上传相关接口
 */

export function preUploadUsingPost(id: string | number, data: any) {
  return post(
    `/api/data-management/datasets/${id}/files/upload/pre-upload`,
    data
  );
}

export function cancelUploadUsingPut(id) {
  return put(
    `/api/data-management/datasets/upload/cancel-upload/${id}`,
    {},
    { showLoading: false }
  );
}

export function uploadFileChunkUsingPost(id: string | number, params, config) {
  return post(
    `/api/data-management/datasets/${id}/files/upload/chunk`,
    params,
    {
      showLoading: false,
      ...config,
    }
  );
}
