import { useEffect, useState } from "react";
import {
  Button,
  App,
  Input,
  Select,
  Form,
  Modal,
  Steps,
  Empty,
  Checkbox,
  Pagination,
  Space,
} from "antd";
import { SearchOutlined, PlusOutlined } from "@ant-design/icons";
import { KnowledgeBaseItem } from "../knowledge-base.model";
import {
  queryDatasetFilesUsingGet,
  queryDatasetsUsingGet,
} from "@/pages/DataManagement/dataset.api";
import { datasetTypeMap } from "@/pages/DataManagement/dataset.const";
import { addKnowledgeBaseFilesUsingPost } from "../knowledge-base.api";
import { DatasetType } from "@/pages/DataManagement/dataset.model";

// 定义简单的FileInfo接口，确保与API兼容
interface FileInfo {
  id: string;
  name?: string;
  fileName?: string;
  size?: string;
  createdAt?: string;
}

const { Step } = Steps;

const sliceOptions = [
  { label: "默认分块", value: "DEFAULT_CHUNK" },
  { label: "章节分块", value: "CHAPTER_CHUNK" },
  { label: "段落分块", value: "PARAGRAPH_CHUNK" },
  { label: "长度分块", value: "LENGTH_CHUNK" },
  { label: "自定义分割符分块", value: "CUSTOM_SEPARATOR_CHUNK" },
];

