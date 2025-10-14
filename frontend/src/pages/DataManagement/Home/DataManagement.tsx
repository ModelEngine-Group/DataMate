import { Card, Button, Statistic, Table, Tooltip, Tag, App } from "antd";
import {
  DownloadOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import TagManager from "@/components/TagManagement";
import { Link, useNavigate } from "react-router";
import { useEffect, useState } from "react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import { datasetStatusMap, datasetTypeMap, mapDataset } from "../dataset.const";
import useFetchData from "@/hooks/useFetchData";
import {
  downloadDatasetUsingGet,
  getDatasetStatisticsUsingGet,
  queryDatasetsUsingGet,
  deleteDatasetByIdUsingDelete,
  createDatasetTagUsingPost,
  queryDatasetTagsUsingGet,
  updateDatasetTagByIdUsingPut,
  deleteDatasetTagByIdUsingDelete,
} from "../dataset.api";
import { formatBytes } from "@/utils/unit";

export default function DatasetManagementPage() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");

  const [statisticsData, setStatisticsData] = useState<any>({
    count: {},
    size: {},
  });

  async function fetchStatistics() {
    const { data } = await getDatasetStatisticsUsingGet();

    const statistics = {
      size: [
        {
          title: "总计",
          value: data?.totalDatasets,
        },
        {
          title: "文件数",
          value: data?.totalFiles,
        },
        {
          title: "大小",
          value: formatBytes(data?.totalSize),
        },
        {
          title: "视频",
          value: data?.size?.video || "0 MB",
        },
      ],
      count: [
        {
          title: "文本",
          value: data?.count?.text || 0,
        },
        {
          title: "图像",
          value: data?.count?.image || 0,
        },
        {
          title: "音频",
          value: data?.count?.audio || 0,
        },
        {
          title: "视频",
          value: data?.count?.video || 0,
        },
      ],
    };
    setStatisticsData(statistics);
  }

  const [tags] = useState<string[]>(["标签1", "标签2", "标签3", "标签4"]);

  const filterOptions = [
    {
      key: "type",
      label: "类型",
      options: [
        { label: "所有类型", value: "all" },
        ...Object.values(datasetTypeMap),
      ],
    },
    {
      key: "status",
      label: "状态",
      options: [
        { label: "所有状态", value: "all" },
        ...Object.values(datasetStatusMap),
      ],
    },
    {
      key: "tags",
      label: "标签",
      mode: "multiple",
      options: tags.map((tag) => ({ label: tag, value: tag })),
    },
  ];
  const {
    tableData,
    searchParams,
    pagination,
    fetchData,
    setSearchParams,
    handleFiltersChange,
  } = useFetchData(queryDatasetsUsingGet, mapDataset);

  const handleDownloadDataset = async (dataset: Dataset) => {
    await downloadDatasetUsingGet(dataset.id, dataset.name);
    message.success("数据集下载成功");
  };

  const handleDeleteDataset = async (id: number) => {
    if (!id) return;
    await deleteDatasetByIdUsingDelete(id);

    message.success("数据删除成功");
  };

  useEffect(() => {
    fetchStatistics();
  }, []);

  const operations = [
    {
      key: "edit",
      label: "编辑",
      icon: <EditOutlined />,
      onClick: (item) => {
        navigate(`/data/management/create/${item.id}`);
      },
    },
    {
      key: "download",
      label: "下载",
      icon: <DownloadOutlined />,
      onClick: handleDownloadDataset,
    },
    {
      key: "delete",
      label: "删除",
      icon: <DeleteOutlined />,
      onClick: (item) => handleDeleteDataset(item.id),
    },
  ];

  const columns = [
    {
      title: "名称",
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
      title: "类型",
      dataIndex: "type",
      key: "type",
      render: (type: string) => datasetTypeMap[type]?.label || type,
      width: 100,
    },
    {
      title: "大小",
      dataIndex: "size",
      key: "size",
      width: 120,
    },
    {
      title: "数据项",
      dataIndex: "fileCount",
      key: "fileCount",
      width: 100,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: any) => {
        return (
          <Tag icon={status.icon} color={status.color}>
            {status.label}
          </Tag>
        );
      },
      width: 120,
    },
    {
      title: "操作",
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
      data={tableData}
      pageSize={9}
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
        scroll={{ x: "max-content", y: "calc(100vh - 34rem)" }}
      />
    </Card>
  );

  return (
    <div className="space-y-2 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">数据管理</h1>
        </div>
        <div className="flex gap-2">
          {/* tasks */}
          <TagManager
            onCreate={createDatasetTagUsingPost}
            onDelete={deleteDatasetTagByIdUsingDelete}
            onUpdate={updateDatasetTagByIdUsingPut}
            onFetch={queryDatasetTagsUsingGet}
          />
          <Link to="/data/management/create">
            <Button
              type="primary"
              icon={<PlusOutlined className="w-4 h-4 mr-2" />}
            >
              创建数据集
            </Button>
          </Link>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 mt-4">
        {/* <Card title="数据集统计">
          <div className="grid grid-cols-4">
            {statisticsData.count?.map?.((item) => (
              <Statistic
                key={item.title}
                title={item.title}
                value={item.value}
              />
            ))}
          </div>
        </Card> */}
        <Card>
          <div className="grid grid-cols-4">
            {statisticsData.size?.map?.((item) => (
              <Statistic
                key={item.title}
                title={item.title}
                value={`${item.value}`}
              />
            ))}
          </div>
        </Card>
      </div>
      <SearchControls
        searchTerm={searchParams.keywords}
        onSearchChange={(keywords) =>
          setSearchParams({ ...searchParams, keywords })
        }
        searchPlaceholder="搜索数据集名称、描述或标签..."
        filters={filterOptions}
        onFiltersChange={handleFiltersChange}
        onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle
        className="my-4"
        onReload={fetchData}
      />
      {viewMode === "card" ? renderCardView() : renderListView()}
    </div>
  );
}
