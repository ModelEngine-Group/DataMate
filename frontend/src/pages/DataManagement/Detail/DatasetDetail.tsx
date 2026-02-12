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
import { getDatasetTypeMap, mapDataset } from "../dataset.const";
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
import { useTranslation } from "react-i18next";

export default function DatasetDetail() {
  const { id } = useParams(); // 获取动态路由参数
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const { message } = App.useApp();
  const { t } = useTranslation();
  const datasetTypeMap = getDatasetTypeMap(t);
  const [showEditDialog, setShowEditDialog] = useState(false);

  const [dataset, setDataset] = useState<Dataset>({} as Dataset);
  const filesOperation = useFilesOperation(dataset);

  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const navigateItems = useMemo(
    () => [
      {
        title: <Link to="/data/management">{t("dataManagement.detail.breadcrumb")}</Link>,
      },
      {
        title: dataset.name || t("dataManagement.detail.title"),
      },
    ],
    [dataset, t]
  );
  const fetchDataset = async () => {
    const { data } = await queryDatasetByIdUsingGet(id as unknown as number);
    setDataset(mapDataset(data, t));
  };

  useEffect(() => {
    fetchDataset();
    filesOperation.fetchFiles('', 1, 10); // 从根目录开始，第一页
  }, []);

  const handleRefresh = async (showMessage = true, prefixOverride?: string) => {
    fetchDataset();
    // 刷新当前目录，保持在当前页
    const targetPrefix =
      prefixOverride !== undefined
        ? prefixOverride
        : filesOperation.pagination.prefix;
    filesOperation.fetchFiles(
      targetPrefix,
      filesOperation.pagination.current,
      filesOperation.pagination.pageSize
    );
    if (showMessage) {
      message.success({ content: t("dataManagement.messages.refreshSuccess") });
    }
  };

  const handleDownload = async () => {
    await downloadDatasetUsingGet(dataset.id);
    message.success(t("dataManagement.messages.fileDownloadSuccess"));
  };

  const handleDeleteDataset = async () => {
    await deleteDatasetByIdUsingDelete(dataset.id);
    navigate("/data/management");
    message.success(t("dataManagement.messages.deleteSuccess"));
  };

  useEffect(() => {
    const refreshData = (e: Event) => {
      const custom = e as CustomEvent<{ prefix?: string }>;
      const prefixOverride = custom.detail?.prefix;
      handleRefresh(false, prefixOverride);
    };
    window.addEventListener("update:dataset", refreshData as EventListener);
    return () => {
      window.removeEventListener(
        "update:dataset",
        refreshData as EventListener
      );
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
        t("dataManagement.defaults.unknown"),
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
      label: t("dataManagement.actions.edit"),
      icon: <EditOutlined />,
      onClick: () => {
        setShowEditDialog(true);
      },
    },

    {
      key: "upload",
      label: t("dataManagement.actions.importData"),
      icon: <UploadOutlined />,
      onClick: () => setShowUploadDialog(true),
    },
    {
      key: "export",
      label: t("dataManagement.actions.export"),
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
      label: t("dataManagement.actions.refresh"),
      icon: <ReloadOutlined />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: t("dataManagement.actions.delete"),
      danger: true,
      confirm: {
        title: t("dataManagement.confirm.deleteDatasetTitle"),
        description: t("dataManagement.confirm.deleteDatasetDesc"),
        okText: t("dataManagement.confirm.deleteConfirm"),
        cancelText: t("dataManagement.confirm.deleteCancel"),
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDeleteDataset,
    },
  ];

  const tabList = [
    {
      key: "overview",
      label: t("dataManagement.detail.tabOverview"),
    },
    {
      key: "lineage",
      label: t("dataManagement.detail.tabLineage"),
    },
    {
      key: "quality",
      label: t("dataManagement.detail.tabQuality"),
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
            <Overview dataset={dataset} filesOperation={filesOperation} fetchDataset={fetchDataset}/>
          )}
          {activeTab === "lineage" && <DataLineageFlow dataset={dataset} />}
          {activeTab === "quality" && <DataQuality dataset={dataset} />}
        </div>
      </div>
      <ImportConfiguration
        data={dataset}
        open={showUploadDialog}
        onClose={() => setShowUploadDialog(false)}
        prefix={filesOperation.pagination.prefix}
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
