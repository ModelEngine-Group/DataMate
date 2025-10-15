const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 算子标签数据
function labelItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.pick([
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
    usageCount: Mock.Random.integer(1, 500),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
  };
}

const labelList = new Array(50).fill(null).map(labelItem);

module.exports = function (router) {
  // 获取算子标签列表
  router.get(API.queryLabelsUsingGet, (req, res) => {
    const { page = 0, size = 20, keyword = "" } = req.query;

    let filteredLabels = labelList;

    if (keyword) {
      filteredLabels = labelList.filter((label) =>
        label.name.toLowerCase().includes(keyword.toLowerCase())
      );
    }

    const startIndex = page * size;
    const endIndex = startIndex + parseInt(size);
    const pageData = filteredLabels.slice(startIndex, endIndex);

    res.send({
      code: "0",
      msg: "Success",
      data: {
        content: pageData,
        totalElements: filteredLabels.length,
        totalPages: Math.ceil(filteredLabels.length / size),
        size: parseInt(size),
        number: parseInt(page),
      },
    });
  });

  // 创建标签
  router.post(API.createLabelUsingPost, (req, res) => {
    const { name } = req.body;

    const newLabel = {
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      name,
      usageCount: 0,
      createdAt: new Date().toISOString(),
    };

    labelList.push(newLabel);

    res.status(201).send({
      code: "0",
      msg: "Label created successfully",
      data: newLabel,
    });
  });

  // 批量删除标签
  router.delete(API.deleteLabelsUsingDelete, (req, res) => {
    const labelIds = req.body; // 数组形式的标签ID列表

    let deletedCount = 0;
    labelIds.forEach((labelId) => {
      const index = labelList.findIndex((label) => label.id === labelId);
      if (index !== -1) {
        labelList.splice(index, 1);
        deletedCount++;
      }
    });

    res.status(204).send();
  });

  // 更新标签
  router.put(API.updateLabelByIdUsingPut, (req, res) => {
    const { id } = req.params;
    const updates = req.body; // 数组形式的更新数据

    updates.forEach((update) => {
      const index = labelList.findIndex((label) => label.id === update.id);
      if (index !== -1) {
        labelList[index] = {
          ...labelList[index],
          ...update,
          updatedAt: new Date().toISOString(),
        };
      }
    });

    res.send({
      code: "0",
      msg: "Labels updated successfully",
      data: null,
    });
  });
};
