import { Card, Button, Statistic, Table, Tooltip, Tag, App } from "antd";
import {
  DownloadOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import TagManager from "@/components/business/TagManagement";
import { Link, useNavigate } from "react-router";
import { useEffect, useMemo, useState } from "react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import { getDatasetStatusMap, getDatasetTypeMap, mapDataset } from "../dataset.const";
import useFetchData from "@/hooks/useFetchData";
import {
  downloadDatasetUsingGet,
  getDatasetStatisticsUsingGet,
  queryDatasetsUsingGet,
  deleteDatasetByIdUsingDelete,
  createDatasetTagUsingPost,
  queryDatasetTagsUsingGet,
  deleteDatasetTagUsingDelete,
  updateDatasetTagUsingPut,
} from "../dataset.api";
import { formatBytes } from "@/utils/unit";
import EditDataset from "../Create/EditDataset";
import ImportConfiguration from "../Detail/components/ImportConfiguration";
import { useTranslation } from "react-i18next";

export default function DatasetManagementPage() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { t } = useTranslation();
  const datasetStatusMap = getDatasetStatusMap(t);
  const datasetTypeMap = getDatasetTypeMap(t);
  const [viewMode, setViewMode] = useState<"card" | "list">("card");
  const [editDatasetOpen, setEditDatasetOpen] = useState(false);
  const [currentDataset, setCurrentDataset] = useState<Dataset | null>(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [statisticsData, setStatisticsData] = useState<any>({
    count: {},
    size: {},
  });

  async function fetchStatistics() {
    const { data } = await getDatasetStatisticsUsingGet();

    const statistics = {
      size: [
        {
          title: t("dataManagement.stats.totalDatasets"),
          value: data?.totalDatasets || 0,
        },
        {
          title: t("dataManagement.stats.totalFiles"),
          value: data?.totalFiles || 0,
        },
        {
          title: t("dataManagement.stats.totalSize"),
          value: formatBytes(data?.totalSize) || '0 B',
        },
      ],
      count: [
        {
          title: t("dataManagement.stats.text"),
          value: data?.count?.text || 0,
        },
        {
          title: t("dataManagement.stats.image"),
          value: data?.count?.image || 0,
        },
        {
          title: t("dataManagement.stats.audio"),
          value: data?.count?.audio || 0,
        },
        {
          title: t("dataManagement.stats.video"),
          value: data?.count?.video || 0,
        },
      ],
    };
    setStatisticsData(statistics);
  }

  const [tags, setTags] = useState<string[]>([]);

  const filterOptions = useMemo(
    () => [
      {
        key: "type",
        label: t("dataManagement.filters.type"),
        options: [...Object.values(datasetTypeMap)],
      },
      {
        key: "status",
        label: t("dataManagement.filters.status"),
        options: [...Object.values(datasetStatusMap)],
      },
      {
        key: "tags",
        label: t("dataManagement.filters.tags"),
        mode: "multiple",
        options: tags.map((tag) => ({ label: tag, value: tag })),
      },
    ],
    [tags, datasetStatusMap, datasetTypeMap, t]
  );

  const {
    loading,
    tableData,
    searchParams,
    pagination,
    fetchData,
    setSearchParams,
    handleFiltersChange,
    handleKeywordChange,
  } = useFetchData<Dataset>(
    queryDatasetsUsingGet,
    (dataset) => mapDataset(dataset, t),
    30000, // 30秒轮询间隔
    true, // 自动刷新
    [fetchStatistics], // 额外的轮询函数
    0
  );

  useEffect(() => {
    const fetchTags = async () => {
      const { data } = await queryDatasetTagsUsingGet();
      setTags(data.map((tag) => tag.name));
    };
    fetchTags();
    fetchData();
    fetchStatistics();
  }, [t]);

  const handleDownloadDataset = async (dataset: Dataset) => {
    await downloadDatasetUsingGet(dataset.id);
    message.success(t("dataManagement.messages.downloadSuccess"));
  };

  const handleDeleteDataset = async (id: number) => {
    if (!id) return;
    await deleteDatasetByIdUsingDelete(id);
    fetchData({ pageOffset: 0 });
    message.success(t("dataManagement.messages.deleteSuccess"));
  };

  const handleImportData = (dataset: Dataset) => {
    setCurrentDataset(dataset);
    setShowUploadDialog(true);
  };

  const handleRefresh = async (showMessage = true) => {
    await fetchData({ pageOffset: 0 });
    if (showMessage) {
      message.success(t("dataManagement.messages.refreshSuccess"));
    }
  };

  const operations = [
    {
      key: "edit",
      label: t("dataManagement.actions.edit"),
      icon: <EditOutlined />,
      onClick: (item: Dataset) => {
        setCurrentDataset(item);
        setEditDatasetOpen(true);
      },
    },
    {
      key: "import",
      label: t("dataManagement.actions.import"),
      icon: <UploadOutlined />,
      onClick: (item: Dataset) => {
        handleImportData(item);
      },
    },
    {
      key: "download",
      label: t("dataManagement.actions.download"),
      icon: <DownloadOutlined />,
      onClick: (item: Dataset) => {
        if (!item.id) return;
        handleDownloadDataset(item);
      },
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
      onClick: (item: Dataset) => handleDeleteDataset(item.id),
    },
  ];

  const columns = [
    {
      title: t("dataManagement.columns.name"),
      dataIndex: "name",
      key: "name",
      fixed: "left",
      render: (name, record) => (
        <Button
          type="link"
          onClick={() => navigate(`/data/management/detail/${record.id}`)}
        >
          {name}
        </Button>
      ),
    },
    {
      title: t("dataManagement.columns.type"),
      dataIndex: "type",
      key: "type",
      width: 100,
    },
    {
      title: t("dataManagement.columns.status"),
      dataIndex: "status",
      key: "status",
      render: (status: any) => {
        return (
          <Tag icon={status?.icon} color={status?.color}>
            {status?.label}
          </Tag>
        );
      },
      width: 120,
    },
    {
      title: t("dataManagement.columns.size"),
      dataIndex: "size",
      key: "size",
      width: 120,
    },
    {
      title: t("dataManagement.columns.fileCount"),
      dataIndex: "fileCount",
      key: "fileCount",
      width: 100,
    },
    {
      title: t("dataManagement.columns.storagePath"),
      dataIndex: "targetLocation",
      key: "targetLocation",
      width: 200,
      ellipsis: true,
    },
    {
      title: t("dataManagement.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
    },
    {
      title: t("dataManagement.columns.updatedAt"),
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 180,
    },
    {
      title: t("dataManagement.columns.actions"),
      key: "actions",
      width: 200,
      fixed: "right",
      render: (_: any, record: Dataset) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                onClick={() => op.onClick(record)}
              />
            </Tooltip>
          ))}
        </div>
      ),
    },
  ];

  const renderCardView = () => (
    <CardView
      loading={loading}
      data={tableData}
      operations={operations}
      pagination={pagination}
      onView={(dataset) => {
        navigate("/data/management/detail/" + dataset.id);
      }}
    />
  );

  const renderListView = () => (
    <Card>
      <Table
        columns={columns}
        dataSource={tableData}
        pagination={pagination}
        rowKey="id"
        scroll={{ x: "max-content", y: "calc(100vh - 30rem)" }}
      />
    </Card>
  );

  useEffect(() => {
    const refresh = () => {
      handleRefresh(true);
    };
    window.addEventListener("update:datasets", refresh);
    return () => {
      window.removeEventListener("update:datasets", refresh);
    };
  }, []);

  return (
    <div className="gap-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("dataManagement.title")}</h1>
        <div className="flex gap-2 items-center">
          {/* tasks */}
          <TagManager
            onCreate={createDatasetTagUsingPost}
            onDelete={(ids: string) => deleteDatasetTagUsingDelete({ ids })}
            onUpdate={updateDatasetTagUsingPut}
            onFetch={queryDatasetTagsUsingGet}
          />
          <Link to="/data/management/create">
            <Button
              type="primary"
              icon={<PlusOutlined className="w-4 h-4 mr-2" />}
            >
              {t("dataManagement.actions.createDataset")}
            </Button>
          </Link>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-4">
        <Card>
          <div className="grid grid-cols-3">
            {statisticsData.size?.map?.((item) => (
              <Statistic
                title={item.title}
                key={item.title}
                value={`${item.value}`}
              />
            ))}
          </div>
        </Card>
      </div>
      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={handleKeywordChange}
        searchPlaceholder={t("dataManagement.search.placeholder")}
        filters={filterOptions}
        onFiltersChange={handleFiltersChange}
        onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle
        onReload={handleRefresh}
      />
      {viewMode === "card" ? renderCardView() : renderListView()}
      <EditDataset
        open={editDatasetOpen}
        data={currentDataset}
        onClose={() => {
          setCurrentDataset(null);
          setEditDatasetOpen(false);
        }}
        onRefresh={handleRefresh}
      />
      <ImportConfiguration
        data={currentDataset}
        open={showUploadDialog}
        onClose={() => {
          setCurrentDataset(null);
          setShowUploadDialog(false);
        }}
        prefix=""
        updateEvent="update:datasets"
      />
    </div>
  );
}
