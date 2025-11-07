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
    settings: JSON.stringify({
      host: { type: "input", name: "主机地址", defaultVal: "localhost" },
      fileLength: {
        name: "文档字数",
        description:
          "过滤字数不在指定范围内的文档，如[10,10000000]。若输入为空，则不对字数上/下限做限制。",
        type: "range",
        defaultVal: [10, 10000000],
        min: 0,
        max: 10000000000000000,
        step: 1,
      },
      range: {
        type: "range",
        name: "读取行数",
        description: "某个词的统计数/文档总词数 > 设定值，该文档被去除。",
        properties: [
          {
            name: "起始行",
            type: "inputNumber",
            defaultVal: 1000,
            min: 100,
            max: 10000,
            step: 1,
          },
          {
            name: "结束行",
            type: "inputNumber",
            defaultVal: 2000,
            min: 100,
            max: 10000,
            step: 1,
          },
        ],
      },
      filepath: { type: "input", name: "文件路径", defaultVal: "/path" },
      encoding: {
        type: "select",
        name: "编码",
        defaultVal: "utf-8",
        options: ["utf-8", "gbk", "ascii"],
      },
      radio: {
        type: "radio",
        name: "radio",
        defaultVal: "utf-8",
        options: ["utf-8", "gbk", "ascii"],
      },
      features: {
        type: "checkbox",
        name: "特征列",
        defaultVal: ["feature1", "feature3"],
        options: ["feature1", "feature2", "feature3"],
      },
      repeatPhraseRatio: {
        name: "文档词重复率",
        description: "某个词的统计数/文档总词数 > 设定值，该文档被去除。",
        type: "slider",
        defaultVal: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
      },
      hitStopwords: {
        name: "去除停用词",
        description: "统计重复词时，选择是否要去除停用词。",
        type: "switch",
        defaultVal: false,
        required: true,
        checkedLabel: "去除",
        unCheckedLabel: "不去除",
      },
    }),
    categories: [Mock.Random.pick([3, 4, 5, 6, 7, 8, 9])],
    isStar: Mock.Random.boolean(),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const operatorList = new Array(50).fill(null).map(operatorItem);

// 清洗任务数据
function cleaningTaskItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    description: Mock.Random.csentence(5, 30),
    status: Mock.Random.pick([
      "PENDING",
      "RUNNING",
      "COMPLETED",
      "FAILED",
      "STOPPED",
    ]),
    srcDatasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    srcDatasetName: Mock.Random.ctitle(5, 15),
    destDatasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    destDatasetName: Mock.Random.ctitle(5, 15),
    progress: {
      finishedFileNum: Mock.Random.integer(0, 100),
      process: Mock.Random.integer(0, 100),
      totalFileNum: 100,
    },
    startedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    finishedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
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
    instance: operatorList.slice(
      Mock.Random.integer(0, 5),
      Mock.Random.integer(6, 50)
    ),
    category: Mock.Random.ctitle(3, 8),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const cleaningTemplateList = new Array(15).fill(null).map(cleaningTemplateItem);

const categoryTree = [
  {
    id: 1,
    name: "modal",
    count: 7,
    categories: [
      { id: 3, name: "text", count: 3, type: null, parentId: null },
      { id: 4, name: "image", count: 0, type: null, parentId: null },
      { id: 5, name: "audio", count: 0, type: null, parentId: null },
      { id: 6, name: "video", count: 0, type: null, parentId: null },
      {
        id: 7,
        name: "multimodal",
        count: 0,
        type: null,
        parentId: null,
      },
    ],
  },
  {
    id: 2,
    name: "language",
    count: 3,
    categories: [
      { id: 8, name: "python", count: 2, type: null, parentId: null },
      { id: 9, name: "java", count: 1, type: null, parentId: null },
    ],
  },
];

