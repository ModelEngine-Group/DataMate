const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 算子标签数据
function ModelItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    modelName: Mock.Random.pick([
      "数据清洗",
      "特征选择",
      "分类算法",
      "聚类算法",
      "回归分析",
      "深度神经网络",
      "卷积神经网络",
      "循环神经网络",
      "注意力机制",
      "文本分析",
      "图像处理",
      "语音识别",
      "推荐算法",
      "异常检测",
      "优化算法",
      "集成学习",
      "迁移学习",
      "强化学习",
      "联邦学习",
    ]),
    provider: Mock.Random.pick([
      "OpenAI",
      "Anthropic",
      "Cohere",
      "AI21 Labs",
      "Hugging Face",
      "Google Cloud AI",
      "Microsoft Azure AI",
      "Amazon Web Services AI",
      "IBM Watson",
      "Alibaba Cloud AI",
    ]),
    type: Mock.Random.pick(["CHAT", "EMBEDDING"]),
    usageCount: Mock.Random.integer(1, 500),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const modelList = new Array(50).fill(null).map(ModelItem);

function ProviderItem(provider) {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    provider,
    baseUrl: Mock.Random.url("https") + "/v1/models",
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const ProviderList = [
  "OpenAI",
  "Anthropic",
  "Cohere",
  "AI21 Labs",
  "Hugging Face",
  "Google Cloud AI",
  "Microsoft Azure AI",
  "Amazon Web Services AI",
  "IBM Watson",
  "Alibaba Cloud AI",
].map(ProviderItem);

module.exports = function (router) {
  // 获取模型列表
  router.get(API.queryModelsUsingGet, (req, res) => {
    const {
      page = 0,
      size = 20,
      keyword = "",
      provider = "",
      type = "",
    } = req.query;

    let filteredModels = modelList;

    if (keyword) {
      filteredModels = modelList.filter((model) =>
        model.modelName.toLowerCase().includes(keyword.toLowerCase())
      );
    }
    if (provider && provider !== "all") {
      filteredModels = filteredModels.filter(
        (model) => model.provider === provider
      );
    }
    if (type && type !== "all") {
      filteredModels = filteredModels.filter((model) => model.type === type);
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredModels.slice(startIndex, endIndex);

    res.status(201).send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredModels.length,
        totalPages: Math.ceil(filteredModels.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 获取模型提供商列表
  router.get(API.queryProvidersUsingGet, (req, res) => {
    res.status(201).send({
      code: "0",
      msg: "success",
      data: ProviderList,
    });
  });

  // 创建模型
  router.post(API.createModelUsingPost, (req, res) => {
    const { ...modelData } = req.body;
    const newModel = {
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      ...modelData,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    modelList.unshift(newModel);
    res.status(201).send({
      code: "0",
      msg: "success",
      data: newModel,
    });
  });

  // 删除模型
  router.delete(API.deleteModelUsingDelete, (req, res) => {
    const { id } = req.params;

    const index = modelList.findIndex((model) => model.id === id);
    if (index !== -1) {
      modelList.splice(index, 1);
    }

    res.status(204).send({
      code: "0",
      msg: "success",
      data: null,
    });
  });

  // 更新模型
  router.put(API.updateModelUsingPut, (req, res) => {
    const { id, ...update } = req.params;

    const index = modelList.findIndex((model) => model.id === id);
    if (index !== -1) {
      modelList[index] = {
        ...modelList[index],
        ...update,
        updatedAt: new Date().toISOString(),
      };
    }

    res.status(201).send({
      code: "0",
      msg: "success",
      data: null,
    });
  });
};
