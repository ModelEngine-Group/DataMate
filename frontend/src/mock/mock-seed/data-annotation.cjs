const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 标注任务数据
function annotationTaskItem() {
  return {
    source_dataset_id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    mapping_id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    labelling_project_id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    labelling_project_name: Mock.Random.ctitle(5, 20),
    created_at: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    last_updated_at: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    deleted_at: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    // id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    // name: Mock.Random.ctitle(5, 20),
    // description: Mock.Random.csentence(5, 30),
    // type: Mock.Random.pick([
    //   "TEXT_CLASSIFICATION",
    //   "NAMED_ENTITY_RECOGNITION",
    //   "OBJECT_DETECTION",
    //   "SEMANTIC_SEGMENTATION",
    // ]),
    // status: Mock.Random.pick(["PENDING", "IN_PROGRESS", "COMPLETED", "PAUSED"]),
    // datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    // progress: Mock.Random.float(0, 100, 2, 2),
    // createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    // updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    // createdBy: Mock.Random.cname(),
    // assignedTo: Mock.Random.cname(),
    // totalDataCount: Mock.Random.integer(100, 10000),
    // annotatedCount: Mock.Random.integer(10, 500),
    // configuration: {
    //   labels: Mock.Random.shuffle([
    //     "正面",
    //     "负面",
    //     "中性",
    //     "人物",
    //     "地点",
    //     "组织",
    //     "时间",
    //   ]).slice(0, Mock.Random.integer(3, 5)),
    //   guidelines: Mock.Random.csentence(10, 50),
    //   qualityThreshold: Mock.Random.float(0.8, 1.0, 2, 2),
    // },
    // statistics: {
    //   accuracy: Mock.Random.float(0.85, 0.99, 2, 2),
    //   averageTime: Mock.Random.integer(30, 300), // seconds
    //   reviewCount: Mock.Random.integer(0, 50),
    // },
  };
}

const annotationTaskList = new Array(25).fill(null).map(annotationTaskItem);

// 标注数据项
function annotationDataItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    taskId: Mock.Random.pick(annotationTaskList).id,
    content: Mock.Random.cparagraph(1, 3),
    originalData: {
      text: Mock.Random.cparagraph(1, 3),
      source: Mock.Random.url(),
      metadata: {
        author: Mock.Random.cname(),
        timestamp: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
      },
    },
    annotations: [
      {
        id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
        label: Mock.Random.pick(["正面", "负面", "中性"]),
        confidence: Mock.Random.float(0.7, 1.0, 2, 2),
        annotator: Mock.Random.cname(),
        createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
        isPreAnnotation: Mock.Random.boolean(),
      },
    ],
    status: Mock.Random.pick(["PENDING", "ANNOTATED", "REVIEWED", "REJECTED"]),
    priority: Mock.Random.integer(1, 5),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const annotationDataList = new Array(200).fill(null).map(annotationDataItem);

// 标注模板数据
function annotationTemplateItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 15),
    description: Mock.Random.csentence(5, 25),
    type: Mock.Random.pick([
      "TEXT_CLASSIFICATION",
      "NAMED_ENTITY_RECOGNITION",
      "OBJECT_DETECTION",
      "SEMANTIC_SEGMENTATION",
    ]),
    category: Mock.Random.ctitle(3, 8),
    labels: Mock.Random.shuffle([
      "正面",
      "负面",
      "中性",
      "人物",
      "地点",
      "组织",
      "时间",
      "产品",
      "服务",
    ]).slice(0, Mock.Random.integer(3, 6)),
    guidelines: Mock.Random.csentence(10, 50),
    usageCount: Mock.Random.integer(0, 100),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    createdBy: Mock.Random.cname(),
  };
}

const annotationTemplateList = new Array(15)
  .fill(null)
  .map(annotationTemplateItem);

// 标注者数据
function annotatorItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.cname(),
    email: Mock.Random.email(),
    role: Mock.Random.pick(["ANNOTATOR", "REVIEWER", "ADMIN"]),
    skillLevel: Mock.Random.pick(["BEGINNER", "INTERMEDIATE", "EXPERT"]),
    specialties: Mock.Random.shuffle([
      "文本分类",
      "命名实体识别",
      "目标检测",
      "语义分割",
    ]).slice(0, Mock.Random.integer(1, 3)),
    statistics: {
      totalAnnotations: Mock.Random.integer(100, 5000),
      accuracy: Mock.Random.float(0.85, 0.99, 2, 2),
      averageSpeed: Mock.Random.integer(50, 200), // annotations per hour
      totalWorkTime: Mock.Random.integer(10, 500), // hours
    },
    status: Mock.Random.pick(["ACTIVE", "INACTIVE", "SUSPENDED"]),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const annotatorList = new Array(20).fill(null).map(annotatorItem);

