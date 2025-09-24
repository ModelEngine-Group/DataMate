const { addMockPrefix } = require("./mock-core/util.cjs");

const MockAPI = {
  // 数据归集接口
  queryTasksUsingPost: "/data-collection/tasks", // 获取数据源任务列表
  createTaskUsingPost: "/data-collection/tasks/create", // 创建数据源任务
  queryTaskByIdUsingGet: "/data-collection/tasks/:id", // 根据ID获取数据源任务详情
  updateTaskByIdUsingPut: "/data-collection/tasks/:id", // 更新数据源任务
  deleteTaskByIdUsingDelete: "/data-collection/tasks/:id", // 删除数据源任务
  executeTaskByIdUsingPost: "/data-collection/tasks/:id/execute", // 执行数据源任务
  stopTaskByIdUsingPost: "/data-collection/tasks/:id/stop", // 停止数据源任务
  queryExecutionLogUsingPost: "/data-collection/executions", // 获取任务执行日志
  queryExecutionLogByIdUsingGet: "/data-collection/executions/:id", // 获取任务执行日志详情
  queryCollectionStatisticsUsingGet: "/data-collection/monitor/statistics", // 获取数据归集统计信息

  // 数据管理接口
  queryDatasetsUsingPost: "/datasets", // 获取数据集列表
  createDatasetUsingPost: "/datasets/create", // 创建数据集
  queryDatasetByIdUsingGet: "/datasets/:id", // 根据ID获取数据集详情
  updateDatasetByIdUsingPut: "/datasets/:id", // 更新数据集
  deleteDatasetByIdUsingDelete: "/datasets/:id", // 删除数据集
  queryFilesUsingGet: "/datasets/:id/files", // 获取数据集文件列表
  uploadFileUsingPost: "/datasets/:id/files", // 添加数据集文件
  queryFileByIdUsingGet: "/datasets/:id/files/:fileId", // 获取数据集文件详情
  deleteFileByIdUsingDelete: "/datasets/:id/files/:fileId", // 删除数据集文件
  downloadFileByIdUsingGet: "/datasets/:id/files/:fileId/download", // 下载文件
  queryDatasetTypesUsingGet: "/dataset-types", // 获取数据集类型列表
  queryTagsUsingGet: "/dataset-tags", // 获取数据集标签列表
  createTagUsingPost: "/dataset-tags", // 创建数据集标签
  queryDatasetStatisticsUsingGet: "/datasets/statistics", // 获取数据集统计信息

  // 数据清洗接口
  queryCleaningRulesUsingGet: "/v1/cleaning/rules", // 获取清洗规则列表
  createCleaningRuleUsingPost: "/v1/cleaning/rules", //创建清洗规则
  queryCleaningRuleByIdUsingGet: "/v1/cleaning/rules/{ruleId}", // 根据ID获取清洗规则详情
  updateCleaningRuleByIdUsingPut: "/v1/cleaning/rules/{ruleId}", // 更新清洗规则
  deleteCleaningRuleByIdUsingDelete: "/v1/cleaning/rules/{ruleId}", // 删除清洗规则
  queryCleaningJobsUsingPost: "/v1/cleaning/jobs", // 获取清洗任务列表
  createCleaningJobUsingPost: "/v1/cleaning/jobs/create", // 创建清洗任务
  queryCleaningJobByIdUsingGet: "/v1/cleaning/jobs/{jobId}", // 根据ID获取清洗任务详情
  deleteCleaningJobByIdUsingDelete: "/v1/cleaning/jobs/{jobId}", // 删除清洗任务
  executeCleaningJobUsingPost: "/v1/cleaning/jobs/{jobId}/execute", // 执行清洗任务
  stopCleaningJobUsingPost: "/v1/cleaning/jobs/{jobId}/stop", // 停止清洗任务
  queryCleaningTemplatesUsingPost: "/v1/cleaning/templates", // 获取清洗模板列表
  createCleaningTemplateUsingPost: "/v1/cleaning/templates/create", // 创建清洗模板
  queryCleaningTemplateByIdUsingGet: "/v1/cleaning/templates/{templateId}", // 根据ID获取清洗模板详情
  deleteCleaningTemplateByIdUsingDelete:
    "/v1/cleaning/templates/{templateId}", // 删除清洗模板
};

module.exports = addMockPrefix("/api", MockAPI);
