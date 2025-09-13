const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

function tagItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.word(3, 10),
    description: Mock.Random.csentence(5, 20),
    color: Mock.Random.color(),
    usageCount: Mock.Random.integer(0, 100),
  };
}
const tagList = new Array(20).fill(null).map((_, index) => tagItem(index));

function datasetItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 20),
    type: Mock.Random.pick(["image", "text", "audio", "video"]),
    status: Mock.Random.pick(["ACTIVE", "INACTIVE", "PROCESSING"]),
    tags: Mock.Random.shuffle(tagList).slice(0, Mock.Random.integer(1, 3)),
    dataSource: "dataSource",
    targetLocation: "targetLocation",
    fileCount: Mock.Random.integer(1, 100),
    totalSize: Mock.Random.integer(1024, 1024 * 1024 * 1024), // in bytes
    completionRate: Mock.Random.integer(0, 100), // percentage
    description: Mock.Random.cparagraph(1, 3),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    createdBy: Mock.Random.cname(),
    updatedBy: Mock.Random.cname(),
  };
}

const datasetList = new Array(50)
  .fill(null)
  .map((_, index) => datasetItem(index));

function datasetFileItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    fileName:
      Mock.Random.word(5, 15) +
      "." +
      Mock.Random.pick(["csv", "json", "xml", "parquet", "avro"]),
    originName:
      Mock.Random.word(5, 15) +
      "." +
      Mock.Random.pick(["csv", "json", "xml", "parquet", "avro"]),
    fileType: Mock.Random.pick(["CSV", "JSON", "XML", "Parquet", "Avro"]),
    size: Mock.Random.integer(1024, 1024 * 1024 * 1024), // in bytes
    type: Mock.Random.pick(["CSV", "JSON", "XML", "Parquet", "Avro"]),
    status: Mock.Random.pick(["UPLOADED", "PROCESSING", "COMPLETED", "ERROR"]),
    description: Mock.Random.csentence(5, 20),
    filePath: "/path/to/file/" + Mock.Random.word(5, 10),
    uploadedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    uploadedBy: Mock.Random.cname(),
  };
}

const datasetFileList = new Array(200)
  .fill(null)
  .map((_, index) => datasetFileItem(index));

const datasetStatistics = {
  count: {
    text: 10,
    image: 34,
    audio: 23,
    video: 5,
  },
  size: {
    text: "120 MB",
    image: "3.4 GB",
    audio: "2.3 GB",
    video: "15 GB",
  },
  totalDatasets: datasetList.length,
  totalFiles: datasetFileList.length,
  completedFiles: datasetFileList.filter((file) => file.status === "COMPLETED")
    .length,
  totalSize: datasetFileList.reduce((acc, file) => acc + file.size, 0), // in bytes
  completionRate:
    datasetFileList.length === 0
      ? 0
      : Math.round(
          (datasetFileList.filter((file) => file.status === "COMPLETED")
            .length /
            datasetFileList.length) *
            100
        ), // percentage
};

module.exports = function (router) {
  // 获取数据统计信息
  router.get(API.getDatasetStatisticsUsingGet, (req, res) => {
    res.send({
      code: "0",
      msg: "Success",
      data: datasetStatistics,
    });
  });

  // 创建数据
  router.post(API.createDatasetUsingPost, (req, res) => {
    const newDataset = {
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      status: "ACTIVE",
      fileCount: 0,
      totalSize: 0,
      completionRate: 0,
      createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
      updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
      createdBy: "Admin",
      updatedBy: "Admin",
      tags: tagList.filter((tag) => req.body?.tagIds?.includes?.(tag.id)),
    };
    datasetList.unshift(newDataset); // Add to the beginning of the list
    res.send({
      code: "0",
      msg: "Dataset created successfully",
      data: newDataset,
    });
  });

  router.get(API.queryDatasetsUsingGet, (req, res) => {
    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements: datasetList.length,
        page: 1,
        size: 10,
        results: datasetList.slice(0, 10),
      },
    });
  });

  // 获取数据集列表
  router.post(API.queryDatasetsUsingGet, (req, res) => {
    const { page = 1, size = 10, keywords, type, status, tags } = req.body;

    let filteredDatasets = datasetList;
    if (keywords) {
      console.log("filter keywords:", keywords);

      filteredDatasets = filteredDatasets.filter((dataset) =>
        dataset.name.includes(keywords) || dataset.description.includes(keywords
      );
    }
    if (type) {
      console.log("filter type:", type);

      filteredDatasets = filteredDatasets.filter(
        (dataset) => dataset.type === type
      );
    }
    if (status) {
      console.log("filter status:", status);
      filteredDatasets = filteredDatasets.filter(
        (dataset) => dataset.status === status
      );
    }
    if (tags && tags.length > 0) {
      console.log("filter tags:", tags);
      filteredDatasets = filteredDatasets.filter((dataset) =>
        tags.every((tag) => dataset.tags.some((t) => t.name === tag))
      );
    }

    const totalElements = filteredDatasets.length;
    const paginatedDatasets = filteredDatasets.slice(
      (page - 1) * size,
      page * size
    );

    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements,
        page,
        size,
        results: paginatedDatasets,
      },
    });
  });

  router.get(API.getDatasetByIdUsingGet, (req, res) => {
    const { id } = req.query;
    const dataset = datasetList.find((d) => d.id === id);
    if (dataset) {
      res.send({
        code: "0",
        msg: "Success",
        data: dataset,
      });
    } else {
      res.send({
        code: "1",
        msg: "Dataset not found",
        data: null,
      });
    }
  });
};
