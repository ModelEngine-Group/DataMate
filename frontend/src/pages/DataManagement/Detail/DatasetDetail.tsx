import { useEffect, useState } from "react";
import { Card, Breadcrumb, Modal, App } from "antd";
import {
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  FileImageOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import DetailHeader from "@/components/DetailHeader";
import {
  mapDataset,
  datasetStatusMap,
  datasetSubTypeMap,
} from "../dataset.const";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import { Link, useParams } from "react-router";
import { useFilesOperation, useImportFile } from "../hooks";
import { downloadFile, queryDatasetByIdUsingGet } from "../dataset.api";
import DataQuality from "./components/DataQuality";
import DataLineageFlow from "./components/DataLineageFlow";
import Overview from "./components/Overview";
import { Activity, Clock, Dock, File, FileType } from "lucide-react";

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
  const [activeTab, setActiveTab] = useState("overview");
  const { message } = App.useApp();

  const [dataset, setDataset] = useState<Dataset>({} as Dataset);
  const { importFileRender, handleUpload } = useImportFile();
  const filesOperation = useFilesOperation(dataset);

  const [showUploadDialog, setShowUploadDialog] = useState(false);

  const fetchDataset = async () => {
    const { data } = await queryDatasetByIdUsingGet(id as unknown as number);
    setDataset(mapDataset(data));
  };

  useEffect(() => {
    fetchDataset();
    filesOperation.fetchFiles();
  }, []);

  const handleRefresh = async () => {
    fetchDataset();
    filesOperation.fetchFiles();
    message.success({ content: "数据刷新成功" });
  };

  const handleExportFormat = async ({ type }) => {
    await downloadFile(dataset.id, type, `${dataset.name}-${type}.txt`);
    message.success("文件下载成功");
  };

  // 基本信息描述项
  const statistics = [
    {
      icon: <File className="text-blue-500 w-4 h-4" />,
      label: "",
      value: dataset?.itemCount || 0,
    },
    {
      icon: <Activity className="text-purple-500 w-4 h-4" />,
      label: "",
      value: dataset?.size || "0 B",
    },
    {
      icon: <FileType className="text-green-500 w-4 h-4" />,
      label: "",
      value:
        datasetSubTypeMap[dataset?.type?.code as keyof typeof datasetSubTypeMap]
          ?.label || dataset?.type?.code,
    },
    {
      icon: <Clock className="text-orange-500 w-4 h-4" />,
      label: "",
      value: dataset?.createdAt,
    },
  ];

  // 数据集操作列表
  const operations = [
    {
      key: "refresh",
      label: "刷新",
      icon: <ReloadOutlined />,
      onClick: handleRefresh,
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

  return (
    <div className="min-h-screen flex flex-col gap-4">
      <Breadcrumb items={navigateItems} />
      {/* Header */}
      <DetailHeader
        data={dataset}
        statistics={statistics}
        operations={operations}
      />
      <Card
        tabList={tabList}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        {activeTab === "overview" && (
          <Overview dataset={dataset} filesOperation={filesOperation} />
        )}
        {activeTab === "lineage" && <DataLineageFlow dataset={dataset} />}
        {activeTab === "quality" && <DataQuality />}
      </Card>

      {/* Upload Dialog */}
      <Modal
        title="上传文件"
        open={showUploadDialog}
        onCancel={() => setShowUploadDialog(false)}
        onOk={async () => {
          await handleUpload(message, dataset);
          setShowUploadDialog(false);
          filesOperation.fetchFiles();
        }}
      >
        {importFileRender()}
      </Modal>
    </div>
  );
}
