const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 合成类型枚举
const SynthesisTypes = [
  "INSTRUCTION_TUNING",
  "COT_DISTILLATION", 
  "DIALOGUE_GENERATION",
  "TEXT_AUGMENTATION",
  "MULTIMODAL_SYNTHESIS",
  "CUSTOM"
];

// 任务状态枚举
const JobStatuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"];

// 模型配置
function modelConfigItem() {
  return {
    modelName: Mock.Random.pick([
      "gpt-3.5-turbo",
      "gpt-4",
      "claude-3",
      "llama-2-70b",
      "qwen-max"
    ]),
    temperature: Mock.Random.float(0.1, 1.0, 2, 2),
    maxTokens: Mock.Random.pick([512, 1024, 2048, 4096]),
    topP: Mock.Random.float(0.1, 1.0, 2, 2),
    frequencyPenalty: Mock.Random.float(0, 2.0, 2, 2)
  };
}

// 合成模板数据
function synthesisTemplateItem() {
  const type = Mock.Random.pick(SynthesisTypes);
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 30),
    type,
    category: Mock.Random.pick([
      "教育培训", "对话系统", "内容生成", "代码生成", "多模态", "自定义"
    ]),
    modelConfig: modelConfigItem(),
    enabled: Mock.Random.boolean(),
    promptTemplate: type === "INSTRUCTION_TUNING" 
      ? "请根据以下主题生成一个指令：{topic}\n指令应该包含：\n1. 明确的任务描述\n2. 具体的输入要求\n3. 期望的输出格式"
      : type === "COT_DISTILLATION"
      ? "问题：{question}\n请提供详细的推理步骤，然后给出最终答案。\n推理过程：\n1. 分析问题的关键信息\n2. 应用相关知识和规则\n3. 逐步推导出结论"
      : "请根据以下模板生成内容：{template}",
    parameters: {
      maxLength: Mock.Random.integer(100, 2000),
      diversity: Mock.Random.float(0.1, 1.0, 2, 2),
      quality: Mock.Random.float(0.7, 1.0, 2, 2)
    },
    examples: new Array(Mock.Random.integer(2, 5)).fill(null).map(() => ({
      input: Mock.Random.csentence(10, 30),
      output: Mock.Random.csentence(20, 50),
      explanation: Mock.Random.csentence(5, 20)
    })),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss")
  };
}

const synthesisTemplateList = new Array(25).fill(null).map(synthesisTemplateItem);

// 合成任务数据
function synthesisJobItem() {
  const template = Mock.Random.pick(synthesisTemplateList);
  const targetCount = Mock.Random.integer(100, 10000);
  const generatedCount = Mock.Random.integer(0, targetCount);
  const progress = targetCount > 0 ? (generatedCount / targetCount) * 100 : 0;
  
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 30),
    templateId: template.id,
    template: {
      id: template.id,
      name: template.name,
      type: template.type
    },
    status: Mock.Random.pick(JobStatuses),
    progress: Math.round(progress * 100) / 100,
    targetCount,
    generatedCount,
    startTime: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    endTime: progress >= 100 ? Mock.Random.datetime("yyyy-MM-dd HH:mm:ss") : null,
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    statistics: {
      totalGenerated: generatedCount,
      successfulGenerated: Math.floor(generatedCount * Mock.Random.float(0.85, 0.98, 2, 2)),
      failedGenerated: Math.floor(generatedCount * Mock.Random.float(0.02, 0.15, 2, 2)),
      averageLength: Mock.Random.integer(50, 500),
      uniqueCount: Math.floor(generatedCount * Mock.Random.float(0.8, 0.95, 2, 2))
    },
    samples: new Array(Math.min(10, generatedCount)).fill(null).map(() => ({
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      content: Mock.Random.cparagraph(1, 3),
      score: Mock.Random.float(0.6, 1.0, 2, 2),
      metadata: {
        length: Mock.Random.integer(50, 500),
        model: template.modelConfig.modelName,
        timestamp: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss")
      },
      createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss")
    }))
  };
}

const synthesisJobList = new Array(30).fill(null).map(synthesisJobItem);

// 生成指令数据
function generatedInstructionItem() {
  return {
    instruction: Mock.Random.csentence(10, 30),
    input: Mock.Random.csentence(5, 20),
    output: Mock.Random.csentence(10, 40),
    quality: Mock.Random.float(0.7, 1.0, 2, 2)
  };
}

// COT 示例数据
function cotExampleItem() {
  return {
    question: Mock.Random.csentence(10, 25) + "？",
    reasoning: Mock.Random.cparagraph(2, 4),
    answer: Mock.Random.csentence(5, 15)
  };
}

