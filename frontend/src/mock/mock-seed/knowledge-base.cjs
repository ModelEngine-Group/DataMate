const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 知识库数据
function KnowledgeBaseItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.ctitle(5, 15),
    description: Mock.Random.csentence(10, 30),
    createdBy: Mock.Random.cname(),
    updatedBy: Mock.Random.cname(),
    embeddingModel: Mock.Random.pick([
      "text-embedding-ada-002",
      "text-embedding-3-small",
      "text-embedding-3-large",
    ]),
    chatModel: Mock.Random.pick(["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const knowledgeBaseList = new Array(50).fill(null).map(KnowledgeBaseItem);

function fileItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    createdBy: Mock.Random.cname(),
    updatedBy: Mock.Random.cname(),
    knowledgeBaseId: Mock.Random.pick(knowledgeBaseList).id,
    fileId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    fileName: Mock.Random.ctitle(5, 15),
    chunkCount: Mock.Random.integer(1, 100),
    metadata: {},
    status: Mock.Random.pick([
      "UNPROCESSED",
      "PROCESSING",
      "PROCESSED",
      "PROCESS_FAILED",
    ]),
  };
}

const fileList = new Array(20).fill(null).map(fileItem);

module.exports = function (router) {
  // 获取知识库列表
  router.post(API.queryKnowledgeBasesUsingPost, (req, res) => {
    const { page = 0, size, keyword } = req.body;
    let filteredList = knowledgeBaseList;
    if (keyword) {
      filteredList = knowledgeBaseList.filter(
        (kb) => kb.name.includes(keyword) || kb.description.includes(keyword)
      );
    }
    const start = page * size;
    const end = start + size;
    const totalElements = filteredList.length;
    const paginatedList = filteredList.slice(start, end);
    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements,
        page,
        size,
        content: paginatedList,
      },
    });
  });

  // 创建知识库
  router.post(API.createKnowledgeBaseUsingPost, (req, res) => {
    const item = KnowledgeBaseItem();
    knowledgeBaseList.unshift(item);
    res.status(201).send(item);
  });

  // 获取知识库详情
  router.get(API.queryKnowledgeBaseByIdUsingGet, (req, res) => {
    const id = req.params.baseId;
    const item =
      knowledgeBaseList.find((kb) => kb.id === id) || KnowledgeBaseItem();
    res.send({
      code: "0",
      msg: "Success",
      data: item,
    });
  });

  // 更新知识库
  router.put(API.updateKnowledgeBaseByIdUsingPut, (req, res) => {
    const id = req.params.baseId;
    const idx = knowledgeBaseList.findIndex((kb) => kb.id === id);
    if (idx >= 0) {
      knowledgeBaseList[idx] = { ...knowledgeBaseList[idx], ...req.body };
      res.status(201).send(knowledgeBaseList[idx]);
    } else {
      res.status(404).send({ message: "Not found" });
    }
  });

  // 删除知识库
  router.delete(API.deleteKnowledgeBaseByIdUsingDelete, (req, res) => {
    const id = req.params.baseId;
    const idx = knowledgeBaseList.findIndex((kb) => kb.id === id);
    if (idx >= 0) {
      knowledgeBaseList.splice(idx, 1);
      res.status(201).send({ success: true });
    } else {
      res.status(404).send({ message: "Not found" });
    }
  });

  // 添加文件到知识库
  router.post(API.addKnowledgeBaseFilesUsingPost, (req, res) => {
    const file = Mock.mock({
      id: "@guid",
      name: "@ctitle(5,15)",
      size: "@integer(1000,1000000)",
      status: "uploaded",
      createdAt: "@datetime",
    });
    res.status(201).send(file);
  });

  // 获取知识生成文件详情
  router.get(API.queryKnowledgeBaseFilesGet, (req, res) => {
    const { keyword, page, size } = req.query;
    let filteredList = fileList;
    if (keyword) {
      filteredList = fileList.filter((file) => file.fileName.includes(keyword));
    }
    const start = page * size;
    const end = start + size;
    const totalElements = filteredList.length;
    const paginatedList = filteredList.slice(start, end);
    res.send({
      code: "0",
      msg: "Success",
      data: {
        totalElements,
        page,
        size,
        content: paginatedList,
      },
    });
  });

  router.get(API.queryKnowledgeBaseFilesByIdUsingGet, (req, res) => {
    const { baseId, fileId } = req.params;
    const item =
      fileList.find(
        (file) => file.knowledgeBaseId === baseId && file.id === fileId
      ) || fileItem();
    res.send({
      code: "0",
      msg: "Success",
      data: item,
    });
  });

  // 删除知识生成文件
  router.delete(API.deleteKnowledgeBaseTaskByIdUsingDelete, (req, res) => {
    const { id } = req.params;
    const idx = fileList.findIndex((file) => file.id === id);
    if (idx >= 0) {
      fileList.splice(idx, 1);
      res.status(200).send({ success: true });
      return;
    }
    res.status(404).send({ message: "Not found" });
  });
};
