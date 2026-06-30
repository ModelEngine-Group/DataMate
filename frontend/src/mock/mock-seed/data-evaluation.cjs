const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 质量指标枚举
const QualityMetrics = [
  "COMPLETENESS",
  "ACCURACY", 
  "CONSISTENCY",
  "VALIDITY",
  "UNIQUENESS",
  "TIMELINESS"
];

// 适配性标准枚举
const CompatibilityCriteria = [
  "FORMAT_COMPATIBILITY",
  "SCHEMA_COMPATIBILITY", 
  "SIZE_ADEQUACY",
  "DISTRIBUTION_MATCH",
  "FEATURE_COVERAGE"
];

// 价值标准枚举
const ValueCriteria = [
  "RARITY",
  "DEMAND",
  "QUALITY", 
  "COMPLETENESS",
  "TIMELINESS",
  "STRATEGIC_IMPORTANCE"
];

// 评估类型枚举
const EvaluationTypes = ["QUALITY", "COMPATIBILITY", "VALUE", "COMPREHENSIVE"];

// 评估状态枚举
const EvaluationStatuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED"];

// 生成质量评估结果
function qualityEvaluationItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    status: Mock.Random.pick(EvaluationStatuses),
    overallScore: Mock.Random.float(0.6, 1.0, 2, 2),
    metrics: Mock.Random.shuffle(QualityMetrics).slice(0, Mock.Random.integer(3, 5)).map(metric => ({
      metric,
      score: Mock.Random.float(0.5, 1.0, 2, 2),
      details: {
        totalRecords: Mock.Random.integer(1000, 100000),
        validRecords: Mock.Random.integer(800, 95000),
        issues: Mock.Random.integer(0, 50)
      },
      issues: new Array(Mock.Random.integer(0, 3)).fill(null).map(() => ({
        type: Mock.Random.pick(["MISSING_VALUE", "INVALID_FORMAT", "DUPLICATE", "OUTLIER"]),
        severity: Mock.Random.pick(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        description: Mock.Random.csentence(5, 15),
        affectedRecords: Mock.Random.integer(1, 1000),
        suggestions: [Mock.Random.csentence(5, 20)]
      }))
    })),
    recommendations: new Array(Mock.Random.integer(2, 5)).fill(null).map(() => 
      Mock.Random.csentence(10, 30)
    ),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    detailedResults: {
      fieldAnalysis: new Array(Mock.Random.integer(3, 8)).fill(null).map(() => ({
        fieldName: Mock.Random.word(5, 10),
        dataType: Mock.Random.pick(["STRING", "INTEGER", "FLOAT", "BOOLEAN", "DATE"]),
        nullCount: Mock.Random.integer(0, 100),
        uniqueCount: Mock.Random.integer(100, 1000),
        statistics: {
          mean: Mock.Random.float(0, 100, 2, 2),
          median: Mock.Random.float(0, 100, 2, 2),
          stdDev: Mock.Random.float(0, 50, 2, 2)
        }
      })),
      distributionAnalysis: {
        distributions: new Array(3).fill(null).map(() => ({
          field: Mock.Random.word(5, 10),
          type: Mock.Random.pick(["NORMAL", "UNIFORM", "SKEWED"]),
          parameters: {}
        })),
        outliers: new Array(Mock.Random.integer(0, 5)).fill(null).map(() => ({
          field: Mock.Random.word(5, 10),
          value: Mock.Random.float(-100, 100, 2, 2),
          zScore: Mock.Random.float(-3, 3, 2, 2)
        })),
        patterns: [
          "数据分布较为均匀",
          "存在少量异常值",
          "部分字段相关性较强"
        ]
      },
      correlationAnalysis: {
        correlationMatrix: new Array(5).fill(null).map(() => 
          new Array(5).fill(null).map(() => Mock.Random.float(-1, 1, 2, 2))
        ),
        significantCorrelations: new Array(Mock.Random.integer(1, 3)).fill(null).map(() => ({
          field1: Mock.Random.word(5, 10),
          field2: Mock.Random.word(5, 10),
          correlation: Mock.Random.float(0.5, 1, 2, 2),
          pValue: Mock.Random.float(0, 0.05, 3, 3)
        }))
      }
    },
    visualizations: new Array(Mock.Random.integer(2, 4)).fill(null).map(() => ({
      type: Mock.Random.pick(["CHART", "GRAPH", "HISTOGRAM", "HEATMAP"]),
      title: Mock.Random.ctitle(5, 15),
      data: {
        labels: new Array(5).fill(null).map(() => Mock.Random.word(3, 8)),
        values: new Array(5).fill(null).map(() => Mock.Random.integer(0, 100))
      },
      config: {
        width: 400,
        height: 300,
        color: Mock.Random.color()
      }
    }))
  };
}

