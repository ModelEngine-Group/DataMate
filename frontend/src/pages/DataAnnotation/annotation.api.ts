import { get, post, put, del, download } from "@/utils/request";

// 标注任务管理相关接口
export function queryAnnotationTasksUsingGet(params?: any) {
  return get("/project/mappings/list", params);
}

export function createAnnotationTaskUsingPost(data: any) {
  return post("/api/project/create", data);
}

export function syncAnnotationTaskUsingPost(data: any) {
  return post(`/api/project/sync`, data);
}

export function queryAnnotationTaskByIdUsingGet(taskId: string | number) {
  return get(`/api/v1/annotation/tasks/${taskId}`);
}
export function deleteAnnotationTaskByIdUsingDelete(params?: any) {
  return del(`/api/project/mappings`, params);
}

// 智能预标注相关接口
export function preAnnotateUsingPost(data: any) {
  return post("/api/v1/annotation/pre-annotate", data);
}

// 标注数据管理接口
export function queryAnnotationDataUsingGet(
  taskId: string | number,
  params?: any
) {
  return get(`/api/v1/annotation/tasks/${taskId}/data`, params);
}

export function submitAnnotationUsingPost(taskId: string | number, data: any) {
  return post(`/api/v1/annotation/tasks/${taskId}/annotations`, data);
}

export function updateAnnotationUsingPut(
  taskId: string | number,
  annotationId: string | number,
  data: any
) {
  return put(
    `/api/v1/annotation/tasks/${taskId}/annotations/${annotationId}`,
    data
  );
}

export function deleteAnnotationUsingDelete(
  taskId: string | number,
  annotationId: string | number
) {
  return del(`/api/v1/annotation/tasks/${taskId}/annotations/${annotationId}`);
}

// 标注任务执行控制
export function startAnnotationTaskUsingPost(taskId: string | number) {
  return post(`/api/v1/annotation/tasks/${taskId}/start`);
}

export function pauseAnnotationTaskUsingPost(taskId: string | number) {
  return post(`/api/v1/annotation/tasks/${taskId}/pause`);
}

export function resumeAnnotationTaskUsingPost(taskId: string | number) {
  return post(`/api/v1/annotation/tasks/${taskId}/resume`);
}

export function completeAnnotationTaskUsingPost(taskId: string | number) {
  return post(`/api/v1/annotation/tasks/${taskId}/complete`);
}

// 标注任务统计信息
export function getAnnotationTaskStatisticsUsingGet(taskId: string | number) {
  return get(`/api/v1/annotation/tasks/${taskId}/statistics`);
}

export function getAnnotationStatisticsUsingGet(params?: any) {
  return get("/api/v1/annotation/statistics", params);
}

// 标注模板管理
export function queryAnnotationTemplatesUsingGet(params?: any) {
  return get("/api/v1/annotation/templates", params);
}

export function createAnnotationTemplateUsingPost(data: any) {
  return post("/api/v1/annotation/templates", data);
}

export function queryAnnotationTemplateByIdUsingGet(
  templateId: string | number
) {
  return get(`/api/v1/annotation/templates/${templateId}`);
}

export function updateAnnotationTemplateByIdUsingPut(
  templateId: string | number,
  data: any
) {
  return put(`/api/v1/annotation/templates/${templateId}`, data);
}

export function deleteAnnotationTemplateByIdUsingDelete(
  templateId: string | number
) {
  return del(`/api/v1/annotation/templates/${templateId}`);
}

// 主动学习相关接口
export function queryActiveLearningCandidatesUsingGet(
  taskId: string | number,
  params?: any
) {
  return get(
    `/api/v1/annotation/tasks/${taskId}/active-learning/candidates`,
    params
  );
}

export function submitActiveLearningFeedbackUsingPost(
  taskId: string | number,
  data: any
) {
  return post(
    `/api/v1/annotation/tasks/${taskId}/active-learning/feedback`,
    data
  );
}

