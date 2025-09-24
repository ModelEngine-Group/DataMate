import { get, post, put, del } from "@/utils/request";

// 清洗规则相关接口
export function queryCleaningRulesUsingGet(params?: any) {
  return get("/api/v1/cleaning/rules", params);
}

export function createCleaningRuleUsingPost(data: any) {
  return post("/api/v1/cleaning/rules", data);
}

export function queryCleaningRuleByIdUsingGet(ruleId: string | number) {
  return get(`/api/v1/cleaning/rules/${ruleId}`);
}

export function updateCleaningRuleByIdUsingPut(ruleId: string | number, data: any) {
  return put(`/api/v1/cleaning/rules/${ruleId}`, data);
}

export function deleteCleaningRuleByIdUsingDelete(ruleId: string | number) {
  return del(`/api/v1/cleaning/rules/${ruleId}`);
}

// 清洗任务相关接口
export function queryCleaningJobsUsingGet(params?: any) {
  return post("/api/v1/cleaning/jobs", params);
}

export function createCleaningJobUsingPost(data: any) {
  return post("/api/v1/cleaning/jobs/create", data);
}

export function queryCleaningJobByIdUsingGet(jobId: string | number) {
  return get(`/api/v1/cleaning/jobs/${jobId}`);
}

export function updateCleaningJobByIdUsingPut(jobId: string | number, data: any) {
  return put(`/api/v1/cleaning/jobs/${jobId}`, data);
}

export function deleteCleaningJobByIdUsingDelete(jobId: string | number) {
  return del(`/api/v1/cleaning/jobs/${jobId}`);
}

export function executeCleaningJobUsingPost(jobId: string | number, data?: any) {
  return post(`/api/v1/cleaning/jobs/${jobId}/execute`, data);
}

export function stopCleaningJobUsingPost(jobId: string | number, data?: any) {
  return post(`/api/v1/cleaning/jobs/${jobId}/stop`, data);
}

// 清洗模板相关接口
export function queryCleaningTemplatesUsingPost(params?: any) {
  return post("/api/v1/cleaning/templates", params);
}

export function createCleaningTemplateUsingPost(data: any) {
  return post("/api/v1/cleaning/templates/create", data);
}

export function queryCleaningTemplateByIdUsingGet(templateId: string | number) {
  return get(`/api/v1/cleaning/templates/${templateId}`);
}

export function updateCleaningTemplateByIdUsingPut(templateId: string | number, data: any) {
  return put(`/api/v1/cleaning/templates/${templateId}`, data);
}

export function deleteCleaningTemplateByIdUsingDelete(templateId: string | number) {
  return del(`/api/v1/cleaning/templates/${templateId}`);
}