// 生成适配性评估结果
function compatibilityEvaluationItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    targetType: Mock.Random.pick(["LANGUAGE_MODEL", "CLASSIFICATION_MODEL", "RECOMMENDATION_SYSTEM", "CUSTOM_TASK"]),
    compatibilityScore: Mock.Random.float(0.6, 1.0, 2, 2),
    results: Mock.Random.shuffle(CompatibilityCriteria).slice(0, Mock.Random.integer(3, 5)).map(criterion => ({
      criterion,
      score: Mock.Random.float(0.5, 1.0, 2, 2),
      status: Mock.Random.pick(["PASS", "WARN", "FAIL"]),
      details: Mock.Random.csentence(10, 30)
    })),
    suggestions: new Array(Mock.Random.integer(2, 4)).fill(null).map(() => 
      Mock.Random.csentence(10, 25)
    ),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss")
  };
}

// 生成价值评估结果
function valueEvaluationItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    valueScore: Mock.Random.float(0.6, 1.0, 2, 2),
    monetaryValue: Mock.Random.float(10000, 1000000, 2, 2),
    strategicValue: Mock.Random.float(0.6, 1.0, 2, 2),
    results: Mock.Random.shuffle(ValueCriteria).slice(0, Mock.Random.integer(3, 5)).map(criterion => ({
      criterion,
      score: Mock.Random.float(0.5, 1.0, 2, 2),
      impact: Mock.Random.pick(["LOW", "MEDIUM", "HIGH"]),
      explanation: Mock.Random.csentence(10, 30)
    })),
    insights: new Array(Mock.Random.integer(3, 6)).fill(null).map(() => 
      Mock.Random.csentence(15, 40)
    ),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss")
  };
}

// 生成评估报告
function evaluationReportItem() {
  const type = Mock.Random.pick(EvaluationTypes);
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    datasetName: Mock.Random.ctitle(5, 15),
    type,
    status: Mock.Random.pick(EvaluationStatuses),
    overallScore: Mock.Random.float(0.6, 1.0, 2, 2),
    summary: Mock.Random.csentence(20, 50),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    completedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    qualityResults: type === "QUALITY" || type === "COMPREHENSIVE" ? qualityEvaluationItem() : null,
    compatibilityResults: type === "COMPATIBILITY" || type === "COMPREHENSIVE" ? compatibilityEvaluationItem() : null,
    valueResults: type === "VALUE" || type === "COMPREHENSIVE" ? valueEvaluationItem() : null,
    attachments: new Array(Mock.Random.integer(1, 3)).fill(null).map(() => ({
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      name: Mock.Random.word(5, 10) + "." + Mock.Random.pick(["pdf", "xlsx", "json"]),
      type: Mock.Random.pick(["PDF", "EXCEL", "JSON"]),
      size: Mock.Random.integer(1024, 1024 * 1024),
      downloadUrl: "/api/v1/evaluation/attachments/" + Mock.Random.guid()
    }))
  };
}

const qualityEvaluationList = new Array(30).fill(null).map(qualityEvaluationItem);
const compatibilityEvaluationList = new Array(20).fill(null).map(compatibilityEvaluationItem);
const valueEvaluationList = new Array(25).fill(null).map(valueEvaluationItem);
const evaluationReportList = new Array(50).fill(null).map(evaluationReportItem);

