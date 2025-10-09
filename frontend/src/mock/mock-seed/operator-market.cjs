const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

// 算子分类数据
function categoryItem() {
  return {
    id: Mock.Random.integer(1, 1000),
    name: Mock.Random.pick([
      "数据预处理",
      "特征工程", 
      "机器学习",
      "深度学习",
      "自然语言处理",
      "计算机视觉",
      "推荐系统",
      "时间序列",
      "图神经网络",
      "强化学习"
    ]),
    count: Mock.Random.integer(5, 100),
    type: Mock.Random.pick(["0", "1"]), // 0: 预置，1: 自定义
    parentId: Mock.Random.integer(0, 10),
    categories: []
  };
}

// 生成分类树结构
function generateCategoryTree() {
  const rootCategories = new Array(8).fill(null).map(() => {
    const category = categoryItem();
    category.parentId = 0;
    category.categories = new Array(Mock.Random.integer(2, 5)).fill(null).map(() => {
      const subCategory = categoryItem();
      subCategory.parentId = category.id;
      subCategory.categories = [];
      return subCategory;
    });
    return category;
  });
  return rootCategories;
}

const categoryTree = generateCategoryTree();

// 算子标签数据
function labelItem() {
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.pick([
      "数据清洗", "特征选择", "分类算法", "聚类算法", "回归分析", 
      "深度神经网络", "卷积神经网络", "循环神经网络", "注意力机制",
      "文本分析", "图像处理", "语音识别", "推荐算法", "异常检测",
      "优化算法", "集成学习", "迁移学习", "强化学习", "联邦学习"
    ]),
    usageCount: Mock.Random.integer(1, 500),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss")
  };
}

const labelList = new Array(50).fill(null).map(labelItem);

// 算子数据
function operatorItem() {
  const categories = categoryTree.flatMap(cat => [cat, ...cat.categories]);
  const selectedCategory = Mock.Random.pick(categories);
  const selectedLabels = Mock.Random.shuffle(labelList).slice(0, Mock.Random.integer(2, 5));
  
  return {
    id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
    name: Mock.Random.pick([
      "数据标准化算子", "缺失值填充算子", "异常值检测算子", "特征选择算子",
      "线性回归算子", "逻辑回归算子", "决策树算子", "随机森林算子",
      "支持向量机算子", "K均值聚类算子", "DBSCAN聚类算子", "PCA降维算子",
      "卷积神经网络算子", "LSTM算子", "Transformer算子", "BERT算子",
      "文本分类算子", "情感分析算子", "目标检测算子", "图像分割算子"
    ]),
    description: Mock.Random.csentence(10, 50),
    version: Mock.Random.pick(["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"]),
    category: {
      id: selectedCategory.id,
      name: selectedCategory.name
    },
    labels: selectedLabels.map(label => ({
      id: label.id,
      name: label.name
    })),
    language: Mock.Random.pick(["Python", "R", "Java", "Scala", "Julia"]),
    modal: Mock.Random.pick(["CPU", "GPU", "TPU"]),
    inputs: JSON.stringify({
      data: {
        type: "DataFrame",
        description: "输入数据集",
        required: true
      },
      parameters: {
        type: "Object",
        description: "算法参数",
        required: false
      }
    }),
    outputs: JSON.stringify({
      result: {
        type: "DataFrame", 
        description: "处理结果"
      },
      metrics: {
        type: "Object",
        description: "性能指标"
      }
    }),
    runtime: JSON.stringify({
      memory: Mock.Random.pick(["512MB", "1GB", "2GB", "4GB"]),
      cpu: Mock.Random.pick(["1 core", "2 cores", "4 cores"]),
      timeout: Mock.Random.integer(30, 3600) + "s"
    }),
    settings: JSON.stringify({
      configurable: Mock.Random.boolean(),
      parameters: {
        learning_rate: {
          type: "float",
          default: 0.01,
          range: [0.001, 1.0]
        },
        max_iterations: {
          type: "int", 
          default: 100,
          range: [10, 1000]
        }
      }
    }),
    isStar: Mock.Random.boolean(),
    isPublic: Mock.Random.boolean(),
    downloadCount: Mock.Random.integer(0, 10000),
    rating: Mock.Random.float(3.0, 5.0, 1, 1),
    ratingCount: Mock.Random.integer(0, 1000),
    author: {
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      name: Mock.Random.cname(),
      avatar: Mock.Random.image("40x40", Mock.Random.color(), "#FFF", "png", Mock.Random.first())
    },
    documentation: Mock.Random.cparagraph(3, 8),
    changelog: Mock.Random.cparagraph(2, 5),
    dependencies: Mock.Random.shuffle([
      "numpy>=1.18.0",
      "pandas>=1.0.0", 
      "scikit-learn>=0.24.0",
      "torch>=1.8.0",
      "tensorflow>=2.4.0"
    ]).slice(0, Mock.Random.integer(1, 3)),
    license: Mock.Random.pick(["MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0"]),
    repositoryUrl: Mock.Random.url("https", "github.com"),
    createdAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    updatedAt: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
    status: Mock.Random.pick(["PUBLISHED", "DRAFT", "REVIEWING", "REJECTED"]),
    tags: selectedLabels.map(label => label.name)
  };
}

