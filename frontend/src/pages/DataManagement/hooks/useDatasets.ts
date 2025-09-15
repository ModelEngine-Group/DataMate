import {
  getTypeColor,
  getTypeIcon,
  mockTags,
  statisticsData as statistics,
} from "@/mock/dataset";
import type { Dataset } from "@/types/dataset";
import { message } from "antd";
import { useEffect, useState } from "react";
import {
  getDatasetStatisticsUsingGet,
  queryDatasetsUsingGet,
} from "../dataset-apis";
import { datasetStatusMap, datasetTypeMap } from "../model";
import { useDebouncedEffect } from "@/hooks/useDebouncedEffect";
import { formatBytes } from "@/utils/unit";

export function useDatasets() {
  const [statisticsData, setStatisticsData] = useState<any>({
    count: statistics,
    size: statistics,
  });
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  const [searchParams, setSearchParams] = useState({
    keywords: "",
    filter: {
      type: [] as string[],
      status: [] as string[],
      tags: [] as string[],
    },
    current: 1,
    pageSize: 15,
  });
  const [favoriteDatasets, setFavoriteDatasets] = useState<Set<number>>(
    new Set([1, 3])
  );
  const [pagination, setPagination] = useState({
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ["10", "15", "20", "50"],
    showTotal: (total: number) => `共 ${total} 条`,
    onChange: (current: number, pageSize?: number) => {
      setSearchParams((prev) => ({
        ...prev,
        current,
        pageSize: pageSize || prev.pageSize,
      }));
    },
  });
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
      options: mockTags.map((tag) => ({ label: tag, value: tag })),
    },
  ];

  const handleFiltersChange = (searchFilters: { [key: string]: string[] }) => {
    setSearchParams({
      ...searchParams,
      current: 1,
      filter: { ...searchParams.filter, ...searchFilters },
    });
  };

  const handleToggleFavorite = (datasetId: number) => {
    setFavoriteDatasets((prev) => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(datasetId)) {
        newFavorites.delete(datasetId);
      } else {
        newFavorites.add(datasetId);
      }
      return newFavorites;
    });
  };

  const handleDownloadDataset = (dataset: Dataset) => {};

  const [messageApi, contextHolder] = message.useMessage();

  const handleDeleteDataset = async (id: number) => {
    await fetch(`/api/datasets/${id}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });
    messageApi.success("数据删除成功");
  };

  function mapDatasets(result: Dataset[]) {
    const res = result.map((dataset: Dataset) => ({
      ...dataset,
      size: formatBytes(dataset.totalSize || 0),
      icon: getTypeIcon(dataset.type),
      iconColor: getTypeColor(dataset.type),
      status: datasetStatusMap[dataset.status],
      tags: dataset.tags.map((tag) => tag.name),
      statistics: [
        { label: "数据项", value: dataset?.fileCount || 0 },
        {
          label: "已标注",
          value: dataset.annotations?.completed || 0,
        },
        { label: "大小", value: dataset.totalSize || "0 MB" },
        {
          label: "存储路径",
          value: dataset.storagePath || "未知",
        },
      ],
      lastModified: dataset.updatedAt,
    }));
    return res;
  }

  function getFirstOfArray(arr: string[]) {
    if(!arr || arr.length === 0 || !Array.isArray(arr)) return undefined;
    if(arr[0] === "all") return undefined;
    return arr[0];
  }

  async function fetchDatasets() {
    const { keywords, filter, current, pageSize } = searchParams;
    const data = await queryDatasetsUsingGet({
      ...filter,
      keywords,
      type: getFirstOfArray(filter?.type) || undefined,
      status: getFirstOfArray(filter?.status) || undefined,
      tags: filter?.tags?.length ? filter.tags.join(",") : undefined,
      page: current,
      size: pageSize,
    });
    setPagination((prev) => ({
      ...prev,
      total: data?.totalElements || 0,
    }));
    const result = data?.results ?? [];
    setDatasets(mapDatasets(result));
  }

  async function getDatasetStatistics() {
    const data = await getDatasetStatisticsUsingGet();
    const statistics = {
      size: [
        {
          title: "文本",
          value: data.size.text || "0 MB",
        },
        {
          title: "图像",
          value: data.size.image || "0 MB",
        },
        {
          title: "音频",
          value: data.size.audio || "0 MB",
        },
        {
          title: "视频",
          value: data.size.video || "0 MB",
        },
      ],
      count: [
        {
          title: "文本",
          value: data.count.text || 0,
        },
        {
          title: "图像",
          value: data.count.image || 0,
        },
        {
          title: "音频",
          value: data.count.audio || 0,
        },
        {
          title: "视频",
          value: data.count.video || 0,
        },
      ],
    };
    setStatisticsData(statistics);
  }

  useDebouncedEffect(
    () => {
      fetchDatasets();
    },
    [searchParams],
    500
  );

  useEffect(() => {
    getDatasetStatistics();
  }, []);

  return {
    datasets,
    favoriteDatasets,
    contextHolder,
    filterOptions,
    pagination,
    searchParams,
    setSearchParams,
    setPagination,
    handleToggleFavorite,
    handleDownloadDataset,
    handleDeleteDataset,
    handleFiltersChange,
    fetchDatasets,
    statisticsData,
  };
}
