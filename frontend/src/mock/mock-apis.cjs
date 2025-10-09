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
  queryCleaningRuleByIdUsingGet: "/v1/cleaning/rules/:ruleId", // 根据ID获取清洗规则详情
  updateCleaningRuleByIdUsingPut: "/v1/cleaning/rules/:ruleId", // 更新清洗规则
  deleteCleaningRuleByIdUsingDelete: "/v1/cleaning/rules/:ruleId", // 删除清洗规则
  queryCleaningJobsUsingPost: "/v1/cleaning/jobs", // 获取清洗任务列表
  createCleaningJobUsingPost: "/v1/cleaning/jobs/create", // 创建清洗任务
  queryCleaningJobByIdUsingGet: "/v1/cleaning/jobs/:jobId", // 根据ID获取清洗任务详情
  deleteCleaningJobByIdUsingDelete: "/v1/cleaning/jobs/:jobId", // 删除清洗任务
  executeCleaningJobUsingPost: "/v1/cleaning/jobs/:jobId/execute", // 执行清洗任务
  stopCleaningJobUsingPost: "/v1/cleaning/jobs/:jobId/stop", // 停止清洗任务
  queryCleaningTemplatesUsingPost: "/v1/cleaning/templates", // 获取清洗模板列表
  createCleaningTemplateUsingPost: "/v1/cleaning/templates/create", // 创建清洗模板
  queryCleaningTemplateByIdUsingGet: "/v1/cleaning/templates/:templateId", // 根据ID获取清洗模板详情
  deleteCleaningTemplateByIdUsingDelete: "/v1/cleaning/templates/:templateId", // 删除清洗模板

  // 数据标注接口
  queryAnnotationTasksUsingGet: "/v1/annotation/tasks", // 获取标注任务列表
  createAnnotationTaskUsingPost: "/v1/annotation/tasks/create", // 创建标注任务
  queryAnnotationTaskByIdUsingGet: "/v1/annotation/tasks/:taskId", // 根据ID获取标注任务详情
  updateAnnotationTaskByIdUsingPut: "/v1/annotation/tasks/:taskId", // 更新标注任务
  deleteAnnotationTaskByIdUsingDelete: "/v1/annotation/tasks/:taskId", // 删除标注任务
  executeAnnotationTaskByIdUsingPost: "/v1/annotation/tasks/:taskId/execute", // 执行标注任务
  stopAnnotationTaskByIdUsingPost: "/v1/annotation/tasks/:taskId/stop", // 停止标注任务
  queryAnnotationDataUsingGet: "/v1/annotation/data", // 获取标注数据列表
  submitAnnotationUsingPost: "/v1/annotation/submit/:id", // 提交标注
  updateAnnotationUsingPut: "/v1/annotation/update/:id", // 根据ID更新标注
  deleteAnnotationUsingDelete: "/v1/annotation/delete/:id", // 根据ID删除标注
  startAnnotationTaskUsingPost: "/v1/annotation/start/:taskId", // 开始标注任务
  pauseAnnotationTaskUsingPost: "/v1/annotation/pause/:taskId", // 暂停标注任务
  resumeAnnotationTaskUsingPost: "/v1/annotation/resume/:taskId", // 恢复标注任务
  completeAnnotationTaskUsingPost: "/v1/annotation/complete/:taskId", // 完成标注任务
  getAnnotationTaskStatisticsUsingGet: "/v1/annotation/statistics/:taskId", // 获取标注任务统计信息
  getAnnotationStatisticsUsingGet: "/v1/annotation/statistics", // 获取标注统计信息
  queryAnnotationTemplatesUsingGet: "/v1/annotation/templates", // 获取标注模板列表
  createAnnotationTemplateUsingPost: "/v1/annotation/templates", // 创建标注模板
  queryAnnotationTemplateByIdUsingGet: "/v1/annotation/templates/:templateId", // 根据ID获取标注模板详情
  queryAnnotatorsUsingGet: "/v1/annotation/annotators", // 获取标注者列表
  assignAnnotatorUsingPost: "/v1/annotation/annotators/:annotatorId", // 分配标注者

  // 数据合成接口
  querySynthesisJobsUsingGet: "/v1/synthesis/jobs", // 获取合成任务列表
  createSynthesisJobUsingPost: "/v1/synthesis/jobs/create", // 创建合成任务
  querySynthesisJobByIdUsingGet: "/v1/synthesis/jobs/:jobId", // 根据ID获取合成任务详情
  updateSynthesisJobByIdUsingPut: "/v1/synthesis/jobs/:jobId", // 更新合成任务
  deleteSynthesisJobByIdUsingDelete: "/v1/synthesis/jobs/:jobId", // 删除合成任务
  executeSynthesisJobUsingPost: "/v1/synthesis/jobs/execute/:jobId", // 执行合成任务
  stopSynthesisJobByIdUsingPost: "/v1/synthesis/jobs/stop/:jobId", // 停止合成任务
  querySynthesisTemplatesUsingGet: "/v1/synthesis/templates", // 获取合成模板列表
  createSynthesisTemplateUsingPost: "/v1/synthesis/templates/create", // 创建合成模板
  querySynthesisTemplateByIdUsingGet: "/v1/synthesis/templates/:templateId", // 根据ID获取合成模板详情
  updateSynthesisTemplateByIdUsingPut: "/v1/synthesis/templates/:templateId", // 更新合成模板
  deleteSynthesisTemplateByIdUsingDelete: "/v1/synthesis/templates/:templateId", // 删除合成模板
  queryInstructionTemplatesUsingPost: "/v1/synthesis/templates", // 获取指令模板列表
  createInstructionTemplateUsingPost: "/v1/synthesis/templates/create", // 创建指令模板
  queryInstructionTemplateByIdUsingGet: "/v1/synthesis/templates/:templateId", // 根据ID获取指令模板详情
  deleteInstructionTemplateByIdUsingDelete:
    "/v1/synthesis/templates/:templateId", // 删除指令模板
  instructionTuningUsingPost: "/v1/synthesis/instruction-tuning", // 指令微调
  cotDistillationUsingPost: "/v1/synthesis/cot-distillation", // Cot蒸馏
  queryOperatorsUsingPost: "/v1/synthesis/operators", // 获取操作列表

  // 数据评测接口
  queryEvaluationTasksUsingPost: "/v1/evaluation/tasks", // 获取评测任务列表
  createEvaluationTaskUsingPost: "/v1/evaluation/tasks/create", // 创建评测任务
  queryEvaluationTaskByIdUsingGet: "/v1/evaluation/tasks/:taskId", // 根据ID获取评测任务详情
  updateEvaluationTaskByIdUsingPut: "/v1/evaluation/tasks/:taskId", // 更新评测任务
  deleteEvaluationTaskByIdUsingDelete: "/v1/evaluation/tasks/:taskId", // 删除评测任务
  executeEvaluationTaskByIdUsingPost: "/v1/evaluation/tasks/:taskId/execute", // 执行评测任务
  stopEvaluationTaskByIdUsingPost: "/v1/evaluation/tasks/:taskId/stop", // 停止评测任务
  queryEvaluationReportsUsingPost: "/v1/evaluation/reports", // 获取评测报告列表
  queryEvaluationReportByIdUsingGet: "/v1/evaluation/reports/:reportId", // 根据ID获取评测报告详情
  manualEvaluateUsingPost: "/v1/evaluation/manual-evaluate", // 人工评测
  queryEvaluationStatisticsUsingGet: "/v1/evaluation/statistics", // 获取评测统计信息
  evaluateDataQualityUsingPost: "/v1/evaluation/data-quality", // 数据质量评测
  getQualityEvaluationByIdUsingGet: "/v1/evaluation/data-quality/:id", // 根据ID获取数据质量评测详情
  evaluateCompatibilityUsingPost: "/v1/evaluation/compatibility", // 兼容性评测
  evaluateValueUsingPost: "/v1/evaluation/value", // 价值评测
  queryEvaluationReportsUsingGet: "/v1/evaluation/reports", // 获取评测报告列表（简化版）
  getEvaluationReportByIdUsingGet: "/v1/evaluation/reports/:reportId", // 根据ID获取评测报告详情（简化版）
  exportEvaluationReportUsingGet: "/v1/evaluation/reports/:reportId/export", // 导出评测报告
  batchEvaluationUsingPost: "/v1/evaluation/batch-evaluate", // 批量评测

  // 知识生成接口
  queryKnowledgeBasesUsingPost: "/v1/knowledge/bases", // 获取知识库列表
  createKnowledgeBaseUsingPost: "/v1/knowledge/bases/create", // 创建知识库
  queryKnowledgeBaseByIdUsingGet: "/v1/knowledge/bases/:baseId", // 根据ID获取知识库详情
  updateKnowledgeBaseByIdUsingPut: "/v1/knowledge/bases/:baseId", // 更新知识库
  deleteKnowledgeBaseByIdUsingDelete: "/v1/knowledge/bases/:baseId", // 删除知识库
  queryKnowledgeGenerationTasksUsingPost: "/v1/knowledge/tasks", // 获取知识生成任务列表
  createKnowledgeGenerationTaskUsingPost: "/v1/knowledge/tasks/create", // 创建知识生成任务
  queryKnowledgeGenerationTaskByIdUsingGet: "/v1/knowledge/tasks/:taskId", // 根据ID获取知识生成任务详情
  updateKnowledgeGenerationTaskByIdUsingPut: "/v1/knowledge/tasks/:taskId", // 更新知识生成任务
  deleteKnowledgeGenerationTaskByIdUsingDelete: "/v1/knowledge/tasks/:taskId", // 删除知识生成任务
  executeKnowledgeGenerationTaskByIdUsingPost:
    "/v1/knowledge/tasks/:taskId/execute", // 执行知识生成任务
  stopKnowledgeGenerationTaskByIdUsingPost: "/v1/knowledge/tasks/:taskId/stop", // 停止知识生成任务
  queryKnowledgeStatisticsUsingGet: "/v1/knowledge/statistics", // 获取知识生成

  // 算子市场
  createOperatorUsingPost: "/v1/operators", // 创建算子
  uploadOperatorUsingPost: "/v1/operators/upload", // 上传算子
  deleteCategoryUsingDelete: "/v1/operators/categories/:categoryId", // 删除算子分类
  createCategoryUsingPost: "/v1/operators/categories", // 创建算子分类
  queryCategoryTreeUsingGet: "/v1/operators/categories/tree", // 获取算子分类树
  createLabelUsingPost: "/v1/operators/labels", // 创建算子标签
  queryLabelsUsingGet: "/v1/operators/labels", // 获取算子标签列表
  deleteLabelsUsingDelete: "/v1/operators/labels", // 删除算子标签
  updateLabelByIdUsingPut: "/v1/operators/labels/:labelId", // 更新算子标签
  queryOperatorsUsingGet: "/v1/operators", // 获取算子列表
  queryOperatorByIdUsingGet: "/v1/operators/:operatorId", // 根据ID获取算子详情
  updateOperatorByIdUsingPut: "/v1/operators/:operatorId", // 更新算子
  deleteOperatorByIdUsingDelete: "/v1/operators/:operatorId", // 删除算子
  publishOperatorUsingPost: "/v1/operators/:operatorId/publish", // 发布算子
  unpublishOperatorUsingPost: "/v1/operators/:operatorId/unpublish", // 下架算子
  rateOperatorUsingPost: "/v1/operators/:operatorId/rate", // 评分算子
  queryOperatorRatingsUsingGet: "/v1/operators/:operatorId/ratings", // 获取算子评分列表
  queryOperatorStatisticsUsingGet: "/v1/operators/statistics", // 获取算子统计信息
};

module.exports = addMockPrefix("/api", MockAPI);