export function updateActiveLearningModelUsingPost(
  taskId: string | number,
  data: any
) {
  return post(
    `/api/v1/annotation/tasks/${taskId}/active-learning/update-model`,
    data
  );
}

// 标注质量控制
export function validateAnnotationsUsingPost(
  taskId: string | number,
  data: any
) {
  return post(`/api/v1/annotation/tasks/${taskId}/validate`, data);
}

export function getAnnotationQualityReportUsingGet(taskId: string | number) {
  return get(`/api/v1/annotation/tasks/${taskId}/quality-report`);
}

// 标注数据导入导出
export function exportAnnotationsUsingPost(taskId: string | number, data: any) {
  return post(`/api/v1/annotation/tasks/${taskId}/export`, data);
}

export function importAnnotationsUsingPost(taskId: string | number, data: any) {
  return post(`/api/v1/annotation/tasks/${taskId}/import`, data);
}

export function downloadAnnotationsUsingGet(
  taskId: string | number,
  filename?: string
) {
  return download(
    `/api/v1/annotation/tasks/${taskId}/download`,
    null,
    filename
  );
}

// 标注者管理
export function queryAnnotatorsUsingGet(params?: any) {
  return get("/api/v1/annotation/annotators", params);
}

export function assignAnnotatorUsingPost(taskId: string | number, data: any) {
  return post(`/api/v1/annotation/tasks/${taskId}/assign`, data);
}

export function getAnnotatorStatisticsUsingGet(annotatorId: string | number) {
  return get(`/api/v1/annotation/annotators/${annotatorId}/statistics`);
}

// 标注配置管理
export function getAnnotationConfigUsingGet(taskId: string | number) {
  return get(`/api/v1/annotation/tasks/${taskId}/config`);
}

export function updateAnnotationConfigUsingPut(
  taskId: string | number,
  data: any
) {
  return put(`/api/v1/annotation/tasks/${taskId}/config`, data);
}

// 标注类型和标签管理
export function queryAnnotationTypesUsingGet() {
  return get("/api/v1/annotation/types");
}

export function queryAnnotationLabelsUsingGet(taskId: string | number) {
  return get(`/api/v1/annotation/tasks/${taskId}/labels`);
}

export function createAnnotationLabelUsingPost(
  taskId: string | number,
  data: any
) {
  return post(`/api/v1/annotation/tasks/${taskId}/labels`, data);
}

export function updateAnnotationLabelUsingPut(
  taskId: string | number,
  labelId: string | number,
  data: any
) {
  return put(`/api/v1/annotation/tasks/${taskId}/labels/${labelId}`, data);
}

export function deleteAnnotationLabelUsingDelete(
  taskId: string | number,
  labelId: string | number
) {
  return del(`/api/v1/annotation/tasks/${taskId}/labels/${labelId}`);
}

// 批量操作
export function batchAssignAnnotatorsUsingPost(data: any) {
  return post("/api/v1/annotation/tasks/batch-assign", data);
}

export function batchUpdateTaskStatusUsingPost(data: any) {
  return post("/api/v1/annotation/tasks/batch-update-status", data);
}

export function batchDeleteTasksUsingPost(data: { taskIds: string[] }) {
  return post("/api/v1/annotation/tasks/batch-delete", data);
}

// 标注进度跟踪
export function getAnnotationProgressUsingGet(taskId: string | number) {
  return get(`/api/v1/annotation/tasks/${taskId}/progress`);
}

// 标注审核
export function submitAnnotationReviewUsingPost(
  taskId: string | number,
  data: any
) {
  return post(`/api/v1/annotation/tasks/${taskId}/review`, data);
}

export function getAnnotationReviewResultsUsingGet(
  taskId: string | number,
  params?: any
) {
  return get(`/api/v1/annotation/tasks/${taskId}/reviews`, params);
}
