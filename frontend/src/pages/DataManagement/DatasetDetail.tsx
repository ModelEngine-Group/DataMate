import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Table,
  Breadcrumb,
  Descriptions,
  Tag,
  message,
  Modal,
} from "antd";
import {
  StarOutlined,
  ReloadOutlined,
  FlagOutlined,
  DownloadOutlined,
  UploadOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  FileImageOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import {
  getStatusBadge,
  mockDatasets,
  mockFiles,
  mockTags,
} from "@/mock/dataset";
import {
  AlertTriangle,
  Database,
  Download,
  FileText,
  GitBranch,
  Target,
  Trash2,
} from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import { TypeMap } from "./model";
import type { Dataset } from "@/types/dataset";
import { Link, useParams } from "react-router";
import { useImportFile } from "./hooks/useImportFile";

const navigateItems = [
  {
    title: <Link to="/data/management">数据管理</Link>,
  },
  {
    title: "数据集详情",
  },
];

const tabList = [
  {
    key: "overview",
    label: "概览",
  },
  {
    key: "lineage",
    label: "数据血缘",
  },
  {
    key: "quality",
    label: "数据质量",
  },
];

export default function DatasetDetail() {
  const { id } = useParams(); // 获取动态路由参数
  const [messageApi, contextHolder] = message.useMessage();
  const [activeTab, setActiveTab] = useState("overview");

  const [dataset, setDataset] = useState<Dataset>(mockDatasets[0]);
  const { importFileRender, handleUpload } = useImportFile(messageApi, dataset);

  // 模拟数据集详情

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  // 文件相关状态
  const [fileList, setFileList] = useState(mockFiles);
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);

  // 标签相关状态
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");
  const [showAddTagPopover, setShowAddTagPopover] = useState(false);
  const [showDetailAddTagPopover, setShowDetailAddTagPopover] = useState(false);
  const [detailNewTag, setDetailNewTag] = useState("");
  const [availableTags, setAvailableTags] = useState<string[]>(mockTags);

  // 文件预览相关状态
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState("");
  const [previewFileName, setPreviewFileName] = useState("");

  const getDatasetDetail = async () => {
    const res = await fetch(`/api/dataset/v2/${id}`);
    setDataset(await res.json());
  };

  const getFiles = async () => {
    const res = await fetch(`/api/dataset/v2/${id}/files`);
    setFileList(await res.json());
  };

  useEffect(() => {
    // getDatasetDetail();
    // getFiles();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // 模拟刷新
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsRefreshing(false);
  };

  const handleExportFormat = ({ key }) => {
    console.log(`导出为 ${key} 格式`);
    // 实际导出逻辑
  };

  const handleCreateNewTag = () => {
    if (newTag.trim() && !availableTags.includes(newTag.trim())) {
      setAvailableTags([...availableTags, newTag.trim()]);
      setNewTag("");
      setShowAddTagPopover(false);
    }
  };

  const handleEditTag = (oldTag: string, newTag: string) => {
    if (newTag.trim() && newTag !== oldTag) {
      // 更新可用标签列表
      setAvailableTags(
        availableTags.map((tag) => (tag === oldTag ? newTag.trim() : tag))
      );
      // 更新所有数据集中的标签
    }
    setEditingTag(null);
    setEditingTagValue("");
  };

  const handleDeleteTag = (tagToDelete: string) => {
    // 从可用标签中删除
    setAvailableTags(availableTags.filter((tag) => tag !== tagToDelete));
    // 从所有数据集中删除该标签
  };

  const handleAddTagToDataset = (datasetId: number, tag: string) => {
    // Update selected dataset if it's currently selected
  };

  const handleCreateAndAddTag = (datasetId: number) => {
    if (detailNewTag.trim() && !availableTags.includes(detailNewTag.trim())) {
      setAvailableTags([...availableTags, detailNewTag.trim()]);
    }
    if (detailNewTag.trim()) {
      handleAddTagToDataset(datasetId, detailNewTag.trim());
      setDetailNewTag("");
    }
  };

  const handleBatchDelete = () => {
    if (selectedFiles.length === 0) {
      messageApi.open({ type: "warning", content: "请先选择要删除的文件" });
      return;
    }
    // 执行批量删除逻辑
    setSelectedFiles([]);
    messageApi.open({
      type: "success",
      content: `已删除 ${selectedFiles.length} 个文件`,
    });
  };

  const handleBatchExport = () => {
    console.log("批量导出文件:", selectedFiles);
    // 实际导出逻辑
  };

  const handleShowFile = (file: any) => async () => {
    // 请求文件内容并弹窗预览
    try {
      const res = await fetch(`/api/dataset/v2/file/${file.id}`);
      const data = await res.text();
      setPreviewFileName(file.name);
      setPreviewContent(data);
      setPreviewVisible(true);
    } catch (err) {
      messageApi.open({ type: "error", content: "文件预览失败" });
    }
  };

  // 文件列表多选配置
  const rowSelection = {
    onChange: (selectedRowKeys: React.Key[], selectedRows: any[]) => {
      setSelectedFiles(selectedRowKeys as number[]);
      console.log(
        `selectedRowKeys: ${selectedRowKeys}`,
        "selectedRows: ",
        selectedRows
      );
    },
  };

  // 基本信息描述项
  const statistics = [
    {
      icon: <FileTextOutlined className="text-blue-500" />,
      label: "数据项",
      value: dataset.itemCount || 0,
    },
    {
      icon: <DatabaseOutlined className="text-green-500" />,
      label: "大小",
      value: dataset.size || "0 B",
    },
    {
      icon: <FileImageOutlined className="text-purple-500" />,
      label: "类型",
      value:
        TypeMap[dataset.type as keyof typeof TypeMap]?.label || dataset.type,
    },
    {
      icon: <ClockCircleOutlined className="text-grey-500" />,
      label: "",
      value: dataset.lastModified
        ? new Date(dataset.lastModified).toLocaleDateString()
        : "未知",
    },
  ];

  // 操作列表
  const operations = [
    {
      key: "star",
      label: "收藏",
      icon: <StarOutlined />,
      onClick: () => {},
    },
    {
      key: "refresh",
      label: "刷新",
      icon: <ReloadOutlined />,
      onClick: handleRefresh,
    },
    {
      key: "publish",
      label: "发布",
      icon: <FlagOutlined />,
      onClick: () => {},
    },
    {
      key: "upload",
      label: "上传文件",
      icon: <UploadOutlined />,
      onClick: () => setShowUploadDialog(true),
    },
    {
      key: "export",
      label: "导出",
      icon: <DownloadOutlined />,
      isDropdown: true,
      items: [
        { key: "alpaca", label: "Alpaca 格式", icon: <FileTextOutlined /> },
        { key: "jsonl", label: "JSONL 格式", icon: <DatabaseOutlined /> },
        { key: "csv", label: "CSV 格式", icon: <FileTextOutlined /> },
        { key: "coco", label: "COCO 格式", icon: <FileImageOutlined /> },
      ],
      onMenuClick: handleExportFormat,
    },
  ];

  // 基本信息
  const items: DescriptionsProps["items"] = [
    {
      key: "importMethod",
      label: "导入方式",
      children: "本地上传",
    },
    {
      key: "createdBy",
      label: "创建者",
      children: "admin",
    },
    {
      key: "createdTime",
      label: "创建时间",
      children: "2025-01-15 10:30:00",
    },
  ];

  // 文件列表列定义
  const columns = [
    {
      title: "文件名",
      dataIndex: "name",
      key: "name",
      render: (text, file) => (
        <Button type="link" onClick={handleShowFile(file)}>
          {text}
        </Button>
      ),
    },
    {
      title: "大小",
      dataIndex: "size",
      key: "size",
      sorter: (a, b) => {
        const sizeA = parseFloat(a.size.replace("MB", "").replace("KB", ""));
        const sizeB = parseFloat(b.size.replace("MB", "").replace("KB", ""));
        return sizeA - sizeB;
      },
    },
    {
      title: "上传时间",
      dataIndex: "uploadedAt",
      key: "uploadedAt",
      sorter: (a, b) =>
        new Date(a.uploadedAt).getTime() - new Date(b.uploadedAt).getTime(),
    },
    {
      title: "操作",
      key: "action",
      render: (_, record) => (
        <div>
          <Button type="link">下载</Button>
          <Button
            type="link"
            onClick={async () => {
              await fetch(`/api/dataset/v2/file/${record.id}`, {
                method: "DELETE",
              });
              messageApi.open({
                type: "success",
                content: `文件 ${record.name} 已删除`,
              });
            }}
          >
            删除
          </Button>
        </div>
      ),
    },
  ];

  const renderOverviewTab = () => (
    <div className=" flex flex-col gap-4">
      {/* 基本信息 */}
      <Card>
        <Descriptions title="基本信息" items={items} column={2} />
      </Card>
      {/* 标签 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">标签</h3>
        <div className="flex flex-wrap gap-2">
          {dataset.tags?.map((tag, index) => (
            <Tag
              key={index}
              className="px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full"
            >
              {tag}
            </Tag>
          ))}
        </div>
      </Card>
      <Card>
        <div className="flex justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">文件列表</h3>
          <Button
            onClick={handleBatchDelete}
            danger
            disabled={!selectedFiles.length}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            批量删除
          </Button>
        </div>
        {selectedFiles.length > 0 && (
          <div className="flex items-center gap-2 mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <span className="text-sm text-blue-700 font-medium">
              已选择 {selectedFiles.length} 个文件
            </span>
            <Button
              onClick={handleBatchExport}
              className="ml-auto bg-transparent"
            >
              <Download className="w-4 h-4 mr-2" />
              批量导出
            </Button>
            <Button
              onClick={handleBatchDelete}
              className="text-red-600 hover:text-red-700 hover:bg-red-50 bg-transparent"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              批量删除
            </Button>
          </div>
        )}
        <div className="overflow-x-auto">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={fileList}
            rowSelection={rowSelection}
          />
        </div>
        {fileList.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>没有找到匹配的文件</p>
          </div>
        )}
      </Card>
    </div>
  );

  const renderLineageFlow = (lineage: Dataset["lineage"]) => {
    if (!lineage) return null;

    const steps = [
      { name: "数据源", value: lineage.source, icon: Database },
      ...lineage.processing.map((step, index) => ({
        name: `处理${index + 1}`,
        value: step,
        icon: GitBranch,
      })),
    ];

    if (lineage.training) {
      steps.push({
        name: "模型训练",
        value: `${lineage.training.model} (准确率: ${lineage.training.accuracy}%)`,
        icon: Target,
      });
    }

    return (
      <div className="space-y-4">
        <div className="relative">
          {steps.map((step, index) => (
            <div key={index} className="flex items-start gap-4 pb-8 last:pb-0">
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                  <step.icon className="w-6 h-6 text-white" />
                </div>
                {index < steps.length - 1 && (
                  <div className="w-0.5 h-12 bg-gradient-to-b from-blue-200 to-indigo-200 mt-2"></div>
                )}
              </div>
              <div className="flex-1 pt-3">
                <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                  <h5 className="font-semibold text-gray-900 mb-1">
                    {step.name}
                  </h5>
                  <p className="text-sm text-gray-600">{step.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderDataQualityTab = () => (
    <div className=" mt-0">
      <div className="grid md:grid-cols-2 gap-6">
        <Card title="质量分布">
          {[
            { metric: "图像清晰度", value: 96.2, color: "bg-green-500" },
            { metric: "色彩一致性", value: 94.8, color: "bg-blue-500" },
            { metric: "标注完整性", value: 98.1, color: "bg-purple-500" },
          ].map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.metric}</span>
                <span className="font-semibold">{item.value}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${item.color} h-3 rounded-full transition-all duration-500`}
                  style={{ width: `${item.value}%` }}
                ></div>
              </div>
            </div>
          ))}
        </Card>

        <Card title="数据完整性">
          {[
            { metric: "文件完整性", value: 99.7, color: "bg-green-500" },
            { metric: "元数据完整性", value: 97.3, color: "bg-blue-500" },
            { metric: "标签一致性", value: 95.6, color: "bg-purple-500" },
          ].map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.metric}</span>
                <span className="font-semibold">{item.value}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${item.color} h-3 rounded-full transition-all duration-500`}
                  style={{ width: `${item.value}%` }}
                ></div>
              </div>
            </div>
          ))}
        </Card>
      </div>

      <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-yellow-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-yellow-800 mb-2">质量改进建议</h4>
            <ul className="text-sm text-yellow-700 space-y-2">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                建议对42张图像进行重新标注以提高准确性
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                检查并补充缺失的病理分级信息
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                考虑增加更多低分化样本以平衡数据分布
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col gap-4">
      {contextHolder}
      <Breadcrumb items={navigateItems} />
      {/* Header */}
      <DetailHeader
        data={{
          ...dataset,
          status: getStatusBadge(dataset.status),
        }}
        statistics={statistics}
        operations={operations}
      />
      <Card
        tabList={tabList}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        <div className="">
          {activeTab === "overview" && renderOverviewTab()}
          {activeTab === "lineage" && renderLineageFlow(dataset.lineage)}
          {activeTab === "quality" && renderDataQualityTab()}
        </div>
      </Card>

      {/* 文件预览弹窗 */}
      <Modal
        title={`文件预览：${previewFileName}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={700}
      >
        <pre
          style={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
            fontSize: 14,
            color: "#222",
          }}
        >
          {previewContent}
        </pre>
      </Modal>

      {/* Upload Dialog */}
      <Modal
        title="上传文件"
        open={showUploadDialog}
        onCancel={() => setShowUploadDialog(false)}
        onOk={handleUpload}
      >
        {importFileRender()}
      </Modal>
    </div>
  );
}