module.exports = function (router) {
  // 数据质量评估
  router.post(API.evaluateDataQualityUsingPost, (req, res) => {
    const { datasetId, metrics, sampleSize, parameters } = req.body;
    
    const newEvaluation = {
      ...qualityEvaluationItem(),
      datasetId,
      status: "RUNNING",
      metrics: metrics.map(metric => ({
        metric,
        score: Mock.Random.float(0.5, 1.0, 2, 2),
        details: {
          totalRecords: sampleSize || Mock.Random.integer(1000, 100000),
          validRecords: Mock.Random.integer(800, 95000),
          issues: Mock.Random.integer(0, 50)
        },
        issues: []
      })),
      createdAt: new Date().toISOString()
    };
    
    qualityEvaluationList.push(newEvaluation);
    
    // 模拟异步处理，2秒后完成
    setTimeout(() => {
      newEvaluation.status = "COMPLETED";
    }, 2000);
    
    res.send({
      code: "0",
      msg: "Quality evaluation started successfully",
      data: newEvaluation
    });
  });

  // 获取质量评估结果
  router.get(API.getQualityEvaluationByIdUsingGet, (req, res) => {
    const { evaluationId } = req.params;
    const evaluation = qualityEvaluationList.find(e => e.id === evaluationId);
    
    if (evaluation) {
      res.send({
        code: "0",
        msg: "Success",
        data: evaluation
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Quality evaluation not found",
        data: null
      });
    }
  });

  // 适配性评估
  router.post(API.evaluateCompatibilityUsingPost, (req, res) => {
    const { datasetId, targetType, targetConfig, evaluationCriteria } = req.body;
    
    const newEvaluation = {
      ...compatibilityEvaluationItem(),
      datasetId,
      targetType,
      results: evaluationCriteria.map(criterion => ({
        criterion,
        score: Mock.Random.float(0.5, 1.0, 2, 2),
        status: Mock.Random.pick(["PASS", "WARN", "FAIL"]),
        details: Mock.Random.csentence(10, 30)
      })),
      createdAt: new Date().toISOString()
    };
    
    compatibilityEvaluationList.push(newEvaluation);
    
    res.send({
      code: "0",
      msg: "Compatibility evaluation completed successfully",
      data: newEvaluation
    });
  });

  // 价值评估
  router.post(API.evaluateValueUsingPost, (req, res) => {
    const { datasetId, valueCriteria, marketContext, businessContext } = req.body;
    
    const newEvaluation = {
      ...valueEvaluationItem(),
      datasetId,
      results: valueCriteria.map(criterion => ({
        criterion,
        score: Mock.Random.float(0.5, 1.0, 2, 2),
        impact: Mock.Random.pick(["LOW", "MEDIUM", "HIGH"]),
        explanation: Mock.Random.csentence(10, 30)
      })),
      createdAt: new Date().toISOString()
    };
    
    valueEvaluationList.push(newEvaluation);
    
    res.send({
      code: "0",
      msg: "Value evaluation completed successfully",
      data: newEvaluation
    });
  });

  // 获取评估报告列表
  router.get(API.queryEvaluationReportsUsingGet, (req, res) => {
    const { page = 0, size = 20, type, datasetId } = req.query;
    let filteredReports = evaluationReportList;
    
    if (type) {
      filteredReports = filteredReports.filter(report => report.type === type);
    }
    
    if (datasetId) {
      filteredReports = filteredReports.filter(report => report.datasetId === datasetId);
    }
    
    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredReports.slice(startIndex, endIndex);
    
    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredReports.length,
        totalPages: Math.ceil(filteredReports.length / size),
        size: parseInt(size),
        number: parseInt(page)
      }
    });
  });

  // 获取评估报告详情
  router.get(API.getEvaluationReportByIdUsingGet, (req, res) => {
    const { reportId } = req.params;
    const report = evaluationReportList.find(r => r.id === reportId);
    
    if (report) {
      res.send({
        code: "0",
        msg: "Success",
        data: report
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Evaluation report not found",
        data: null
      });
    }
  });

  // 导出评估报告
  router.get(API.exportEvaluationReportUsingGet, (req, res) => {
    const { reportId } = req.params;
    const { format = "PDF" } = req.query;
    const report = evaluationReportList.find(r => r.id === reportId);
    
    if (report) {
      const fileName = `evaluation_report_${reportId}.${format.toLowerCase()}`;
      
      res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
      res.setHeader('Content-Type', 'application/octet-stream');
      res.send(`Mock ${format} content for evaluation report ${reportId}`);
    } else {
      res.status(404).send({
        code: "1",
        msg: "Evaluation report not found",
        data: null
      });
    }
  });

  // 批量评估
  router.post(API.batchEvaluationUsingPost, (req, res) => {
    const { datasetIds, evaluationTypes, parameters } = req.body;
    
    const batchId = Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, "");
    const totalTasks = datasetIds.length * evaluationTypes.length;
    
    // 为每个数据集和评估类型组合创建任务
    datasetIds.forEach(datasetId => {
      evaluationTypes.forEach(type => {
        const report = {
          ...evaluationReportItem(),
          datasetId,
          type,
          status: "PENDING",
          batchId
        };
        evaluationReportList.push(report);
        
        // 模拟异步处理
        setTimeout(() => {
          report.status = "COMPLETED";
        }, Mock.Random.integer(3000, 10000));
      });
    });
    
    res.status(202).send({
      code: "0",
      msg: "Batch evaluation submitted successfully",
      data: {
        batchId,
        status: "SUBMITTED",
        totalTasks,
        submittedAt: new Date().toISOString()
      }
    });
  });

  // 获取批量评估状态
  router.get("/api/v1/evaluation/batch/:batchId", (req, res) => {
    const { batchId } = req.params;
    const batchReports = evaluationReportList.filter(r => r.batchId === batchId);
    
    const completedTasks = batchReports.filter(r => r.status === "COMPLETED").length;
    const runningTasks = batchReports.filter(r => r.status === "RUNNING").length;
    const pendingTasks = batchReports.filter(r => r.status === "PENDING").length;
    const failedTasks = batchReports.filter(r => r.status === "FAILED").length;
    
    let overallStatus = "COMPLETED";
    if (runningTasks > 0 || pendingTasks > 0) {
      overallStatus = "RUNNING";
    } else if (failedTasks > 0) {
      overallStatus = "PARTIAL_FAILED";
    }
    
    res.send({
      code: "0",
      msg: "Success",
      data: {
        batchId,
        status: overallStatus,
        totalTasks: batchReports.length,
        completedTasks,
        runningTasks,
        pendingTasks,
        failedTasks,
        progress: batchReports.length > 0 ? Math.round((completedTasks / batchReports.length) * 100) : 0,
        reports: batchReports
      }
    });
  });

  // 获取评估统计信息
  router.get("/api/v1/evaluation/statistics", (req, res) => {
    const { timeRange = "LAST_30_DAYS" } = req.query;
    
    const statistics = {
      totalEvaluations: evaluationReportList.length,
      completedEvaluations: evaluationReportList.filter(r => r.status === "COMPLETED").length,
      runningEvaluations: evaluationReportList.filter(r => r.status === "RUNNING").length,
      failedEvaluations: evaluationReportList.filter(r => r.status === "FAILED").length,
      averageScore: Mock.Random.float(0.75, 0.95, 2, 2),
      evaluationTypeDistribution: {
        QUALITY: evaluationReportList.filter(r => r.type === "QUALITY").length,
        COMPATIBILITY: evaluationReportList.filter(r => r.type === "COMPATIBILITY").length,
        VALUE: evaluationReportList.filter(r => r.type === "VALUE").length,
        COMPREHENSIVE: evaluationReportList.filter(r => r.type === "COMPREHENSIVE").length
      },
      scoreDistribution: {
        excellent: evaluationReportList.filter(r => r.overallScore >= 0.9).length,
        good: evaluationReportList.filter(r => r.overallScore >= 0.8 && r.overallScore < 0.9).length,
        fair: evaluationReportList.filter(r => r.overallScore >= 0.6 && r.overallScore < 0.8).length,
        poor: evaluationReportList.filter(r => r.overallScore < 0.6).length
      },
      trends: new Array(30).fill(null).map((_, index) => ({
        date: Mock.Random.date("yyyy-MM-dd"),
        evaluations: Mock.Random.integer(5, 50),
        averageScore: Mock.Random.float(0.7, 0.95, 2, 2)
      }))
    };
    
    res.send({
      code: "0",
      msg: "Success",
      data: statistics
    });
  });

  // 删除评估报告
  router.delete("/api/v1/evaluation/reports/:reportId", (req, res) => {
    const { reportId } = req.params;
    const index = evaluationReportList.findIndex(r => r.id === reportId);
    
    if (index !== -1) {
      evaluationReportList.splice(index, 1);
      res.send({
        code: "0",
        msg: "Evaluation report deleted successfully",
        data: null
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Evaluation report not found",
        data: null
      });
    }
  });
};