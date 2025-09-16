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
  queryDatasetsUsingGet: "/datasets", // 获取数据集列表
  createDatasetUsingPost: "/datasets/create", // 创建数据集
  getDatasetByIdUsingGet: "/datasets/:id", // 根据ID获取数据集详情
  updateDatasetByIdUsingPut: "/datasets/:id", // 更新数据集
  deleteDatasetByIdUsingDelete: "/datasets/:id", // 删除数据集
  queryDatasetFilesUsingGet: "/datasets/:id/files", // 获取数据集文件列表
  addDatasetFileUsingPost: "/datasets/:id/files", // 添加数据集文件
  getDatasetFileByIdUsingGet: "/datasets/:id/files/:fileId", // 获取数据集文件详情
  deleteDatasetFileByIdUsingDelete: "/datasets/:id/files/:fileId", // 删除数据集文件
  downloadFileByIdUsingGet: "/datasets/:id/files/:fileId/download", // 下载文件
  queryDatasetTypesUsingGet: "/dataset-types", // 获取数据集类型列表
  queryDatasetTagsUsingGet: "/datasets/tags", // 获取数据集标签列表
  createDatasetTagsUsingPost: "/datasets/tags", // 创建数据集标签
  getDatasetStatisticsUsingGet: "/datasets/statistics", // 获取数据集统计信息

  // 数据清洗接口
  queryCleaningRulesUsingGet: "/api/v1/cleaning/rules", // 获取清洗规则列表
  createCleaningRuleUsingPost: "/api/v1/cleaning/rules", //创建清洗规则
  queryCleaningRuleByIdUsingGet: "/api/v1/cleaning/rules/{ruleId}", // 根据ID获取清洗规则详情
  updateCleaningRuleByIdUsingPut: "/api/v1/cleaning/rules/{ruleId}", // 更新清洗规则
  deleteCleaningRuleByIdUsingDelete: "/api/v1/cleaning/rules/{ruleId}", // 删除清洗规则
  queryCleaningJobsUsingGet: "/api/v1/cleaning/jobs", // 获取清洗任务列表
  createCleaningJobUsingPost: "/api/v1/cleaning/jobs", // 创建清洗任务
  queryCleaningJobByIdUsingGet: "/api/v1/cleaning/jobs/{jobId}", // 根据ID获取清洗任务详情
  deleteCleaningJobByIdUsingDelete: "/api/v1/cleaning/jobs/{jobId}", // 删除清洗任务
  executeCleaningJobUsingPost: "/api/v1/cleaning/jobs/{jobId}/execute", // 执行清洗任务
  stopCleaningJobUsingPost: "/api/v1/cleaning/jobs/{jobId}/stop", // 停止清洗任务
  queryCleaningTemplatesUsingGet: "/api/v1/cleaning/templates", // 获取清洗模板列表
  createCleaningTemplateUsingPost: "/api/v1/cleaning/templates", // 创建清洗模板
  queryCleaningTemplateByIdUsingGet: "/api/v1/cleaning/templates/{templateId}", // 根据ID获取清洗模板详情
  deleteCleaningTemplateByIdUsingDelete:
    "/api/v1/cleaning/templates/{templateId}", // 删除清洗模板
};

module.exports = addMockPrefix("/api", MockAPI);
