const Mock = require("mockjs");
const API = require("../mock-apis.cjs");
const { Random } = Mock;

// 生成模拟数据归集统计信息
function dataXTemplate() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 15),
    sourceType: Mock.Random.csentence(3, 10),
    targetType: Mock.Random.csentence(3, 10),
    description: Mock.Random.csentence(5, 20),
    version: `v${Mock.Random.integer(1, 5)}.${Mock.Random.integer(
      0,
      9
    )}.${Mock.Random.integer(0, 9)}`,
    isSystem: Mock.Random.boolean(),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const templateList = new Array(20).fill(null).map(dataXTemplate);

// 生成模拟任务数据
function taskItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 20),
    syncMode: Mock.Random.pick(["ONCE", "SCHEDULED"]),
    config: {
      query: "SELECT * FROM table WHERE condition",
      batchSize: Mock.Random.integer(100, 1000),
      frequency: Mock.Random.integer(1, 60), // in minutes
    },
    scheduleExpression: "0 0 * * *", // cron expression
    lastExecutionId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    status: Mock.Random.pick([
      "DRAFT",
      "READY",
      "RUNNING",
      "FAILED",
      "STOPPED",
      "SUCCESS",
    ]),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    sourceDataSourceId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    sourceDataSourceName: Mock.Random.ctitle(5, 20),
    targetDataSourceId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    targetDataSourceName: Mock.Random.ctitle(5, 20),
  };
}

const taskList = new Array(50).fill(null).map(taskItem);

// 生成模拟任务执行日志数据
function executionLogItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    taskName: Mock.Random.ctitle(5, 20),
    dataSource: Mock.Random.ctitle(5, 15),
    startTime: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    endTime: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    status: Mock.Random.pick(["SUCCESS", "FAILED", "RUNNING"]),
    triggerType: Mock.Random.pick(["MANUAL", "SCHEDULED", "API"]),
    duration: Mock.Random.integer(1, 120),
    retryCount: Mock.Random.integer(0, 5),
    recordsProcessed: Mock.Random.integer(100, 10000),
    processId: Mock.Random.integer(1000, 9999),
    errorMessage: Mock.Random.boolean() ? "" : Mock.Random.csentence(5, 20),
  };
}

const executionLogList = new Array(100).fill(null).map(executionLogItem);

module.exports = function (router) {
  // 获取任务列表
  router.get(API.queryTasksUsingGet, (req, res) => {
    const { keyword, status, page = 0, size = 10 } = req.query;
    let filteredTasks = taskList;
    if (keyword) {
      filteredTasks = filteredTasks.filter((task) =>
        task.name.includes(keyword)
      );
    }
    if (status && status.length > 0) {
      filteredTasks = filteredTasks.filter((task) =>
        status.includes(task.status)
      );
    }
    const startIndex = page * size;
    const endIndex = startIndex + size;
    const paginatedTasks = filteredTasks.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements: filteredTasks.length,
        page,
        size,
        content: paginatedTasks,
      },
    });
  });

  router.get(API.queryDataXTemplatesUsingGet, (req, res) => {
    const { keyword, page = 0, size = 10 } = req.query;
    let filteredTemplates = templateList;
    if (keyword) {
      filteredTemplates = filteredTemplates.filter((template) =>
        template.name.includes(keyword)
      );
    }
    const startIndex = page * size;
    const endIndex = startIndex + size;
    const paginatedTemplates = filteredTemplates.slice(startIndex, endIndex);
    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: paginatedTemplates,
        totalElements: filteredTemplates.length,
        page,
        size,
      },
    });
  });

  // 创建任务
  router.post(API.createTaskUsingPost, (req, res) => {
    taskList.unshift(taskItem()); // 添加一个新的任务到列表开头
    res.send({
      code: "0",
      msg: "任务创建成功",
      data: {
        id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      },
    });
  });

  // 更新任务
  router.post(API.updateTaskByIdUsingPut, (req, res) => {
    const { id } = req.body;
    res.send({
      code: "0",
      msg: "Data source task updated successfully",
      data: taskList.find((task) => task.id === id),
    });
  });

  // 删除任务
  router.post(API.deleteTaskByIdUsingDelete, (req, res) => {
    const { id } = req.body;
    const index = taskList.findIndex((task) => task.id === id);
    if (index !== -1) {
      taskList.splice(index, 1);
    }
    res.send({
      code: "0",
      msg: "Data source task deleted successfully",
      data: null,
    });
  });

  // 执行任务
  router.post(API.executeTaskByIdUsingPost, (req, res) => {
    console.log("Received request to execute task", req.body);
    const { id } = req.body;
    console.log("Executing task with ID:", id);
    taskList.find((task) => task.id === id).status = "RUNNING";
    res.send({
      code: "0",
      msg: "Data source task execution started",
      data: null,
    });
  });

  // 停止任务
  router.post(API.stopTaskByIdUsingPost, (req, res) => {
    const { id } = req.body;
    const task = taskList.find((task) => task.id === id);
    if (task) {
      task.status = "STOPPED";
    }
    res.send({
      code: "0",
      msg: "Data source task stopped successfully",
      data: null,
    });
  });

  // 获取任务执行日志
  router.post(API.queryExecutionLogUsingPost, (req, res) => {
    const { keyword, page = 1, size = 10, status } = req.body;
    let filteredLogs = executionLogList;
    if (keyword) {
      filteredLogs = filteredLogs.filter((log) =>
        log.taskName.includes(keyword)
      );
    }
    if (status && status.length > 0) {
      filteredLogs = filteredLogs.filter((log) => status.includes(log.status));
    }
    const startIndex = (page - 1) * size;
    const endIndex = startIndex + size;
    const paginatedLogs = filteredLogs.slice(startIndex, endIndex);
    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements: filteredLogs.length,
        page,
        size,
        results: paginatedLogs,
      },
    });
  });

  // 获取任务执行日志详情
  router.post(API.queryExecutionLogByIdUsingGet, (req, res) => {
    const { id } = req.body;
    const log = executionLogList.find((log) => log.id === id);
    res.send({
      code: "0",
      msg: "Success",
      data: log,
    });
  });
};