// 蒸馏COT数据
function distilledCOTDataItem() {
  return {
    question: Mock.Random.csentence(10, 25) + "？",
    reasoning: Mock.Random.cparagraph(2, 4),
    answer: Mock.Random.csentence(5, 15),
    confidence: Mock.Random.float(0.7, 1.0, 2, 2)
  };
}

module.exports = function (router) {
  // 获取合成模板列表
  router.get(API.querySynthesisTemplatesUsingGet, (req, res) => {
    const { page = 0, size = 20, type } = req.query;
    let filteredTemplates = synthesisTemplateList;

    if (type) {
      filteredTemplates = synthesisTemplateList.filter(
        (template) => template.type === type
      );
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredTemplates.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredTemplates.length,
        totalPages: Math.ceil(filteredTemplates.length / size),
        size: parseInt(size),
        number: parseInt(page)
      }
    });
  });

  // 创建合成模板
  router.post(API.createSynthesisTemplateUsingPost, (req, res) => {
    const newTemplate = {
      ...synthesisTemplateItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      enabled: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    synthesisTemplateList.push(newTemplate);

    res.status(201).send({
      code: "0",
      msg: "Synthesis template created successfully",
      data: newTemplate
    });
  });

  // 获取合成模板详情
  router.get(API.querySynthesisTemplateByIdUsingGet, (req, res) => {
    const { templateId } = req.params;
    const template = synthesisTemplateList.find((t) => t.id === templateId);

    if (template) {
      res.send({
        code: "0",
        msg: "Success",
        data: template
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Synthesis template not found",
        data: null
      });
    }
  });

  // 更新合成模板
  router.put(API.updateSynthesisTemplateByIdUsingPut, (req, res) => {
    const { templateId } = req.params;
    const index = synthesisTemplateList.findIndex((t) => t.id === templateId);

    if (index !== -1) {
      synthesisTemplateList[index] = {
        ...synthesisTemplateList[index],
        ...req.body,
        updatedAt: new Date().toISOString()
      };
      res.send({
        code: "0",
        msg: "Synthesis template updated successfully",
        data: synthesisTemplateList[index]
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Synthesis template not found",
        data: null
      });
    }
  });

  // 删除合成模板
  router.delete(API.deleteSynthesisTemplateByIdUsingDelete, (req, res) => {
    const { templateId } = req.params;
    const index = synthesisTemplateList.findIndex((t) => t.id === templateId);

    if (index !== -1) {
      synthesisTemplateList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Synthesis template deleted successfully",
        data: null
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Synthesis template not found",
        data: null
      });
    }
  });

  // 获取合成任务列表
  router.get(API.querySynthesisJobsUsingGet, (req, res) => {
    const { page = 0, size = 20, status } = req.query;
    let filteredJobs = synthesisJobList;

    if (status) {
      filteredJobs = synthesisJobList.filter((job) => job.status === status);
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredJobs.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredJobs.length,
        totalPages: Math.ceil(filteredJobs.length / size),
        size: parseInt(size),
        number: parseInt(page)
      }
    });
  });

  // 创建合成任务
  router.post(API.createSynthesisJobUsingPost, (req, res) => {
    const { templateId } = req.body;
    const template = synthesisTemplateList.find(t => t.id === templateId);
    
    const newJob = {
      ...synthesisJobItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      templateId,
      template: template ? {
        id: template.id,
        name: template.name,
        type: template.type
      } : null,
      status: "PENDING",
      progress: 0,
      generatedCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    synthesisJobList.push(newJob);

    res.status(201).send({
      code: "0",
      msg: "Synthesis job created successfully",
      data: newJob
    });
  });

  // 获取合成任务详情
  router.get(API.querySynthesisJobByIdUsingGet, (req, res) => {
    const { jobId } = req.params;
    const job = synthesisJobList.find((j) => j.id === jobId);

    if (job) {
      const template = synthesisTemplateList.find(t => t.id === job.templateId);
      const jobDetail = {
        ...job,
        template: template || null
      };
      
      res.send({
        code: "0",
        msg: "Success",
        data: jobDetail
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Synthesis job not found",
        data: null
      });
    }
  });

  // 删除合成任务
  router.delete(API.deleteSynthesisJobByIdUsingDelete, (req, res) => {
    const { jobId } = req.params;
    const index = synthesisJobList.findIndex((j) => j.id === jobId);

    if (index !== -1) {
      synthesisJobList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Synthesis job deleted successfully",
        data: null
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Synthesis job not found",
        data: null
      });
    }
  });

  // 执行合成任务
  router.post(API.executeSynthesisJobUsingPost, (req, res) => {
    const { jobId } = req.params;
    const job = synthesisJobList.find((j) => j.id === jobId);

    if (job) {
      job.status = "RUNNING";
      job.startTime = new Date().toISOString();
      job.updatedAt = new Date().toISOString();

      // 模拟异步执行
      setTimeout(() => {
        job.status = Mock.Random.pick(["COMPLETED", "FAILED"]);
        job.progress = job.status === "COMPLETED" ? 100 : Mock.Random.float(10, 90, 2, 2);
        job.generatedCount = Math.floor((job.progress / 100) * job.targetCount);
        job.endTime = new Date().toISOString();
      }, Mock.Random.integer(2000, 5000));

      res.send({
        code: "0",
        msg: "Synthesis job execution started",
        data: {
          executionId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
          status: "RUNNING",
          message: "Job execution started successfully"
        }
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Synthesis job not found",
        data: null
      });
    }
  });

  // 指令调优数据合成
  router.post(API.instructionTuningUsingPost, (req, res) => {
    const { baseInstructions, targetDomain, count, modelConfig, parameters } = req.body;
    
    const jobId = Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, "");
    const generatedInstructions = new Array(count).fill(null).map(() => generatedInstructionItem());
    
    const statistics = {
      totalGenerated: count,
      averageQuality: Mock.Random.float(0.8, 0.95, 2, 2),
      diversityScore: Mock.Random.float(0.7, 0.9, 2, 2)
    };

    res.send({
      code: "0",
      msg: "Instruction tuning completed successfully",
      data: {
        jobId,
        generatedInstructions,
        statistics
      }
    });
  });

  // COT蒸馏数据合成
  router.post(API.cotDistillationUsingPost, (req, res) => {
    const { sourceModel, targetFormat, examples, parameters } = req.body;
    
    const jobId = Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, "");
    const processedCount = examples.length;
    const successfulCount = Math.floor(processedCount * Mock.Random.float(0.85, 0.98, 2, 2));
    
    const distilledData = new Array(successfulCount).fill(null).map(() => distilledCOTDataItem());
    
    const statistics = {
      totalProcessed: processedCount,
      successfulDistilled: successfulCount,
      averageConfidence: Mock.Random.float(0.8, 0.95, 2, 2)
    };

    res.send({
      code: "0",
      msg: "COT distillation completed successfully",
      data: {
        jobId,
        distilledData,
        statistics
      }
    });
  });

  // 获取合成任务统计信息
  router.get("/api/v1/synthesis/statistics", (req, res) => {
    const statistics = {
      totalJobs: synthesisJobList.length,
      completedJobs: synthesisJobList.filter(j => j.status === "COMPLETED").length,
      runningJobs: synthesisJobList.filter(j => j.status === "RUNNING").length,
      failedJobs: synthesisJobList.filter(j => j.status === "FAILED").length,
      totalGenerated: synthesisJobList.reduce((sum, job) => sum + job.generatedCount, 0),
      averageQuality: Mock.Random.float(0.8, 0.95, 2, 2),
      templateTypeDistribution: {
        "INSTRUCTION_TUNING": synthesisTemplateList.filter(t => t.type === "INSTRUCTION_TUNING").length,
        "COT_DISTILLATION": synthesisTemplateList.filter(t => t.type === "COT_DISTILLATION").length,
        "DIALOGUE_GENERATION": synthesisTemplateList.filter(t => t.type === "DIALOGUE_GENERATION").length,
        "TEXT_AUGMENTATION": synthesisTemplateList.filter(t => t.type === "TEXT_AUGMENTATION").length,
        "MULTIMODAL_SYNTHESIS": synthesisTemplateList.filter(t => t.type === "MULTIMODAL_SYNTHESIS").length,
        "CUSTOM": synthesisTemplateList.filter(t => t.type === "CUSTOM").length
      },
      dailyGeneration: new Array(7).fill(null).map((_, index) => ({
        date: Mock.Random.date("yyyy-MM-dd"),
        count: Mock.Random.integer(100, 5000)
      }))
    };

    res.send({
      code: "0",
      msg: "Success",
      data: statistics
    });
  });

  // 批量操作
  router.post("/api/v1/synthesis/jobs/batch", (req, res) => {
    const { action, jobIds } = req.body;
    
    let successCount = 0;
    let failedCount = 0;
    
    jobIds.forEach(jobId => {
      const job = synthesisJobList.find(j => j.id === jobId);
      if (job) {
        switch(action) {
          case "DELETE":
            const index = synthesisJobList.findIndex(j => j.id === jobId);
            synthesisJobList.splice(index, 1);
            successCount++;
            break;
          case "START":
            job.status = "RUNNING";
            job.startTime = new Date().toISOString();
            successCount++;
            break;
          case "STOP":
            job.status = "CANCELLED";
            job.endTime = new Date().toISOString();
            successCount++;
            break;
        }
      } else {
        failedCount++;
      }
    });

    res.send({
      code: "0",
      msg: `Batch ${action.toLowerCase()} completed`,
      data: {
        total: jobIds.length,
        success: successCount,
        failed: failedCount
      }
    });
  });
};