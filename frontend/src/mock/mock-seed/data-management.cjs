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
    type: Mock.Random.pick([
      "TEXT_DOCUMENT",
      "TEXT_WEB",
      "TEXT_DIALOG",
      "IMAGE_IMAGE",
      "IMAGE_CAPTION",
      "AUDIO_AUDIO",
      "AUDIO_JSONL",
      "VIDEO_VIDEO",
      "VIDEO_JSONL",
    ]),
    status: Mock.Random.pick(["ACTIVE", "INACTIVE", "PROCESSING"]),
    tags: Mock.Random.shuffle(tagList).slice(0, Mock.Random.integer(1, 3)),
    totalSize: Mock.Random.integer(1024, 1024 * 1024 * 1024), // in bytes
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

const datasetTypes = [
  {
    code: "PRETRAIN",
    name: "预训练数据集",
    description: "用于模型预训练的大规模数据集",
    supportedFormats: ["txt", "json", "csv", "parquet"],
    icon: "brain",
  },
  {
    code: "FINE_TUNE",
    name: "微调数据集",
    description: "用于模型微调的专业数据集",
    supportedFormats: ["json", "csv", "xlsx"],
    icon: "tune",
  },
  {
    code: "EVAL",
    name: "评估数据集",
    description: "用于模型评估的标准数据集",
    supportedFormats: ["json", "csv", "xml"],
    icon: "assessment",
  },
];

module.exports = { datasetList };
module.exports = function (router) {
  // 获取数据统计信息
  router.get(API.queryDatasetStatisticsUsingGet, (req, res) => {
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

  // 获取数据集列表
  router.get(API.queryDatasetsUsingGet, (req, res) => {
    const { page = 0, size = 10, keywords, type, status, tags } = req.query;
    console.log("Received query params:", req.query);

    let filteredDatasets = datasetList;
    if (keywords) {
      console.log("filter keywords:", keywords);

      filteredDatasets = filteredDatasets.filter(
        (dataset) =>
          dataset.name.includes(keywords) ||
          dataset.description.includes(keywords)
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
      page * size,
      (page + 1) * size
    );

    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements,
        page,
        size,
        content: paginatedDatasets,
      },
    });
  });

  // 根据ID获取数据集详情
  router.get(API.queryDatasetByIdUsingGet, (req, res) => {
    const { id } = req.params;

    const dataset = datasetList.find((d) => d.id === id);
    if (dataset) {
      res.send({
        code: "0",
        msg: "Success",
        data: dataset,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Dataset not found",
        data: null,
      });
    }
  });

  // 更新数据集
  router.put(API.updateDatasetByIdUsingPut, (req, res) => {
    const { datasetId } = req.params;
    const index = datasetList.findIndex((d) => d.id === datasetId);

    if (index !== -1) {
      datasetList[index] = {
        ...datasetList[index],
        ...req.body,
        updatedAt: new Date().toISOString(),
        updatedBy: "Admin",
      };
      res.send({
        code: "0",
        msg: "Dataset updated successfully",
        data: datasetList[index],
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "Dataset not found",
        data: null,
      });
    }
  });

  // 删除数据集
  router.delete(API.deleteDatasetByIdUsingDelete, (req, res) => {
    const { datasetId } = req.params;
    const index = datasetList.findIndex((d) => d.id === datasetId);

    if (index !== -1) {
      datasetList.splice(index, 1);
      res.status(204).send();
    } else {
      res.status(404).send({
        code: "1",
        msg: "Dataset not found",
        data: null,
      });
    }
  });

  // 获取数据集文件列表
  router.get(API.queryFilesUsingGet, (req, res) => {
    const { datasetId } = req.params;
    const { page = 0, size = 20, fileType, status } = req.query;

    let filteredFiles = datasetFileList;

    if (fileType) {
      filteredFiles = filteredFiles.filter(
        (file) => file.fileType === fileType
      );
    }

    if (status) {
      filteredFiles = filteredFiles.filter((file) => file.status === status);
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredFiles.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        page: parseInt(page),
        size: parseInt(size),
        totalElements: filteredFiles.length,
      },
    });
  });

  // 上传文件到数据集
  router.post(API.uploadFileUsingPost, (req, res) => {
    const { datasetId } = req.params;
    const newFile = {
      ...datasetFileItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      uploadedAt: new Date().toISOString(),
      uploadedBy: "Admin",
    };

    datasetFileList.push(newFile);

    res.status(201).send({
      code: "0",
      msg: "File uploaded successfully",
      data: newFile,
    });
  });

  // 获取文件详情
  router.get(API.queryFileByIdUsingGet, (req, res) => {
    const { datasetId, fileId } = req.params;
    const file = datasetFileList.find((f) => f.id === fileId);

    if (file) {
      res.send({
        code: "0",
        msg: "Success",
        data: file,
      });
    } else {
      res.status(404).send({
        code: "1",
        msg: "File not found",
        data: null,
      });
    }
  });

  // 删除文件
  router.delete(API.deleteFileByIdUsingDelete, (req, res) => {
    const { datasetId, fileId } = req.params;
    const index = datasetFileList.findIndex((f) => f.id === fileId);

    if (index !== -1) {
      datasetFileList.splice(index, 1);
      res.status(204).send();
    } else {
      res.status(404).send({
        code: "1",
        msg: "File not found",
        data: null,
      });
    }
  });

  // 下载文件
  router.get(API.downloadFileByIdUsingGet, (req, res) => {
    const { datasetId, fileId } = req.params;
    const file = datasetFileList.find((f) => f.id === fileId);

    if (file) {
      res.setHeader(
        "Content-Disposition",
        `attachment; filename="${file.fileName}"`
      );
      res.setHeader("Content-Type", "application/octet-stream");
      res.send(`Mock file content for ${file.fileName}`);
    } else {
      res.status(404).send({
        code: "1",
        msg: "File not found",
        data: null,
      });
    }
  });

  // 获取数据集类型列表
  router.get(API.queryDatasetTypesUsingGet, (req, res) => {
    res.send({
      code: "0",
      msg: "Success",
      data: datasetTypes,
    });
  });

  // 获取标签列表
  router.get(API.queryTagsUsingGet, (req, res) => {
    const { keyword } = req.query;
    let filteredTags = tagList;

    if (keyword) {
      filteredTags = tagList.filter((tag) =>
        tag.name.toLowerCase().includes(keyword.toLowerCase())
      );
    }

    res.send({
      code: "0",
      msg: "Success",
      data: filteredTags,
    });
  });

  // 创建标签
  router.post(API.createTagUsingPost, (req, res) => {
    const newTag = {
      ...tagItem(),
      ...req.body,
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      usageCount: 0,
    };

    tagList.push(newTag);

    res.status(201).send({
      code: "0",
      msg: "Tag created successfully",
      data: newTag,
    });
  });
};