const operatorList = new Array(100).fill(null).map(operatorItem);

module.exports = function (router) {
  // 获取算子列表
  router.post(API.queryOperatorsUsingPost, (req, res) => {
    const { 
      page = 0, 
      size = 20, 
      categories = [], 
      operatorName = "",
      labelName = "",
      isStar
    } = req.body;
    
    let filteredOperators = operatorList;
    
    // 按分类筛选
    if (categories && categories.length > 0) {
      filteredOperators = filteredOperators.filter(op => 
        categories.includes(op.category.id)
      );
    }
    
    // 按名称搜索
    if (operatorName) {
      filteredOperators = filteredOperators.filter(op =>
        op.name.toLowerCase().includes(operatorName.toLowerCase())
      );
    }
    
    // 按标签筛选
    if (labelName) {
      filteredOperators = filteredOperators.filter(op =>
        op.labels.some(label => label.name.includes(labelName))
      );
    }
    
    // 按收藏状态筛选
    if (typeof isStar === 'boolean') {
      filteredOperators = filteredOperators.filter(op => op.isStar === isStar);
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
        last: page >= Math.ceil(filteredOperators.length / size) - 1
      }
    });
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
      category: typeof category === 'string' ? { id: category, name: category } : category,
      documentation,
      status: "REVIEWING",
      downloadCount: 0,
      rating: 0,
      ratingCount: 0,
      isStar: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    operatorList.push(newOperator);
    
    res.status(201).send({
      code: "0",
      msg: "Operator created successfully",
      data: newOperator
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
      updatedAt: new Date().toISOString()
    };
    
    operatorList.push(newOperator);
    
    res.status(201).send({
      code: "0",
      msg: "Operator uploaded successfully",
      data: newOperator
    });
  });

  // 获取算子详情
  router.get(API.queryOperatorByIdUsingGet, (req, res) => {
    const { id } = req.params;
    const operator = operatorList.find(op => op.id === id);
    
    if (operator) {
      // 增加浏览次数模拟
      operator.viewCount = (operator.viewCount || 0) + 1;
      
      res.send({
        code: "0",
        msg: "Success",
        data: operator
      });
    } else {
      res.status(404).send({
        error: "OPERATOR_NOT_FOUND",
        message: "算子不存在",
        timestamp: new Date().toISOString()
      });
    }
  });

  // 更新算子信息
  router.put(API.updateOperatorByIdUsingPut, (req, res) => {
    const { id } = req.params;
    const index = operatorList.findIndex(op => op.id === id);
    
    if (index !== -1) {
      operatorList[index] = {
        ...operatorList[index],
        ...req.body,
        updatedAt: new Date().toISOString()
      };
      
      res.send({
        code: "0",
        msg: "Operator updated successfully", 
        data: operatorList[index]
      });
    } else {
      res.status(404).send({
        error: "OPERATOR_NOT_FOUND",
        message: "算子不存在",
        timestamp: new Date().toISOString()
      });
    }
  });

  // 创建算子分类
  router.post(API.createCategoryUsingPost, (req, res) => {
    const { name, parentId } = req.body;
    
    const newCategory = {
      id: Mock.Random.integer(1001, 9999),
      name,
      count: 0,
      type: "1", // 自定义分类
      parentId,
      categories: []
    };
    
    // 添加到对应的父分类下
    if (parentId === 0) {
      categoryTree.push(newCategory);
    } else {
      const parentCategory = categoryTree.find(cat => cat.id === parentId);
      if (parentCategory) {
        parentCategory.categories.push(newCategory);
      }
    }
    
    res.status(201).send({
      code: "0",
      msg: "Category created successfully",
      data: newCategory
    });
  });

  // 删除算子分类
  router.delete(API.deleteCategoryUsingDelete, (req, res) => {
    const { id } = req.body;
    
    // 从根分类中查找并删除
    const rootIndex = categoryTree.findIndex(cat => cat.id === id);
    if (rootIndex !== -1) {
      categoryTree.splice(rootIndex, 1);
      res.status(204).send();
      return;
    }
    
    // 从子分类中查找并删除
    for (const rootCat of categoryTree) {
      const subIndex = rootCat.categories.findIndex(cat => cat.id === id);
      if (subIndex !== -1) {
        rootCat.categories.splice(subIndex, 1);  
        res.status(204).send();
        return;
      }
    }
    
    res.status(404).send({
      error: "CATEGORY_NOT_FOUND",
      message: "分类不存在",
      timestamp: new Date().toISOString()
    });
  });

  // 获取算子分类树
  router.get(API.queryCategoryTreeUsingGet, (req, res) => {
    // 更新每个分类的算子数量
    const updateCategoryCount = (categories) => {
      return categories.map(category => ({
        ...category,
        count: operatorList.filter(op => 
          op.category.id === category.id || 
          category.categories.some(subCat => subCat.id === op.category.id)
        ).length,
        categories: updateCategoryCount(category.categories)
      }));
    };
    
    const updatedCategoryTree = updateCategoryCount(categoryTree);
    
    res.send({
      code: "0",
      msg: "Success",
      data: updatedCategoryTree
    });
  });

  // 获取算子标签列表
  router.get(API.queryLabelsUsingGet, (req, res) => {
    const { page = 0, size = 20, keyword = "" } = req.query;
    
    let filteredLabels = labelList;
    
    if (keyword) {
      filteredLabels = labelList.filter(label =>
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
        number: parseInt(page)
      }
    });
  });

  // 创建标签
  router.post(API.createLabelUsingPost, (req, res) => {
    const { name } = req.body;
    
    const newLabel = {
      id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
      name,
      usageCount: 0,
      createdAt: new Date().toISOString()
    };
    
    labelList.push(newLabel);
    
    res.status(201).send({
      code: "0",
      msg: "Label created successfully",
      data: newLabel
    });
  });

  // 批量删除标签
  router.delete(API.deleteLabelsUsingDelete, (req, res) => {
    const labelIds = req.body; // 数组形式的标签ID列表
    
    let deletedCount = 0;
    labelIds.forEach(labelId => {
      const index = labelList.findIndex(label => label.id === labelId);
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
    
    updates.forEach(update => {
      const index = labelList.findIndex(label => label.id === update.id);
      if (index !== -1) {
        labelList[index] = {
          ...labelList[index],
          ...update,
          updatedAt: new Date().toISOString()
        };
      }
    });
    
    res.send({
      code: "0",
      msg: "Labels updated successfully",
      data: null
    });
  });
};