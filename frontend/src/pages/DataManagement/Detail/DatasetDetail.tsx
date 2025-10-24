import { useEffect, useMemo, useState } from "react";
import { Breadcrumb, App, Tabs } from "antd";
import {
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import DetailHeader from "@/components/DetailHeader";
import { mapDataset, datasetTypeMap } from "../dataset.const";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import { Link, useNavigate, useParams } from "react-router";
import { useFilesOperation } from "./useFilesOperation";
import {
  createDatasetTagUsingPost,
  deleteDatasetByIdUsingDelete,
  downloadDatasetUsingGet,
  queryDatasetByIdUsingGet,
  queryDatasetTagsUsingGet,
  updateDatasetByIdUsingPut,
} from "../dataset.api";
import DataQuality from "./components/DataQuality";
import DataLineageFlow from "./components/DataLineageFlow";
import Overview from "./components/Overview";
import { Activity, Clock, File, FileType } from "lucide-react";
import EditDataset from "../Create/EditDataset";
import ImportConfiguration from "./components/ImportConfiguration";

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
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const { message } = App.useApp();
  const [showEditDialog, setShowEditDialog] = useState(false);

  const [dataset, setDataset] = useState<Dataset>({} as Dataset);
  const filesOperation = useFilesOperation(dataset);

  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const navigateItems = useMemo(
    () => [
      {
        title: <Link to="/data/management">数据管理</Link>,
      },
      {
        title: dataset.name || "数据集详情",
      },
    ],
    [dataset]
  );
  const fetchDataset = async () => {
    const { data } = await queryDatasetByIdUsingGet(id as unknown as number);
    setDataset(mapDataset(data));
  };

  useEffect(() => {
    fetchDataset();
    filesOperation.fetchFiles();
  }, []);

  const handleRefresh = async (showMessage = true) => {
    fetchDataset();
    filesOperation.fetchFiles();
    if (showMessage) message.success({ content: "数据刷新成功" });
  };

  const handleDownload = async () => {
    await downloadDatasetUsingGet(dataset.id);
    message.success("文件下载成功");
  };

  const handleDeleteDataset = async () => {
    await deleteDatasetByIdUsingDelete(dataset.id);
    navigate("/data/management");
    message.success("数据集删除成功");
  };

  useEffect(() => {
    const refreshDataset = () => {
      fetchDataset();
    };
    const refreshData = () => {
      handleRefresh(false);
    };
    window.addEventListener("update:dataset", refreshData);
    window.addEventListener("update:dataset-status", () => refreshDataset());
    return () => {
      window.removeEventListener("update:dataset", refreshData);
      window.removeEventListener("update:dataset-status", refreshDataset);
    };
  }, []);

  // 基本信息描述项
  const statistics = [
    {
      icon: <File className="text-blue-400 w-4 h-4" />,
      key: "file",
      value: dataset?.fileCount || 0,
    },
    {
      icon: <Activity className="text-blue-400 w-4 h-4" />,
      key: "size",
      value: dataset?.size || "0 B",
    },
    {
      icon: <FileType className="text-blue-400 w-4 h-4" />,
      key: "type",
      value:
        datasetTypeMap[dataset?.datasetType as keyof typeof datasetTypeMap]
          ?.label ||
        dataset?.type ||
        "未知",
    },
    {
      icon: <Clock className="text-blue-400 w-4 h-4" />,
      key: "time",
      value: dataset?.updatedAt,
    },
  ];

  // 数据集操作列表
  const operations = [
    {
      key: "edit",
      label: "编辑",
      icon: <EditOutlined />,
      onClick: () => {
        setShowEditDialog(true);
      },
    },

    {
      key: "upload",
      label: "导入数据",
      icon: <UploadOutlined />,
      onClick: () => setShowUploadDialog(true),
    },
    {
      key: "export",
      label: "导出",
      icon: <DownloadOutlined />,
      // isDropdown: true,
      // items: [
      //   { key: "alpaca", label: "Alpaca 格式", icon: <FileTextOutlined /> },
      //   { key: "jsonl", label: "JSONL 格式", icon: <DatabaseOutlined /> },
      //   { key: "csv", label: "CSV 格式", icon: <FileTextOutlined /> },
      //   { key: "coco", label: "COCO 格式", icon: <FileImageOutlined /> },
      // ],
      onClick: () => handleDownload(),
    },
    {
      key: "refresh",
      label: "刷新",
      icon: <ReloadOutlined />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: "删除",
      danger: true,
      confirm: {
        title: "确认删除该数据集？",
        description: "删除后该数据集将无法恢复，请谨慎操作。",
        okText: "删除",
        cancelText: "取消",
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDeleteDataset,
    },
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <Breadcrumb items={navigateItems} />
      {/* Header */}
      <DetailHeader
        data={dataset}
        statistics={statistics}
        operations={operations}
        tagConfig={{
          showAdd: true,
          tags: dataset.tags || [],
          onFetchTags: async () => {
            const res = await queryDatasetTagsUsingGet({
              page: 0,
              pageSize: 1000,
            });
            return res.data || [];
          },
          onCreateAndTag: async (tagName) => {
            const res = await createDatasetTagUsingPost({ name: tagName });
            if (res.data) {
              await updateDatasetByIdUsingPut(dataset.id, {
                tags: [...dataset.tags.map((tag) => tag.name), res.data.name],
              });
              handleRefresh();
            }
          },
          onAddTag: async (tag) => {
            const res = await updateDatasetByIdUsingPut(dataset.id, {
              tags: [...dataset.tags.map((tag) => tag.name), tag],
            });
            if (res.data) {
              handleRefresh();
            }
          },
        }}
      />
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full overflow-auto">
          {activeTab === "overview" && (
            <Overview dataset={dataset} filesOperation={filesOperation} />
          )}
          {activeTab === "lineage" && <DataLineageFlow dataset={dataset} />}
          {activeTab === "quality" && <DataQuality />}
        </div>
      </div>
      <ImportConfiguration
        data={dataset}
        open={showUploadDialog}
        onClose={() => setShowUploadDialog(false)}
        updateEvent="update:dataset"
      />
      <EditDataset
        data={dataset}
        open={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        onRefresh={handleRefresh}
      />
    </div>
  );
}
