import { get, post, put, del, download } from "@/utils/request";

// 标注任务管理相关接口
export function queryAnnotationTasksUsingGet(params?: any) {
  return get("/api/annotation/project", params);
}

export function createAnnotationTaskUsingPost(data: any) {
  return post("/api/annotation/project", data);
}

export function syncAnnotationTaskUsingPost(data: any) {
  return post(`/api/annotation/task/sync`, data);
}

export function deleteAnnotationTaskByIdUsingDelete(mappingId: string) {
  // Backend expects mapping UUID as path parameter
  return del(`/api/annotation/project/${mappingId}`);
}

// 手动标注：查询/更新映射当前关联的 DM 文件列表（用于“编辑任务数据集”）
export function getManualAnnotationMappingFilesUsingGet(mappingId: string) {
  return get(`/api/annotation/project/${mappingId}/files`);
}

export function updateManualAnnotationMappingFilesUsingPut(mappingId: string, data: any) {
  return put(`/api/annotation/project/${mappingId}/files`, data);
}

// 标签配置管理
export function getTagConfigUsingGet() {
  return get("/api/annotation/tags/config");
}

// 标注模板管理
export function queryAnnotationTemplatesUsingGet(params?: any) {
  return get("/api/annotation/template", params);
}

export function createAnnotationTemplateUsingPost(data: any) {
  return post("/api/annotation/template", data);
}

export function updateAnnotationTemplateByIdUsingPut(
  templateId: string | number,
  data: any
) {
  return put(`/api/annotation/template/${templateId}`, data);
}

export function deleteAnnotationTemplateByIdUsingDelete(
  templateId: string | number
) {
  return del(`/api/annotation/template/${templateId}`);
}

// 自动标注任务管理
export function queryAutoAnnotationTasksUsingGet(params?: any) {
  return get("/api/annotation/auto", params);
}

export function createAutoAnnotationTaskUsingPost(data: any) {
  return post("/api/annotation/auto", data);
}

export function deleteAutoAnnotationTaskByIdUsingDelete(taskId: string) {
  return del(`/api/annotation/auto/${taskId}`);
}

export function loginAnnotationUsingGet(mappingId: string) {
  return get(`/api/annotation/project/${mappingId}/login`);
}

// 手动标注：从 Label Studio 导回标注结果到某个数据集（导出为文件写入数据集）
export function importManualAnnotationFromLabelStudioUsingPost(
  mappingId: string,
  data: { exportFormat?: string; fileName?: string }
) {
  return post(`/api/annotation/project/${mappingId}/sync-label-studio-back`, data);
}

// 手动标注：将 Label Studio 中的标注结果同步回数据库（更新 t_dm_dataset_files.tags/annotation）
export function syncManualAnnotationToDatabaseUsingPost(mappingId: string) {
  return post(`/api/annotation/project/${mappingId}/sync-db`);
}

export function downloadAutoAnnotationResultUsingGet(taskId: string) {
  return download(`/api/annotation/auto/${taskId}/download`);
}

// 自动标注结果同步到 Label Studio（写入 predictions）
export function syncAutoAnnotationTaskToLabelStudioUsingPost(taskId: string) {
  return post(`/api/annotation/auto/${taskId}/sync-label-studio`);
}

// 从 Label Studio 导回自动标注任务的标注结果（导出为文件写入指定数据集）
export function importAutoAnnotationFromLabelStudioUsingPost(
  taskId: string,
  data: { exportFormat?: string; fileName?: string }
) {
  return post(`/api/annotation/auto/${taskId}/sync-label-studio-back`, data);
}

// 自动标注：将 Label Studio 中的标注结果同步回数据库（更新 t_dm_dataset_files.tags/annotation）
export function syncAutoAnnotationToDatabaseUsingPost(taskId: string) {
  return post(`/api/annotation/auto/${taskId}/sync-db`);
}

// 查询自动标注任务关联的 Label Studio 项目
export function getAutoAnnotationLabelStudioProjectUsingGet(taskId: string) {
  return get(`/api/annotation/auto/${taskId}/label-studio-project`);
}

// 查询自动标注任务当前关联的 DM 文件列表（用于编辑任务数据集弹窗预选）
export function getAutoAnnotationTaskFilesUsingGet(taskId: string) {
  return get(`/api/annotation/auto/${taskId}/files`);
}

// 更新自动标注任务所关联的数据集文件，并触发重新调度与 LS 同步
export function updateAutoAnnotationTaskFilesUsingPut(taskId: string, data: any) {
  return put(`/api/annotation/auto/${taskId}/files`, data);
}
