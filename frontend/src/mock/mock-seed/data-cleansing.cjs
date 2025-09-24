const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 清洗规则数据
function cleaningRuleItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 30),
    category: Mock.Random.pick([
      "DATA_VALIDATION",
      "MISSING_VALUE_HANDLING",
      "OUTLIER_DETECTION",
      "DEDUPLICATION",
      "FORMAT_STANDARDIZATION",
      "TEXT_CLEANING",
      "CUSTOM",
    ]),
    ruleType: Mock.Random.pick(["FILTER", "TRANSFORM", "VALIDATE", "ENRICH"]),
    priority: Mock.Random.integer(1, 10),
    enabled: Mock.Random.boolean(),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const cleaningRuleList = new Array(30).fill(null).map(cleaningRuleItem);

// 清洗任务数据
function cleaningJobItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 30),
    status: Mock.Random.pick([
      "PENDING",
      "RUNNING",
      "COMPLETED",
      "FAILED",
      "CANCELLED",
    ]),
    dataset: {
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      name: Mock.Random.ctitle(3, 8),
    },
    progress: Mock.Random.float(0, 100, 2, 2),
    startTime: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    endTime: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    rules: [cleaningRuleList[0], cleaningRuleList[1]],
    statistics: {
      totalRecords: Mock.Random.integer(1000, 100000),
      processedRecords: Mock.Random.integer(500, 50000),
      validRecords: Mock.Random.integer(400, 40000),
      invalidRecords: Mock.Random.integer(10, 1000),
      modifiedRecords: Mock.Random.integer(50, 5000),
    },
    logs: [
      {
        timestamp: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
        level: Mock.Random.pick(["INFO", "WARN", "ERROR"]),
        message: Mock.Random.csentence(10, 30),
      },
    ],
  };
}

const cleaningJobList = new Array(20).fill(null).map(cleaningJobItem);

// 清洗模板数据
function cleaningTemplateItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 15),
    description: Mock.Random.csentence(5, 25),
    category: Mock.Random.ctitle(3, 8),
    usage: Mock.Random.integer(1, 100),
    rules: [cleaningRuleList[0], cleaningRuleList[1], cleaningRuleList[2]],
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const cleaningTemplateList = new Array(15).fill(null).map(cleaningTemplateItem);