export default function AddDataDialog({ knowledgeBase, onDataAdded }) {
  const [isOpen, setIsOpen] = useState(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  // 数据集相关状态
  const [datasets, setDatasets] = useState<any[]>([]);
  const [datasetsTotal, setDatasetsTotal] = useState(0);
  const [datasetPage, setDatasetPage] = useState(1);
  const [datasetSearch, setDatasetSearch] = useState('');
  const [datasetsLoading, setDatasetsLoading] = useState(false);
  // 文件相关状态
  const [datasetFiles, setDatasetFiles] = useState<any[]>([]);
  const [filesTotal, setFilesTotal] = useState(0);
  const [filesPage, setFilesPage] = useState(0);
  const [fileSearch, setFileSearch] = useState('knowledge-base/detail/');
  const [filesLoading, setFilesLoading] = useState(false);
  // 已选择的文件，格式：{datasetId: [fileIds]}
  const [selectedFilesMap, setSelectedFilesMap] = useState<Record<string, string[]>>({});
  // 当前正在查看的数据集
  const [activeDataset, setActiveDataset] = useState<any>(null);

  // 定义分块选项
  const sliceOptions = [
    { label: '默认分块', value: 'DEFAULT_CHUNK' },
    { label: '按章节分块', value: 'CHAPTER_CHUNK' },
    { label: '按段落分块', value: 'PARAGRAPH_CHUNK' },
    { label: '固定长度分块', value: 'FIXED_LENGTH_CHUNK' },
    { label: '自定义分隔符分块', value: 'CUSTOM_SEPARATOR_CHUNK' },
  ];
  
  // 定义初始状态
  const [newKB, setNewKB] = useState({
    processType: "DEFAULT_CHUNK",
    chunkSize: 500,
    overlapSize: 50,
    delimiter: '',
  });

  const steps = [
    {
      title: '选择数据集文件',
      description: '从多个数据集中选择文件',
    },
    {
      title: '配置参数',
      description: '设置数据处理参数',
    },
    {
      title: '确认上传',
      description: '确认信息并上传',
    },
  ];

  // 数据集列表每页大小
  const DATASET_PAGE_SIZE = 6;

  // 获取数据集列表（支持分页和搜索）
  const fetchDatasets = async (page = 1, search = '') => {
    setDatasetsLoading(true);
    try {
      const { data } = await queryDatasetsUsingGet({
        page: page,
        size: DATASET_PAGE_SIZE, // 每页大小通过接口传递
        type: DatasetType.TEXT,
        keyword: search || undefined, // 搜索参数
      });
      setDatasets(data.content || []);
      setDatasetsTotal(data.totalElements || 0);
    } catch (error) {
      message.error('获取数据集失败');
      console.error('获取数据集列表失败:', error);
    } finally {
      setDatasetsLoading(false);
    }
  };

  // 文件列表每页大小
  const FILES_PAGE_SIZE = 8;
  
  // 获取数据集文件列表（支持分页和搜索）
  const fetchDatasetFiles = async (datasetId, page = 0, search = '') => {
    if (!datasetId) return;

    setFilesLoading(true);
    try {
      const { data } = await queryDatasetFilesUsingGet(datasetId, {
        page: page, // 后端使用0-based页码
        size: FILES_PAGE_SIZE, // 每页最多8条数据
        keyword: search || undefined, // 搜索参数
      });
      
      // 确保数据格式正确
      if (data && Array.isArray(data.content)) {
        setDatasetFiles(data.content || []);
        setFilesTotal(data.totalElements || 0);
      } else {
        setDatasetFiles([]);
        setFilesTotal(0);
      }
    } catch (error) {
      message.error('获取数据集文件失败');
      console.error('获取文件列表失败:', error);
    } finally {
      setFilesLoading(false);
    }
  };

  // 初始化时加载数据集
  useEffect(() => {
    if (isOpen && currentStep === 0) {
      fetchDatasets(datasetPage, datasetSearch);
    }
  }, [isOpen, currentStep, datasetPage, datasetSearch]);

  // 切换数据集时加载对应文件（重置页码为0）
  useEffect(() => {
    if (activeDataset) {
      setFilesPage(0); // 重置页码
      fetchDatasetFiles(activeDataset.id, 0, fileSearch);
    }
  }, [activeDataset, fileSearch]);

  // 确保在文件搜索文本变化时重新加载文件
  useEffect(() => {
    if (activeDataset && fileSearch !== undefined) {
      setFilesPage(0);
      fetchDatasetFiles(activeDataset.id, 0, fileSearch);
    }
  }, [fileSearch, activeDataset]);

  // 当文件页码变化时重新加载文件
  useEffect(() => {
    if (activeDataset && filesPage >= 1) {
      fetchDatasetFiles(activeDataset.id, filesPage, fileSearch);
    }
  }, [filesPage]);

  // 处理数据集搜索
  const handleDatasetSearch = () => {
    setDatasetPage(1);
    fetchDatasets(1, datasetSearch);
  };

  // 处理文件搜索
  const handleFileSearch = (value) => {
    setFileSearch(value);
    setFilesPage(0);
    if (activeDataset) {
      fetchDatasetFiles(activeDataset.id, 0, value);
    }
  };

  // 处理数据集分页变化
  const handleDatasetPageChange = (page) => {
    setDatasetPage(page);
    fetchDatasets(page, datasetSearch);
  };

  // 处理文件分页变化
  const handleFilesPageChange = (page) => {
    setFilesPage(page);
    if (activeDataset) {
      fetchDatasetFiles(activeDataset.id, page, fileSearch);
    }
  };

  // 切换活动数据集
  const handleDatasetClick = (dataset) => {
    setActiveDataset(dataset);
  };

  // 已经在后面定义了handleFileSelect函数，删除重复定义

  // 处理全选/取消全选
  const handleSelectAll = (e) => {
    if (!activeDataset) return;
    
    const newSelectedFiles = e.target.checked 
      ? datasetFiles.map(file => file.id) 
      : [];
      
    setSelectedFilesMap(prev => ({
      ...prev,
      [activeDataset.id]: newSelectedFiles
    }));
  };

  // 检查文件是否已选择
  const isFileSelected = (fileId) => {
    if (!activeDataset) return false;
    return selectedFilesMap[activeDataset.id]?.includes(fileId) || false;
  };

  // 检查当前数据集是否全选
  const isAllSelected = () => {
    if (!activeDataset || datasetFiles.length === 0) return false;
    const selectedCount = selectedFilesMap[activeDataset.id]?.length || 0;
    return selectedCount === datasetFiles.length;
  };

  // 检查是否部分选择
  const isIndeterminate = () => {
    if (!activeDataset) return false;
    const selectedCount = selectedFilesMap[activeDataset.id]?.length || 0;
    return selectedCount > 0 && selectedCount < datasetFiles.length;
  };

  // 获取已选择文件总数
  const getSelectedFilesCount = () => {
    return Object.values(selectedFilesMap).reduce((total, ids) => total + ids.length, 0);
  };

  // 获取所有已选择的文件信息
  const getAllSelectedFiles = () => {
    const allFiles = [];
    for (const [datasetId, fileIds] of Object.entries(selectedFilesMap)) {
      // 找到对应的数据集
      const dataset = datasets.find(d => d.id === datasetId);
      // 获取文件详情并添加到数组
      if (dataset) {
        allFiles.push(...fileIds.map(fileId => ({
          id: fileId,
          name: `${dataset.name}/file_${fileId}` // 使用数据集名称作为前缀
        })));
      }
    }
    return allFiles;
  };

  const handleNext = () => {
    // 验证当前步骤
    if (currentStep === 0) {
      if (getSelectedFilesCount() === 0) {
        message.warning('请至少选择一个文件');
        return;
      }
    }
    if (currentStep === 1) {
      // 验证切片参数
      if (!newKB.processType) {
        message.warning('请选择分块方式');
        return;
      }
      if (!newKB.chunkSize || Number(newKB.chunkSize) <= 0) {
        message.warning('请输入有效的分块大小');
        return;
      }
      if (!newKB.overlapSize || Number(newKB.overlapSize) < 0) {
        message.warning('请输入有效的重叠长度');
        return;
      }
      if (newKB.processType === 'CUSTOM_SEPARATOR_CHUNK' && !newKB.delimiter) {
        message.warning('请输入分隔符');
        return;
      }
    }
    setCurrentStep(currentStep + 1);
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  // 重置所有状态
  const handleReset = () => {
    setCurrentStep(0);
    setSelectedFilesMap({});
    setNewKB({
      processType: 'DEFAULT_CHUNK',
      chunkSize: 500,
      overlapSize: 50,
      delimiter: '',
    });
    setDatasets([]);
    setDatasetPage(1);
    setDatasetSearch('');
    setDatasetFiles([]);
    setFilesPage(1);
    setFileSearch('');
    setActiveDataset(null);
    setLoadedFilesCache({}); // 清除文件缓存
    form.resetFields();
  };

  // 用于缓存已加载过的文件信息，避免重复请求
  const [loadedFilesCache, setLoadedFilesCache] = useState<Record<string, Record<string, any>>>({});
  
  // 优化处理文件选择（确保选择状态在分页切换后保持）
  const handleFileSelect = (checkedValues) => {
    if (!activeDataset) return;
    
    // 更新选择的文件
    setSelectedFilesMap(prev => ({
      ...prev,
      [activeDataset.id]: checkedValues
    }));
    
    // 缓存当前页面的文件信息
    if (datasetFiles.length > 0) {
      setLoadedFilesCache(prev => {
        const datasetCache = prev[activeDataset.id] || {};
        // 更新缓存中的文件信息
        datasetFiles.forEach(file => {
          datasetCache[file.id] = file;
        });
        return {
          ...prev,
          [activeDataset.id]: datasetCache
        };
      });
    }
  };

  // 当数据集文件加载完成后，缓存文件信息
  useEffect(() => {
    if (activeDataset && datasetFiles.length > 0) {
      setLoadedFilesCache(prev => {
        const datasetCache = prev[activeDataset.id] || {};
        datasetFiles.forEach(file => {
          datasetCache[file.id] = file;
        });
        return {
          ...prev,
          [activeDataset.id]: datasetCache
        };
      });
    }
  }, [activeDataset, datasetFiles]);

  const handleAddData = async () => {
    const selectedFiles = [];

      Object.entries(selectedFilesMap).forEach(([datasetId, fileIds]) => {
          fileIds.forEach(fileId => {
              // 查找文件信息以获取文件名
              const fileInfo = datasetFiles.find(file => file.id === fileId);
              // 根据API定义，需要id和name字段
              selectedFiles.push({
                id: fileId,
                name: fileInfo?.name || fileInfo?.fileName || `文件_${fileId}`
              });
          });
      });
    
    if (selectedFiles.length === 0) {
      message.warning('请至少选择一个文件');
      return;
    }
    
    try {
      // 构造符合API要求的请求数据
      const requestData = {
        files: selectedFiles,
        processType: newKB.processType,
        chunkSize: Number(newKB.chunkSize), // 确保是数字类型
        overlapSize: Number(newKB.overlapSize), // 确保是数字类型
        delimiter: newKB.delimiter,
      };
      
      await addKnowledgeBaseFilesUsingPost(knowledgeBase.id, requestData);
      
      // 先通知父组件刷新数据（确保刷新发生在重置前）
      onDataAdded?.();
      
      message.success('数据添加成功');
      // 重置状态
      handleReset();
      setIsOpen(false);
    } catch (error) {
      message.error('数据添加失败，请重试');
      console.error('添加文件失败:', error);
    }
  };

  // handleReset函数已在前面定义，删除重复定义

  const handleModalCancel = () => {
    handleReset();
    setIsOpen(false);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div className="text-lg font-medium">选择数据集文件</div>
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                请从左侧选择数据集，然后在右侧选择需要导入的文件。支持从多个不同数据集中交叉选择文件。
              </div>
              
              {getSelectedFilesCount() > 0 && (
                <div className="p-3 bg-blue-50 rounded-md text-blue-700">
                  已选择 {getSelectedFilesCount()} 个文件（来自 {Object.keys(selectedFilesMap).length} 个数据集）
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4 h-[500px]">
                {/* 左侧数据集列表（带搜索和分页） */}
                <div className="border rounded-lg flex flex-col h-full">
                  <div className="p-4 border-b">
                    <div className="font-medium mb-3">数据集列表</div>
                    <div className="relative">
                      <Input
                        placeholder="搜索数据集名称"
                        value={datasetSearch}
                        onChange={(e) => setDatasetSearch(e.target.value)}
                        onPressEnter={handleDatasetSearch}
                        prefix={<SearchOutlined />}
                        suffix={
                          <Button type="primary" size="small" onClick={handleDatasetSearch}>
                            搜索
                          </Button>
                        }
                      />
                    </div>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-4 max-h-[400px]">
                    {datasetsLoading ? (
                      <div className="flex justify-center items-center h-full">加载中...</div>
                    ) : datasets.length === 0 ? (
                      <Empty description="暂无可用数据集" />
                    ) : (
                      <div className="space-y-3">
                        {datasets.map(dataset => {
                          const isSelected = selectedFilesMap[dataset.id]?.length > 0;
                          return (
                            <div
                              key={dataset.id}
                              className={`p-3 rounded cursor-pointer transition-all border ${activeDataset?.id === dataset.id 
                                ? 'bg-blue-50 border-blue-300' 
                                : isSelected 
                                  ? 'border-blue-200 bg-blue-50/50' 
                                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}
                              onClick={() => handleDatasetClick(dataset)}
                            >
                              <div className="flex items-center gap-3">
                                <div className="font-medium">{dataset.name}</div>
                                <div className="text-sm text-gray-500">
                                  类型: {datasetTypeMap[dataset.datasetType]?.label || '未知'}
                                </div>
                                <div className="text-sm text-gray-500">
                                  文件数: {dataset.fileCount}
                                </div>
                              </div>
                              {isSelected && (
                                <div className="mt-1 text-xs text-blue-600">
                                  已选择 {selectedFilesMap[dataset.id].length} 个文件
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  
                  {/* 数据集分页 */}
                  <div className="p-3 border-t">
                    <Pagination
                      current={datasetPage}
                      total={datasetsTotal}
                      pageSize={DATASET_PAGE_SIZE}
                      onChange={handleDatasetPageChange}
                      showSizeChanger={false}
                      showQuickJumper
                      showTotal={(total) => `共 ${total} 个数据集`}
                      size="small"
                    />
                  </div>
                </div>

                {/* 右侧文件列表（带搜索和分页） */}
                <div className="border rounded-lg flex flex-col h-full">
                  <div className="p-4 border-b">
                    <div className="font-medium mb-3">
                      {activeDataset ? `${activeDataset.name} 的文件` : '文件列表'}
                    </div>
                    {activeDataset && (
                      <div className="relative">
                        <Input
                          placeholder="搜索文件名"
                          value={fileSearch}
                          onChange={(e) => setFileSearch(e.target.value)}
                          onPressEnter={handleFileSearch}
                          prefix={<SearchOutlined />}
                          suffix={
                            <Button type="primary" size="small" onClick={handleFileSearch}>
                              搜索
                            </Button>
                          }
                        />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-4 max-h-[400px]">
                    {!activeDataset ? (
                      <Empty description="请先选择数据集" />
                    ) : filesLoading ? (
                      <div className="flex justify-center items-center h-full">加载中...</div>
                    ) : datasetFiles.length === 0 ? (
                      <Empty description="该数据集暂无文件" />
                    ) : (
                      <div>
                        <div className="flex justify-between items-center mb-3">
                          <span className="text-sm text-gray-500">
                            每页显示 {Math.min(datasetFiles.length, FILES_PAGE_SIZE)} 条，共 {filesTotal} 条
                          </span>
                          <Checkbox 
                            checked={isAllSelected()}
                            onChange={handleSelectAll}
                            indeterminate={isIndeterminate()}
                          >
                            全选
                          </Checkbox>
                        </div>
                        
                        <Checkbox.Group 
                          value={selectedFilesMap[activeDataset.id] || []}
                          onChange={handleFileSelect}
                          className="w-full"
                        >
                          <div className="space-y-2">
                            {datasetFiles.map(file => (
                              <div key={file.id} className="p-2 rounded hover:bg-gray-50">
                                <Checkbox value={file.id}>
                                  <div className="truncate">{file.name || file.fileName}</div>
                                  <div className="text-xs text-gray-500">
                                    大小: {file.size || 'N/A'} | 创建时间: {file.createdAt ? new Date(file.createdAt).toLocaleString() : 'N/A'}
                                  </div>
                                </Checkbox>
                              </div>
                            ))}
                          </div>
                        </Checkbox.Group>
                      </div>
                    )}
                  </div>
                  
                  {/* 文件分页 */}
                  {activeDataset && (
                    <div className="p-3 border-t">
                      <Pagination
                        current={filesPage + 1} // 前端UI显示1-based页码
                        total={filesTotal}
                        pageSize={FILES_PAGE_SIZE}
                        onChange={(page) => handleFilesPageChange(page - 1)} // 转换为0-based页码
                        showSizeChanger={false}
                        showQuickJumper
                        showTotal={(total) => `共 ${total} 个文件`}
                        size="small"
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <Form.Item
              label="分块方式"
              name="processType"
              required
              rules={[{ required: true }]}
              onChange={(_, value) => setNewKB({ ...newKB, processType: value })}
            >
              <Select options={sliceOptions} />
            </Form.Item>

            <div className="grid grid-cols-2 gap-6">
              <Form.Item
                label="分块大小"
                name="chunkSize"
                rules={[
                  {
                    required: true,
                    message: "请输入分块大小",
                  },
                ]}
                onChange={(_, value) => setNewKB({ ...newKB, chunkSize: value })}
              >
                <Input type="number" placeholder="请输入分块大小" />
              </Form.Item>
              <Form.Item
                label="重叠长度"
                name="overlapSize"
                rules={[
                  {
                    required: true,
                    message: "请输入重叠长度",
                  },
                ]}
                onChange={(_, value) => setNewKB({ ...newKB, overlapSize: value })}
              >
                <Input type="number" placeholder="请输入重叠长度" />
              </Form.Item>
            </div>
            
            {newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && (
              <Form.Item
                label="分隔符"
                name="delimiter"
                rules={[
                  {
                    required: true,
                    message: "请输入分隔符",
                  },
                ]}
                onChange={(_, value) => setNewKB({ ...newKB, delimiter: value })}
              >
                <Input placeholder="输入分隔符，如 \n\n" />
              </Form.Item>
            )}
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-lg font-medium mb-3">上传信息确认</div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-gray-600">数据来源：</div>
                  <div className="col-span-2 font-medium">数据集</div>
                </div>
                
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-gray-600">选择的数据集数：</div>
                  <div className="col-span-2 font-medium">{Object.keys(selectedFilesMap).length}</div>
                </div>
                
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-gray-600">文件总数：</div>
                  <div className="col-span-2 font-medium">{getSelectedFilesCount()}</div>
                </div>
                
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-gray-600">分块方式：</div>
                  <div className="col-span-2 font-medium">
                    {sliceOptions.find(opt => opt.value === newKB.processType)?.label}
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-gray-600">分块大小：</div>
                  <div className="col-span-2 font-medium">{newKB.chunkSize}</div>
                </div>
                
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-gray-600">重叠长度：</div>
                  <div className="col-span-2 font-medium">{newKB.overlapSize}</div>
                </div>
                
                {newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && newKB.delimiter && (
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-gray-600">分隔符：</div>
                    <div className="col-span-2 font-medium font-mono">{newKB.delimiter}</div>
                  </div>
                )}
                
                {/* 显示每个数据集选择的文件数 */}
                {Object.keys(selectedFilesMap).length > 0 && (
                  <div>
                    <div className="text-gray-600 mb-2">数据集文件明细：</div>
                    <div className="border rounded-md p-3 bg-white">
                      {datasets.map(dataset => {
                        const selectedCount = selectedFilesMap[dataset.id]?.length || 0;
                        if (selectedCount === 0) return null;
                        return (
                          <div key={dataset.id} className="py-1">
                            <span className="font-medium">{dataset.name}：</span>
                            <span className="text-blue-600">{selectedCount} 个文件</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="text-sm text-yellow-600">
              提示：上传后系统将自动处理文件，请耐心等待
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={() => setIsOpen(true)}
      >
        添加数据
      </Button>
      <Modal
        title="添加数据"
        open={isOpen}
        onCancel={handleModalCancel}
        footer={null}
        width={1000}
      >
        <div>
          {/* 步骤导航 */}
            <Steps
              current={currentStep}
              onChange={(step) => setCurrentStep(step)}
              className="mb-6"
              items={steps}
            />
          
          {/* 步骤内容 */}
          <div className="p-2">
            <Form
              form={form}
              layout="vertical"
              initialValues={newKB}
              onValuesChange={(_, allValues) => setNewKB(allValues)}
            >
              {renderStepContent()}
            </Form>
          </div>
          
          {/* 底部按钮 */}
            <div className="flex justify-end gap-4 mt-6">
              {currentStep > 0 && (
                <Button onClick={handlePrev}>
                  上一步
                </Button>
              )}
              {currentStep < steps.length - 1 ? (
                <Button type="primary" onClick={handleNext}>
                  下一步
                </Button>
              ) : (
                <Button type="primary" onClick={handleAddData}>
                  确认上传
                </Button>
              )}
          </div>
        </div>
      </Modal>
    </>
  );
}