module.exports = function (router) {
  // 获取清洗任务列表
  router.get(API.queryCleaningTasksUsingGet, (req, res) => {
    const { page = 0, size = 10, status } = req.query;
    let filteredTasks = cleaningTaskList;

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
      task.status = "RUNNING";
      task.startTime = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Cleaning task execution started",
        data: {
          executionId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
          status: "RUNNING",
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
      task.status = "PENDING";
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

  // 获取算子列表
  router.post(API.queryOperatorsUsingPost, (req, res) => {
    const {
      page = 0,
      size = 20,
      categories = [],
      operatorName = "",
      labelName = "",
      isStar,
    } = req.body;

    let filteredOperators = operatorList;

    // 按分类筛选
    if (categories && categories.length > 0) {
      filteredOperators = filteredOperators.filter((op) =>
        categories.includes(op.category.id)
      );
    }

    // 按名称搜索
    if (operatorName) {
      filteredOperators = filteredOperators.filter((op) =>
        op.name.toLowerCase().includes(operatorName.toLowerCase())
      );
    }

    // 按标签筛选
    if (labelName) {
      filteredOperators = filteredOperators.filter((op) =>
        op.labels.some((label) => label.name.includes(labelName))
      );
    }

    // 按收藏状态筛选
    if (typeof isStar === "boolean") {
      filteredOperators = filteredOperators.filter(
        (op) => op.isStar === isStar
      );
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredOperators.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredOperators.length,
        totalPages: Math.ceil(filteredOperators.length / size),
        size: parseInt(size),
        number: parseInt(page),
        first: page === 0,
        last: page >= Math.ceil(filteredOperators.length / size) - 1,
      },
    });
  });

  // 获取算子详情
  router.get(API.queryOperatorByIdUsingGet, (req, res) => {
    const { id } = req.params;
    const operator = operatorList.find((op) => op.id === id);
    console.log("获取算子详情：", id, operator);

    if (operator) {
      // 增加浏览次数模拟
      operator.viewCount = (operator.viewCount || 0) + 1;

      res.send({
        code: "0",
        msg: "Success",
        data: operator,
      });
    } else {
      res.status(404).send({
        error: "OPERATOR_NOT_FOUND",
        message: "算子不存在",
        timestamp: new Date().toISOString(),
      });
    }
  });

  // 更新算子信息
  router.put(API.updateOperatorByIdUsingPut, (req, res) => {
    const { id } = req.params;
    const index = operatorList.findIndex((op) => op.id === id);

    if (index !== -1) {
      operatorList[index] = {
        ...operatorList[index],
        ...req.body,
        updatedAt: new Date().toISOString(),
      };

      res.send({
        code: "0",
        msg: "Operator updated successfully",
        data: operatorList[index],
      });
    } else {
      res.status(404).send({
        error: "OPERATOR_NOT_FOUND",
        message: "算子不存在",
        timestamp: new Date().toISOString(),
      });
    }
  });

  // 创建算子
  router.post(API.createOperatorUsingPost, (req, res) => {
    const { name, description, version, category, documentation } = req.body;

    const newOperator = {
      ...operatorItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      name,
      description,
      version,
      category:
        typeof category === "string"
          ? { id: category, name: category }
          : category,
      documentation,
      status: "REVIEWING",
      downloadCount: 0,
      rating: 0,
      ratingCount: 0,
      isStar: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    operatorList.push(newOperator);

    res.status(201).send({
      code: "0",
      msg: "Operator created successfully",
      data: newOperator,
    });
  });

  // 上传算子
  router.post(API.uploadOperatorUsingPost, (req, res) => {
    const { description } = req.body;

    const newOperator = {
      ...operatorItem(),
      description: description || "通过文件上传创建的算子",
      status: "REVIEWING",
      downloadCount: 0,
      rating: 0,
      ratingCount: 0,
      isStar: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    operatorList.push(newOperator);

    res.status(201).send({
      code: "0",
      msg: "Operator uploaded successfully",
      data: newOperator,
    });
  });

  // 获取算子分类树
  router.get(API.queryCategoryTreeUsingGet, (req, res) => {
    res.send({
      code: "0",
      msg: "Success",
      data: {
        page: 0,
        size: categoryTree.length,
        totalElements: categoryTree.length,
        totalPages: 1,
        content: categoryTree,
      },
    });
  });
};
