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
  queryDatasetsUsingGet: "/data-management/datasets", // 获取数据集列表
  createDatasetUsingPost: "/data-management/datasets", // 创建数据集
  queryDatasetByIdUsingGet: "/data-management/datasets/:id", // 根据ID获取数据集详情
  updateDatasetByIdUsingPut: "/data-management/datasets/:id", // 更新数据集
  deleteDatasetByIdUsingDelete: "/data-management/datasets/:id", // 删除数据集
  queryFilesUsingGet: "/data-management/datasets/:id/files", // 获取数据集文件列表
  uploadFileUsingPost: "/data-management/datasets/:id/files", // 添加数据集文件
  queryFileByIdUsingGet: "/data-management/datasets/:id/files/:fileId", // 获取数据集文件详情
  deleteFileByIdUsingDelete: "/data-management/datasets/:id/files/:fileId", // 删除数据集文件
  downloadFileByIdUsingGet:
    "/data-management/datasets/:id/files/:fileId/download", // 下载文件
  queryDatasetTypesUsingGet: "/data-management/dataset-types", // 获取数据集类型列表
  queryTagsUsingGet: "/data-management/tags", // 获取数据集标签列表
  createTagUsingPost: "/data-management/tags", // 创建数据集标签
  updateTagUsingPost: "/data-management/tags", // 更新数据集标签
  deleteTagUsingPost: "/data-management/tags", // 删除数据集标签
  queryDatasetStatisticsUsingGet: "/data-management/datasets/statistics", // 获取数据集统计信息

  // 数据清洗接口
  queryCleaningTasksUsingGet: "/cleaning/tasks", // 获取清洗任务列表
  createCleaningTaskUsingPost: "/cleaning/tasks", // 创建清洗任务
  queryCleaningTaskByIdUsingGet: "/cleaning/tasks/:taskId", // 根据ID获取清洗任务详情
  deleteCleaningTaskByIdUsingDelete: "/cleaning/tasks/:taskId", // 删除清洗任务
  executeCleaningTaskUsingPost: "/cleaning/tasks/:taskId/execute", // 执行清洗任务
  stopCleaningTaskUsingPost: "/cleaning/tasks/:taskId/stop", // 停止清洗任务
  queryCleaningTemplatesUsingGet: "/cleaning/templates", // 获取清洗模板列表
  createCleaningTemplateUsingPost: "/cleaning/templates", // 创建清洗模板
  queryCleaningTemplateByIdUsingGet: "/cleaning/templates/:templateId", // 根据ID获取清洗模板详情
  updateCleaningTemplateByIdUsingPut: "/cleaning/templates/:templateId", // 根据ID更新清洗模板详情
  deleteCleaningTemplateByIdUsingDelete: "/cleaning/templates/:templateId", // 删除清洗模板

  // 数据标注接口
  queryAnnotationTasksUsingGet: "/annotation/tasks", // 获取标注任务列表
  createAnnotationTaskUsingPost: "/annotation/tasks/create", // 创建标注任务
  queryAnnotationTaskByIdUsingGet: "/annotation/tasks/:taskId", // 根据ID获取标注任务详情
  updateAnnotationTaskByIdUsingPut: "/annotation/tasks/:taskId", // 更新标注任务
  deleteAnnotationTaskByIdUsingDelete: "/annotation/tasks/:taskId", // 删除标注任务
  executeAnnotationTaskByIdUsingPost: "/annotation/tasks/:taskId/execute", // 执行标注任务
  stopAnnotationTaskByIdUsingPost: "/annotation/tasks/:taskId/stop", // 停止标注任务
  queryAnnotationDataUsingGet: "/annotation/data", // 获取标注数据列表
  submitAnnotationUsingPost: "/annotation/submit/:id", // 提交标注
  updateAnnotationUsingPut: "/annotation/update/:id", // 根据ID更新标注
  deleteAnnotationUsingDelete: "/annotation/delete/:id", // 根据ID删除标注
  startAnnotationTaskUsingPost: "/annotation/start/:taskId", // 开始标注任务
  pauseAnnotationTaskUsingPost: "/annotation/pause/:taskId", // 暂停标注任务
  resumeAnnotationTaskUsingPost: "/annotation/resume/:taskId", // 恢复标注任务
  completeAnnotationTaskUsingPost: "/annotation/complete/:taskId", // 完成标注任务
  getAnnotationTaskStatisticsUsingGet: "/annotation/statistics/:taskId", // 获取标注任务统计信息
  getAnnotationStatisticsUsingGet: "/annotation/statistics", // 获取标注统计信息
  queryAnnotationTemplatesUsingGet: "/annotation/templates", // 获取标注模板列表
  createAnnotationTemplateUsingPost: "/annotation/templates", // 创建标注模板
  queryAnnotationTemplateByIdUsingGet: "/annotation/templates/:templateId", // 根据ID获取标注模板详情
  queryAnnotatorsUsingGet: "/annotation/annotators", // 获取标注者列表
  assignAnnotatorUsingPost: "/annotation/annotators/:annotatorId", // 分配标注者

  // 数据合成接口
  querySynthesisJobsUsingGet: "/synthesis/jobs", // 获取合成任务列表
  createSynthesisJobUsingPost: "/synthesis/jobs/create", // 创建合成任务
  querySynthesisJobByIdUsingGet: "/synthesis/jobs/:jobId", // 根据ID获取合成任务详情
  updateSynthesisJobByIdUsingPut: "/synthesis/jobs/:jobId", // 更新合成任务
  deleteSynthesisJobByIdUsingDelete: "/synthesis/jobs/:jobId", // 删除合成任务
  executeSynthesisJobUsingPost: "/synthesis/jobs/execute/:jobId", // 执行合成任务
  stopSynthesisJobByIdUsingPost: "/synthesis/jobs/stop/:jobId", // 停止合成任务
  querySynthesisTemplatesUsingGet: "/synthesis/templates", // 获取合成模板列表
  createSynthesisTemplateUsingPost: "/synthesis/templates/create", // 创建合成模板
  querySynthesisTemplateByIdUsingGet: "/synthesis/templates/:templateId", // 根据ID获取合成模板详情
  updateSynthesisTemplateByIdUsingPut: "/synthesis/templates/:templateId", // 更新合成模板
  deleteSynthesisTemplateByIdUsingDelete: "/synthesis/templates/:templateId", // 删除合成模板
  queryInstructionTemplatesUsingPost: "/synthesis/templates", // 获取指令模板列表
  createInstructionTemplateUsingPost: "/synthesis/templates/create", // 创建指令模板
  queryInstructionTemplateByIdUsingGet: "/synthesis/templates/:templateId", // 根据ID获取指令模板详情
  deleteInstructionTemplateByIdUsingDelete: "/synthesis/templates/:templateId", // 删除指令模板
  instructionTuningUsingPost: "/synthesis/instruction-tuning", // 指令微调
  cotDistillationUsingPost: "/synthesis/cot-distillation", // Cot蒸馏
  queryOperatorsUsingPost: "/synthesis/operators", // 获取操作列表

  // 数据评测接口
  queryEvaluationTasksUsingPost: "/evaluation/tasks", // 获取评测任务列表
  createEvaluationTaskUsingPost: "/evaluation/tasks/create", // 创建评测任务
  queryEvaluationTaskByIdUsingGet: "/evaluation/tasks/:taskId", // 根据ID获取评测任务详情
  updateEvaluationTaskByIdUsingPut: "/evaluation/tasks/:taskId", // 更新评测任务
  deleteEvaluationTaskByIdUsingDelete: "/evaluation/tasks/:taskId", // 删除评测任务
  executeEvaluationTaskByIdUsingPost: "/evaluation/tasks/:taskId/execute", // 执行评测任务
  stopEvaluationTaskByIdUsingPost: "/evaluation/tasks/:taskId/stop", // 停止评测任务
  queryEvaluationReportsUsingPost: "/evaluation/reports", // 获取评测报告列表
  queryEvaluationReportByIdUsingGet: "/evaluation/reports/:reportId", // 根据ID获取评测报告详情
  manualEvaluateUsingPost: "/evaluation/manual-evaluate", // 人工评测
  queryEvaluationStatisticsUsingGet: "/evaluation/statistics", // 获取评测统计信息
  evaluateDataQualityUsingPost: "/evaluation/data-quality", // 数据质量评测
  getQualityEvaluationByIdUsingGet: "/evaluation/data-quality/:id", // 根据ID获取数据质量评测详情
  evaluateCompatibilityUsingPost: "/evaluation/compatibility", // 兼容性评测
  evaluateValueUsingPost: "/evaluation/value", // 价值评测
  queryEvaluationReportsUsingGet: "/evaluation/reports", // 获取评测报告列表（简化版）
  getEvaluationReportByIdUsingGet: "/evaluation/reports/:reportId", // 根据ID获取评测报告详情（简化版）
  exportEvaluationReportUsingGet: "/evaluation/reports/:reportId/export", // 导出评测报告
  batchEvaluationUsingPost: "/evaluation/batch-evaluate", // 批量评测

  // 知识生成接口
  queryKnowledgeBasesUsingPost: "/knowledge/bases", // 获取知识库列表
  createKnowledgeBaseUsingPost: "/knowledge/bases/create", // 创建知识库
  queryKnowledgeBaseByIdUsingGet: "/knowledge/bases/:baseId", // 根据ID获取知识库详情
  updateKnowledgeBaseByIdUsingPut: "/knowledge/bases/:baseId", // 更新知识库
  deleteKnowledgeBaseByIdUsingDelete: "/knowledge/bases/:baseId", // 删除知识库
  queryKnowledgeGenerationTasksUsingPost: "/knowledge/tasks", // 获取知识生成任务列表
  createKnowledgeGenerationTaskUsingPost: "/knowledge/tasks/create", // 创建知识生成任务
  queryKnowledgeGenerationTaskByIdUsingGet: "/knowledge/tasks/:taskId", // 根据ID获取知识生成任务详情
  updateKnowledgeGenerationTaskByIdUsingPut: "/knowledge/tasks/:taskId", // 更新知识生成任务
  deleteKnowledgeGenerationTaskByIdUsingDelete: "/knowledge/tasks/:taskId", // 删除知识生成任务
  executeKnowledgeGenerationTaskByIdUsingPost:
    "/knowledge/tasks/:taskId/execute", // 执行知识生成任务
  stopKnowledgeGenerationTaskByIdUsingPost: "/knowledge/tasks/:taskId/stop", // 停止知识生成任务
  queryKnowledgeStatisticsUsingGet: "/knowledge/statistics", // 获取知识生成

  // 算子市场
  queryOperatorsUsingPost: "/operators/list", // 获取算子列表
  queryCategoryTreeUsingGet: "/categories/tree", // 获取算子分类树
  queryOperatorByIdUsingGet: "/operators/:operatorId", // 根据ID获取算子详情
  createOperatorUsingPost: "/operators/create", // 创建算子
  updateOperatorByIdUsingPut: "/operators/:operatorId", // 更新算子
  uploadOperatorUsingPost: "/operators/upload", // 上传算子
  createLabelUsingPost: "/operators/labels", // 创建算子标签
  queryLabelsUsingGet: "/labels", // 获取算子标签列表
  deleteLabelsUsingDelete: "/labels", // 删除算子标签
  updateLabelByIdUsingPut: "/labels/:labelId", // 更新算子标签
  deleteOperatorByIdUsingDelete: "/operators/:operatorId", // 删除算子
  publishOperatorUsingPost: "/operators/:operatorId/publish", // 发布算子
  unpublishOperatorUsingPost: "/operators/:operatorId/unpublish", // 下架算子
};

module.exports = addMockPrefix("/api", MockAPI);
