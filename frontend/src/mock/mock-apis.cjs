const { addMockPrefix } = require("./mock-core/util.cjs");

const MockAPI = {
    // 数据管理接口
    queryDatasetsUsingGet: '/datasets', // 获取数据集列表
    createDatasetUsingPost: '/datasets/create', // 创建数据集
    getDatasetByIdUsingGet: '/datasets/:id', // 根据ID获取数据集详情
    updateDatasetByIdUsingPut: '/datasets/:id', // 更新数据集
    deleteDatasetByIdUsingDelete: '/datasets/:id', // 删除数据集
    queryDatasetFilesUsingGet: '/datasets/:id/files', // 获取数据集文件列表
    addDatasetFileUsingPost: '/datasets/:id/files', // 添加数据集文件
    getDatasetFileByIdUsingGet: '/datasets/:id/files/:fileId', // 获取数据集文件详情
    deleteDatasetFileByIdUsingDelete: '/datasets/:id/files/:fileId', // 删除数据集文件
    downloadFileByIdUsingGet: '/datasets/:id/files/:fileId/download', // 下载文件
    queryDatasetTypesUsingGet: '/dataset-types', // 获取数据集类型列表
    queryDatasetTagsUsingGet: '/tags', // 获取数据集标签列表
    createDatasetTagsUsingPost: '/tags', // 创建数据集标签
    getDatasetStatisticsUsingGet: '/datasets/statistics', // 获取数据集统计信息
   
    // 数据清洗接口
};

module.exports = addMockPrefix('/api', MockAPI);