module.exports = function (router) {
  // 获取标注任务列表
  router.get(API.queryAnnotationTasksUsingGet, (req, res) => {
    const { page = 0, size = 20, status, type } = req.query;
    let filteredTasks = annotationTaskList;

    if (status) {
      filteredTasks = filteredTasks.filter((task) => task.status === status);
    }

    if (type) {
      filteredTasks = filteredTasks.filter((task) => task.type === type);
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
        first: page == 0,
        last: page >= Math.ceil(filteredTasks.length / size) - 1,
      },
    });
  });

  // 创建标注任务
  router.post(API.createAnnotationTaskUsingPost, (req, res) => {
    const newTask = {
      ...annotationTaskItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      status: "PENDING",
      progress: 0,
      annotatedCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    annotationTaskList.push(newTask);

    res.status(201).send({
      code: "0",
      msg: "Annotation task created successfully",
      data: newTask,
    });
  });

  // 获取标注任务详情
  router.get(API.queryAnnotationTaskByIdUsingGet, (req, res) => {
    const { taskId } = req.params;
    const task = annotationTaskList.find((t) => t.id === taskId);

    if (task) {
      res.send({
        code: "0",
        msg: "Success",
        data: task,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 更新标注任务
  router.put(API.syncAnnotationTaskByIdUsingPost, (req, res) => {
    const { taskId } = req.params;
    const index = annotationTaskList.findIndex((t) => t.id === taskId);

    if (index !== -1) {
      annotationTaskList[index] = {
        ...annotationTaskList[index],
        ...req.body,
        updatedAt: new Date().toISOString(),
      };
      res.send({
        code: "0",
        msg: "Annotation task updated successfully",
        data: annotationTaskList[index],
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 删除标注任务
  router.delete(API.deleteAnnotationTaskByIdUsingDelete, (req, res) => {
    const { taskId } = req.params;
    const index = annotationTaskList.findIndex((t) => t.id === taskId);

    if (index !== -1) {
      annotationTaskList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Annotation task deleted successfully",
        data: null,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 获取标注数据列表
  router.get(API.queryAnnotationDataUsingGet, (req, res) => {
    const { taskId } = req.params;
    const { page = 0, size = 20, status } = req.query;

    let filteredData = annotationDataList.filter(
      (data) => data.taskId === taskId
    );

    if (status) {
      filteredData = filteredData.filter((data) => data.status === status);
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredData.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredData.length,
        totalPages: Math.ceil(filteredData.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 提交标注
  router.post(API.submitAnnotationUsingPost, (req, res) => {
    const { taskId } = req.params;
    const newAnnotation = {
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      taskId,
      ...req.body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    res.status(201).send({
      code: "0",
      msg: "Annotation submitted successfully",
      data: newAnnotation,
    });
  });

  // 更新标注
  router.put(API.updateAnnotationUsingPut, (req, res) => {
    const { taskId, annotationId } = req.params;

    res.send({
      code: "0",
      msg: "Annotation updated successfully",
      data: {
        id: annotationId,
        taskId,
        ...req.body,
        updatedAt: new Date().toISOString(),
      },
    });
  });

  // 删除标注
  router.delete(API.deleteAnnotationUsingDelete, (req, res) => {
    const { taskId, annotationId } = req.params;

    res.send({
      code: "0",
      msg: "Annotation deleted successfully",
      data: null,
    });
  });

  // 开始标注任务
  router.post(API.startAnnotationTaskUsingPost, (req, res) => {
    const { taskId } = req.params;
    const task = annotationTaskList.find((t) => t.id === taskId);

    if (task) {
      task.status = "IN_PROGRESS";
      task.updatedAt = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Annotation task started successfully",
        data: task,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 暂停标注任务
  router.post(API.pauseAnnotationTaskUsingPost, (req, res) => {
    const { taskId } = req.params;
    const task = annotationTaskList.find((t) => t.id === taskId);

    if (task) {
      task.status = "PAUSED";
      task.updatedAt = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Annotation task paused successfully",
        data: task,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 恢复标注任务
  router.post(API.resumeAnnotationTaskUsingPost, (req, res) => {
    const { taskId } = req.params;
    const task = annotationTaskList.find((t) => t.id === taskId);

    if (task) {
      task.status = "IN_PROGRESS";
      task.updatedAt = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Annotation task resumed successfully",
        data: task,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 完成标注任务
  router.post(API.completeAnnotationTaskUsingPost, (req, res) => {
    const { taskId } = req.params;
    const task = annotationTaskList.find((t) => t.id === taskId);

    if (task) {
      task.status = "COMPLETED";
      task.progress = 100;
      task.updatedAt = new Date().toISOString();

      res.send({
        code: "0",
        msg: "Annotation task completed successfully",
        data: task,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 获取标注任务统计信息
  router.get(API.getAnnotationTaskStatisticsUsingGet, (req, res) => {
    const { taskId } = req.params;
    const task = annotationTaskList.find((t) => t.id === taskId);

    if (task) {
      const statistics = {
        taskId,
        totalDataCount: task.totalDataCount,
        annotatedCount: task.annotatedCount,
        progress: task.progress,
        accuracy: task.statistics.accuracy,
        averageAnnotationTime: task.statistics.averageTime,
        reviewCount: task.statistics.reviewCount,
        qualityScore: Mock.Random.float(0.8, 0.99, 2, 2),
        annotatorDistribution: {
          [Mock.Random.cname()]: Mock.Random.integer(10, 100),
          [Mock.Random.cname()]: Mock.Random.integer(10, 100),
          [Mock.Random.cname()]: Mock.Random.integer(10, 100),
        },
      };

      res.send({
        code: "0",
        msg: "Success",
        data: statistics,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation task not found",
        data: null,
      });
    }
  });

  // 获取整体标注统计信息
  router.get(API.getAnnotationStatisticsUsingGet, (req, res) => {
    const statistics = {
      totalTasks: annotationTaskList.length,
      completedTasks: annotationTaskList.filter((t) => t.status === "COMPLETED")
        .length,
      inProgressTasks: annotationTaskList.filter(
        (t) => t.status === "IN_PROGRESS"
      ).length,
      pendingTasks: annotationTaskList.filter((t) => t.status === "PENDING")
        .length,
      totalAnnotations: annotationDataList.length,
      totalAnnotators: annotatorList.length,
      averageAccuracy: Mock.Random.float(0.85, 0.95, 2, 2),
      taskTypeDistribution: {
        TEXT_CLASSIFICATION: Mock.Random.integer(5, 15),
        NAMED_ENTITY_RECOGNITION: Mock.Random.integer(3, 10),
        OBJECT_DETECTION: Mock.Random.integer(2, 8),
        SEMANTIC_SEGMENTATION: Mock.Random.integer(1, 5),
      },
    };

    res.send({
      code: "0",
      msg: "Success",
      data: statistics,
    });
  });

  // 获取标注模板列表
  router.get(API.queryAnnotationTemplatesUsingGet, (req, res) => {
    const { page = 0, size = 20, type } = req.query;
    let filteredTemplates = annotationTemplateList;

    if (type) {
      filteredTemplates = filteredTemplates.filter(
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
        number: parseInt(page),
      },
    });
  });

  // 创建标注模板
  router.post(API.createAnnotationTemplateUsingPost, (req, res) => {
    const newTemplate = {
      ...annotationTemplateItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      usageCount: 0,
      createdAt: new Date().toISOString(),
    };
    annotationTemplateList.push(newTemplate);

    res.status(201).send({
      code: "0",
      msg: "Annotation template created successfully",
      data: newTemplate,
    });
  });

  // 获取标注模板详情
  router.get(API.queryAnnotationTemplateByIdUsingGet, (req, res) => {
    const { templateId } = req.params;
    const template = annotationTemplateList.find((t) => t.id === templateId);

    if (template) {
      res.send({
        code: "0",
        msg: "Success",
        data: template,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Annotation template not found",
        data: null,
      });
    }
  });

  // 获取标注者列表
  router.get(API.queryAnnotatorsUsingGet, (req, res) => {
    const { page = 0, size = 20, status, skillLevel } = req.query;
    let filteredAnnotators = annotatorList;

    if (status) {
      filteredAnnotators = filteredAnnotators.filter(
        (annotator) => annotator.status === status
      );
    }

    if (skillLevel) {
      filteredAnnotators = filteredAnnotators.filter(
        (annotator) => annotator.skillLevel === skillLevel
      );
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredAnnotators.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredAnnotators.length,
        totalPages: Math.ceil(filteredAnnotators.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 分配标注者
  router.post(API.assignAnnotatorUsingPost, (req, res) => {
    const { taskId } = req.params;
    const { annotatorIds } = req.body;

    res.send({
      code: "0",
      msg: "Annotators assigned successfully",
      data: {
        taskId,
        assignedAnnotators: annotatorIds,
        assignedAt: new Date().toISOString(),
      },
    });
  });
};
