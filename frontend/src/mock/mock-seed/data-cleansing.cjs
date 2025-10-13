const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

function operatorItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(3, 10),
    description: Mock.Random.csentence(5, 20),
    version: "1.0.0",
    inputs: Mock.Random.integer(1, 5),
    outputs: Mock.Random.integer(1, 5),
    runtime: Mock.Random.pick(["Python", "Java", "Scala"]),
    settings: {
      host: { type: "input", label: "主机地址", value: "localhost" },
      port: { type: "input", label: "端口", value: "3306" },
      database: { type: "input", label: "数据库名", value: "" },
      table: { type: "input", label: "表名", value: "" },
      limit: {
        type: "range",
        label: "读取行数",
        value: [1000],
        min: 100,
        max: 10000,
        step: 100,
      },
      filepath: { type: "input", label: "文件路径", value: "" },
      encoding: {
        type: "select",
        label: "编码",
        value: "utf-8",
        options: ["utf-8", "gbk", "ascii"],
      },
      features: {
        type: "checkbox",
        label: "特征列",
        value: [],
        options: ["feature1", "feature2", "feature3"],
      },
    },
    isStar: Mock.Random.boolean(),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const operatorList = new Array(10).fill(null).map(operatorItem);

// 清洗任务数据
function cleaningTaskItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 30),
    status: Mock.Random.pick(["pending", "running", "completed", "failed"]),
    srcDatasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    srcDatasetName: Mock.Random.ctitle(5, 15),
    destDatasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    destDatasetName: Mock.Random.ctitle(5, 15),
    progress: Mock.Random.float(0, 100, 2, 2),
    startedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    endedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    instance: operatorList,
  };
}

const cleaningTaskList = new Array(20).fill(null).map(cleaningTaskItem);

// 清洗模板数据
function cleaningTemplateItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 15),
    description: Mock.Random.csentence(5, 25),
    instance: operatorList,
    category: Mock.Random.ctitle(3, 8),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const cleaningTemplateList = new Array(15).fill(null).map(cleaningTemplateItem);

module.exports = function (router) {
  // 获取清洗任务列表
  router.get(API.queryCleaningTasksUsingGet, (req, res) => {
    const { page = 0, size = 10, status } = req.query;
    let filteredTasks = cleaningTaskList;
    console.log(req.query);

    if (status) {
      filteredTasks = cleaningTaskList.filter((task) => task.status === status);
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredTasks.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredTasks.length,
        totalPages: Math.ceil(filteredTasks.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 创建清洗任务
  router.post(API.createCleaningTaskUsingPost, (req, res) => {
    const newTask = {
      ...cleaningTaskItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      status: "PENDING",
      createdAt: new Date().toISOString(),
    };
    cleaningTaskList.push(newTask);

    res.status(201).send({
      code: "0",
      msg: "Cleaning task created successfully",
      data: newTask,
    });
  });

  // 获取清洗任务详情
  router.get(API.queryCleaningTaskByIdUsingGet, (req, res) => {
    const { taskId } = req.params;
    const task = cleaningTaskList.find((j) => j.id === taskId);

    if (task) {
      res.send({
        code: "0",
        msg: "Success",
        data: task,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning task not found",
        data: null,
      });
    }
  });

  // 删除清洗任务
  router.delete(API.deleteCleaningTaskByIdUsingDelete, (req, res) => {
    const { taskId } = req.params;
    const index = cleaningTaskList.findIndex((j) => j.id === taskId);

    if (index !== -1) {
      cleaningTaskList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Cleaning task deleted successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning task not found",
        data: null,
      });
    }
  });

  // 执行清洗任务
  router.post(API.executeCleaningTaskUsingPost, (req, res) => {
    const { taskId } = req.params;
    const task = cleaningTaskList.find((j) => j.id === taskId);

    if (task) {
      task.status = "running";
      task.startTime = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Cleaning task execution started",
        data: {
          executionId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
          status: "running",
          message: "Task execution started successfully",
        },
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning task not found",
        data: null,
      });
    }
  });

  // 停止清洗任务
  router.post(API.stopCleaningTaskUsingPost, (req, res) => {
    const { taskId } = req.params;
    const task = cleaningTaskList.find((j) => j.id === taskId);

    if (task) {
      task.status = "pending";
      task.endTime = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Cleaning task stopped successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Cleaning task not found",
        data: null,
      });
    }
  });

  // 获取清洗模板列表
  router.get(API.queryCleaningTemplatesUsingGet, (req, res) => {
    const { page = 0, size = 20 } = req.query;
    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = cleaningTemplateList.slice(startIndex, endIndex);
    res.send({
      code: "0",
      msg: "Success",
      data: { content: pageData, totalElements: cleaningTemplateList.length },
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
