const Mock = require("mockjs");
const API = require("../mock-apis.cjs");
const { Random } = Mock;

// 生成模拟数据归集统计信息
const collectionStatistics = {
  period: Random.pick(["HOUR", "DAY", "WEEK", "MONTH"]),
  totalTasks: Random.integer(50, 200),
  activeTasks: Random.integer(10, 50),
  successfulExecutions: Random.integer(30, 150),
  failedExecutions: Random.integer(0, 50),
  totalExecutions: Random.integer(20, 100),
  avgExecutionTime: Random.integer(1000, 10000), // in milliseconds
  avgThroughput: Random.integer(100, 1000), // records per second
  topDataSources: new Array(5).fill(null).map(() => ({
    dataSourceId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    dataSourceName: Mock.Random.word(5, 15),
    type: Mock.Random.pick([
      "MySQL",
      "PostgreSQL",
      "ORACLE",
      "SQLSERVER",
      "MONGODB",
      "REDIS",
      "ELASTICSEARCH",
      "HIVE",
      "HDFS",
      "KAFKA",
      "HTTP",
      "FILE",
    ]),
    taskCount: Mock.Random.integer(1, 20),
    executionCount: Mock.Random.integer(1, 50),
    recordsProcessed: Mock.Random.integer(70, 100), // percentage
  })),
};

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
  // 获取数据统计信息
  router.get(API.queryCollectionStatisticsUsingGet, (req, res) => {
    res.send({
      code: "0",
      msg: "Success",
      data: collectionStatistics,
    });
  });

  // 获取任务列表
  router.post(API.queryTasksUsingPost, (req, res) => {
    const { searchTerm, filters, page = 1, size = 10 } = req.body;
    let filteredTasks = taskList;
    if (searchTerm) {
      filteredTasks = filteredTasks.filter((task) =>
        task.name.includes(searchTerm)
      );
    }
    if (filters && filters.status && filters.status.length > 0) {
      filteredTasks = filteredTasks.filter((task) =>
        filters.status.includes(task.status)
      );
    }
    const startIndex = (page - 1) * size;
    const endIndex = startIndex + size;
    const paginatedTasks = filteredTasks.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements: filteredTasks.length,
        page,
        size,
        results: paginatedTasks,
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