module.exports = function (router) {
  // 获取清洗规则列表
  router.get(API.queryCleaningRulesUsingGet, (req, res) => {
    const { page = 0, size = 20, category } = req.query;
    let filteredRules = cleaningRuleList;

    if (category) {
      filteredRules = cleaningRuleList.filter(
        (rule) => rule.category === category
      );
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredRules.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredRules.length,
        totalPages: Math.ceil(filteredRules.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 创建清洗规则
  router.post(API.createCleaningRuleUsingPost, (req, res) => {
    const newRule = {
      ...cleaningRuleItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      createdAt: new Date().toISOString(),
    };
    cleaningRuleList.push(newRule);

    res.status(201).send({
      code: "0",
      msg: "Cleaning rule created successfully",
      data: newRule,
    });
  });

  // 获取清洗规则详情
  router.get(API.queryCleaningRuleByIdUsingGet, (req, res) => {
    const { ruleId } = req.params;
    const rule = cleaningRuleList.find((r) => r.id === ruleId);

    if (rule) {
      res.send({
        code: "0",
        msg: "Success",
        data: rule,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning rule not found",
        data: null,
      });
    }
  });

  // 更新清洗规则
  router.put(API.updateCleaningRuleByIdUsingPut, (req, res) => {
    const { ruleId } = req.params;
    const index = cleaningRuleList.findIndex((r) => r.id === ruleId);

    if (index !== -1) {
      cleaningRuleList[index] = {
        ...cleaningRuleList[index],
        ...req.body,
        updatedAt: new Date().toISOString(),
      };
      res.send({
        code: "0",
        msg: "Cleaning rule updated successfully",
        data: cleaningRuleList[index],
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning rule not found",
        data: null,
      });
    }
  });

  // 删除清洗规则
  router.delete(API.deleteCleaningRuleByIdUsingDelete, (req, res) => {
    const { ruleId } = req.params;
    const index = cleaningRuleList.findIndex((r) => r.id === ruleId);

    if (index !== -1) {
      cleaningRuleList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Cleaning rule deleted successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning rule not found",
        data: null,
      });
    }
  });

  // 获取清洗任务列表
  router.post(API.queryCleaningJobsUsingPost, (req, res) => {
    const { page = 1, size = 10, status, type } = req.body;
    let filteredJobs = cleaningJobList;

    if (status) {
      filteredJobs = cleaningJobList.filter((job) => job.status === status);
    }

    const startIndex = (page - 1) * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredJobs.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        results: pageData,
        totalElements: filteredJobs.length,
        totalPages: Math.ceil(filteredJobs.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 创建清洗任务
  router.post(API.createCleaningJobUsingPost, (req, res) => {
    const newJob = {
      ...cleaningJobItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      status: "PENDING",
      createdAt: new Date().toISOString(),
    };
    cleaningJobList.push(newJob);

    res.status(201).send({
      code: "0",
      msg: "Cleaning job created successfully",
      data: newJob,
    });
  });

  // 获取清洗任务详情
  router.get(API.queryCleaningJobByIdUsingGet, (req, res) => {
    const { jobId } = req.params;
    const job = cleaningJobList.find((j) => j.id === jobId);

    if (job) {
      res.send({
        code: "0",
        msg: "Success",
        data: job,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning job not found",
        data: null,
      });
    }
  });

  // 删除清洗任务
  router.delete(API.deleteCleaningJobByIdUsingDelete, (req, res) => {
    const { jobId } = req.params;
    const index = cleaningJobList.findIndex((j) => j.id === jobId);

    if (index !== -1) {
      cleaningJobList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Cleaning job deleted successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning job not found",
        data: null,
      });
    }
  });

  // 执行清洗任务
  router.post(API.executeCleaningJobUsingPost, (req, res) => {
    const { jobId } = req.params;
    const job = cleaningJobList.find((j) => j.id === jobId);

    if (job) {
      job.status = "RUNNING";
      job.startTime = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Cleaning job execution started",
        data: {
          executionId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
          status: "RUNNING",
          message: "Job execution started successfully",
        },
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning job not found",
        data: null,
      });
    }
  });

  // 停止清洗任务
  router.post(API.stopCleaningJobUsingPost, (req, res) => {
    const { jobId } = req.params;
    const job = cleaningJobList.find((j) => j.id === jobId);

    if (job) {
      job.status = "CANCELLED";
      job.endTime = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Cleaning job stopped successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning job not found",
        data: null,
      });
    }
  });

  // 获取清洗模板列表
  router.post(API.queryCleaningTemplatesUsingPost, (req, res) => {
    const { page = 0, size = 20 } = req.body;
    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = cleaningTemplateList.slice(startIndex, endIndex);
    res.send({
      code: "0",
      msg: "Success",
      data: { results: pageData, totalElements: cleaningTemplateList.length },
    });
  });

  // 创建清洗模板
  router.post(API.createCleaningTemplateUsingPost, (req, res) => {
    const newTemplate = {
      ...cleaningTemplateItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      createdAt: new Date().toISOString(),
    };
    cleaningTemplateList.push(newTemplate);

    res.status(201).send({
      code: "0",
      msg: "Cleaning template created successfully",
      data: newTemplate,
    });
  });

  // 获取清洗模板详情
  router.get(API.queryCleaningTemplateByIdUsingGet, (req, res) => {
    const { templateId } = req.params;
    const template = cleaningTemplateList.find((t) => t.id === templateId);

    if (template) {
      res.send({
        code: "0",
        msg: "Success",
        data: template,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning template not found",
        data: null,
      });
    }
  });

  // 删除清洗模板
  router.delete(API.deleteCleaningTemplateByIdUsingDelete, (req, res) => {
    const { templateId } = req.params;
    const index = cleaningTemplateList.findIndex((t) => t.id === templateId);

    if (index !== -1) {
      cleaningTemplateList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Cleaning template deleted successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning template not found",
        data: null,
      });
    }
  });
};
