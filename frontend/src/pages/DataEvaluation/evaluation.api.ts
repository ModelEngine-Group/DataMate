import { get, post, put, del, download } from "@/utils/request";

export function createEvaluationTaskUsingPost(data: any) {
  return post("/api/evaluation/tasks", data);
}

export function getPagedEvaluationTaskUsingGet(params?: any) {
  return get("/api/evaluation/tasks", params);
}

export function deleteEvaluationTaskUsingGet(id: string) {
  const url = `/api/evaluation/tasks?ids=${id}`;
  return del(url);
}

export function queryPromptTemplatesUsingGet() {
  return get("/api/evaluation/prompt-templates");
}

export function getEvaluationTaskByIdUsingGet(taskId: string | number) {
  return get(`/api/evaluation/tasks/${taskId}`);
}

export function queryEvaluationFilesUsingGet(params: {
  taskId: string;
  page?: number;
  size?: number;
}) {
  const { taskId, ...rest } = params;
  return get(`/api/evaluation/tasks/${taskId}/files`, rest);
}

export function queryEvaluationItemsUsingGet(params: {
  taskId: string;
  page?: number;
  size?: number;
  status?: string;
  file_id?: string;
}) {
  const { taskId, ...rest } = params;
  return get(`/api/evaluation/tasks/${taskId}/items`, rest);
}

// 数据质量评估相关接口
export function evaluateDataQualityUsingPost(data: any) {
  return post("/api/v1/evaluation/quality", data);
}

export function getQualityEvaluationByIdUsingGet(evaluationId: string | number) {
  return get(`/api/v1/evaluation/quality/${evaluationId}`);
}

// 适配性评估相关接口
export function evaluateCompatibilityUsingPost(data: any) {
  return post("/api/v1/evaluation/compatibility", data);
}

// 价值评估相关接口
export function evaluateValueUsingPost(data: any) {
  return post("/api/v1/evaluation/value", data);
}

// 评估报告管理接口
export function queryEvaluationReportsUsingGet(params?: any) {
  return get("/api/v1/evaluation/reports", params);
}

export function getEvaluationReportByIdUsingGet(reportId: string | number) {
  return get(`/api/v1/evaluation/reports/${reportId}`);
}

export function exportEvaluationReportUsingGet(reportId: string | number, format = "PDF", filename?: string) {
  return download(`/api/v1/evaluation/reports/${reportId}/export`, { format }, filename);
}

// 批量评估接口
export function batchEvaluationUsingPost(data: any) {
  return post("/api/v1/evaluation/batch", data);
}

// 扩展功能接口（基于常见需求添加）

// 评估模板管理
export function queryEvaluationTemplatesUsingGet(params?: any) {
  return get("/api/v1/evaluation/templates", params);
}

export function createEvaluationTemplateUsingPost(data: any) {
  return post("/api/v1/evaluation/templates", data);
}

export function getEvaluationTemplateByIdUsingGet(templateId: string | number) {
  return get(`/api/v1/evaluation/templates/${templateId}`);
}

export function updateEvaluationTemplateByIdUsingPut(templateId: string | number, data: any) {
  return put(`/api/v1/evaluation/templates/${templateId}`, data);
}

export function deleteEvaluationTemplateByIdUsingDelete(templateId: string | number) {
  return del(`/api/v1/evaluation/templates/${templateId}`);
}

// 评估历史记录
export function queryEvaluationHistoryUsingGet(params?: any) {
  return get("/api/v1/evaluation/history", params);
}

export function getEvaluationHistoryByDatasetUsingGet(datasetId: string | number, params?: any) {
  return get(`/api/v1/evaluation/history/dataset/${datasetId}`, params);
}

// 评估指标配置
export function queryQualityMetricsUsingGet() {
  return get("/api/v1/evaluation/metrics/quality");
}

export function queryCompatibilityMetricsUsingGet() {
  return get("/api/v1/evaluation/metrics/compatibility");
}

export function queryValueMetricsUsingGet() {
  return get("/api/v1/evaluation/metrics/value");
}

// 评估规则管理
export function queryEvaluationRulesUsingGet(params?: any) {
  return get("/api/v1/evaluation/rules", params);
}

export function createEvaluationRuleUsingPost(data: any) {
  return post("/api/v1/evaluation/rules", data);
}

export function updateEvaluationRuleByIdUsingPut(ruleId: string | number, data: any) {
  return put(`/api/v1/evaluation/rules/${ruleId}`, data);
}

export function deleteEvaluationRuleByIdUsingDelete(ruleId: string | number) {
  return del(`/api/v1/evaluation/rules/${ruleId}`);
}

// 评估统计信息
export function getEvaluationStatisticsUsingGet(params?: any) {
  return get("/api/v1/evaluation/statistics", params);
}

export function getDatasetEvaluationSummaryUsingGet(datasetId: string | number) {
  return get(`/api/v1/evaluation/datasets/${datasetId}/summary`);
}

// 评估任务管理
export function queryEvaluationTasksUsingGet(params?: any) {
  return get("/api/v1/evaluation/tasks", params);
}

export function cancelEvaluationTaskUsingPost(taskId: string | number) {
  return post(`/api/v1/evaluation/tasks/${taskId}/cancel`);
}

export function retryEvaluationTaskUsingPost(taskId: string | number) {
  return post(`/api/v1/evaluation/tasks/${taskId}/retry`);
}

// 评估结果比较
export function compareEvaluationResultsUsingPost(data: any) {
  return post("/api/v1/evaluation/compare", data);
}

// 评估配置管理
export function getEvaluationConfigUsingGet() {
  return get("/api/v1/evaluation/config");
}

export function updateEvaluationConfigUsingPut(data: any) {
  return put("/api/v1/evaluation/config", data);
}

// 数据质量监控
export function createQualityMonitorUsingPost(data: any) {
  return post("/api/v1/evaluation/quality/monitors", data);
}

export function queryQualityMonitorsUsingGet(params?: any) {
  return get("/api/v1/evaluation/quality/monitors", params);
}

export function updateQualityMonitorByIdUsingPut(monitorId: string | number, data: any) {
  return put(`/api/v1/evaluation/quality/monitors/${monitorId}`, data);
}

export function deleteQualityMonitorByIdUsingDelete(monitorId: string | number) {
  return del(`/api/v1/evaluation/quality/monitors/${monitorId}`);
}

// 评估基准管理
export function queryEvaluationBenchmarksUsingGet(params?: any) {
  return get("/api/v1/evaluation/benchmarks", params);
}

export function createEvaluationBenchmarkUsingPost(data: any) {
  return post("/api/v1/evaluation/benchmarks", data);
}

export function updateEvaluationBenchmarkByIdUsingPut(benchmarkId: string | number, data: any) {
  return put(`/api/v1/evaluation/benchmarks/${benchmarkId}`, data);
}

export function deleteEvaluationBenchmarkByIdUsingDelete(benchmarkId: string | number) {
  return del(`/api/v1/evaluation/benchmarks/${benchmarkId}`);
}

// 评估算法管理
export function queryEvaluationAlgorithmsUsingGet(params?: any) {
  return get("/api/v1/evaluation/algorithms", params);
}

export function runCustomEvaluationUsingPost(data: any) {
  return post("/api/v1/evaluation/custom", data);
}

// 评估可视化数据
export function getEvaluationVisualizationUsingGet(evaluationId: string | number, chartType?: string) {
  return get(`/api/v1/evaluation/${evaluationId}/visualization`, { chartType });
}

// 评估通知和警报
export function queryEvaluationAlertsUsingGet(params?: any) {
  return get("/api/v1/evaluation/alerts", params);
}

export function createEvaluationAlertUsingPost(data: any) {
  return post("/api/v1/evaluation/alerts", data);
}

export function updateEvaluationAlertByIdUsingPut(alertId: string | number, data: any) {
  return put(`/api/v1/evaluation/alerts/${alertId}`, data);
}

export function deleteEvaluationAlertByIdUsingDelete(alertId: string | number) {
  return del(`/api/v1/evaluation/alerts/${alertId}`);
}

// 批量操作扩展
export function batchDeleteEvaluationReportsUsingPost(data: { reportIds: string[] }) {
  return post("/api/v1/evaluation/reports/batch-delete", data);
}

export function batchExportEvaluationReportsUsingPost(data: any) {
  return post("/api/v1/evaluation/reports/batch-export", data);
}

// 评估调度管理
export function queryEvaluationSchedulesUsingGet(params?: any) {
  return get("/api/v1/evaluation/schedules", params);
}

export function createEvaluationScheduleUsingPost(data: any) {
  return post("/api/v1/evaluation/schedules", data);
}

export function updateEvaluationScheduleByIdUsingPut(scheduleId: string | number, data: any) {
  return put(`/api/v1/evaluation/schedules/${scheduleId}`, data);
}

export function deleteEvaluationScheduleByIdUsingDelete(scheduleId: string | number) {
  return del(`/api/v1/evaluation/schedules/${scheduleId}`);
}

export function enableEvaluationScheduleUsingPost(scheduleId: string | number) {
  return post(`/api/v1/evaluation/schedules/${scheduleId}/enable`);
}

export function disableEvaluationScheduleUsingPost(scheduleId: string | number) {
  return post(`/api/v1/evaluation/schedules/${scheduleId}/disable`);
}
