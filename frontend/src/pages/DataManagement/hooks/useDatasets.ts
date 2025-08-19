import {
  getStatusBadge,
  getTypeColor,
  getTypeIcon,
  mockDatasets,
  mockTags,
} from "@/mock/dataset";
import type { Dataset } from "@/types/dataset";
import { message } from "antd";
import { useEffect, useState } from "react";

export function useDatasets() {
  const [datasets, setDatasets] = useState(mapDatasets(mockDatasets));
  const [searchTerm, setSearchTerm] = useState("");
  const [favoriteDatasets, setFavoriteDatasets] = useState<Set<number>>(
    new Set([1, 3])
  );
  const filterOptions = [
    {
      key: "type",
      label: "类型",
      options: [
        { label: "所有类型", value: "all" },
        { label: "图像", value: "image" },
        { label: "文本", value: "text" },
        { label: "音频", value: "audio" },
        { label: "视频", value: "video" },
        { label: "多模态", value: "multimodal" },
      ],
    },
    {
      key: "status",
      label: "状态",
      options: [
        { label: "所有状态", value: "all" },
        { label: "活跃", value: "active" },
        { label: "处理中", value: "processing" },
        { label: "已归档", value: "archived" },
      ],
    },
    {
      key: "tag",
      label: "标签",
      mode: "multiple",
      options: mockTags.map((tag) => ({ label: tag, value: tag })),
    },
    {
      key: "isFavorite",
      label: "收藏",
      options: [
        { label: "已收藏", value: "favorited" },
        { label: "未收藏", value: "unfavorited" },
      ],
    },
  ];

  const handleFiltersChange = (searchFilters: { [key: string]: string[] }) => {
    const params = Object.keys(searchFilters).reduce((prev, cur) => {
      const filter = searchFilters[cur] || [];
      return { ...prev, [cur]: filter[0] };
    }, {});
    fetchDatasets(params);
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
    await fetch(`/api/dataset/v2/${id}`);
    messageApi.success("数据删除成功");
  };

  function mapDatasets(result: Dataset[]) {
    return result.map((dataset: Dataset) => ({
      ...dataset,
      icon: getTypeIcon(dataset.type),
      iconColor: getTypeColor(dataset.type),
      status: getStatusBadge(dataset.status),
      description: dataset.description,
      tags: dataset.tags,
      statistics: [
        { label: "数据项", value: dataset.itemCount?.toLocaleString() || 0 },
        {
          label: "已标注",
          value: dataset.annotations?.completed?.toLocaleString() || 0,
        },
        { label: "大小", value: dataset.size || "0 MB" },
        {
          label: "完成率",
          value: dataset.annotations
            ? `${Math.round(
                (dataset.annotations?.completed / dataset.annotations?.total) *
                  100
              )}%`
            : "0%",
        },
      ],
      lastModified: dataset.updatedTime,
    }));
  }

  async function fetchDatasets(params?: any) {
    console.log("Fetching datasets from API...");

    const res = await fetch("/api/dataset/v2/page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...params, pageNum: 1, pageSize: 100 }),
    });
    if (!res.ok) throw new Error("Failed to fetch datasets");
    const data = await res.json();
    const result = data?.records ?? mockDatasets;
    setDatasets(mapDatasets(result));
  }

  useEffect(() => {
    fetchDatasets();
  }, []);

  return {
    datasets,
    favoriteDatasets,
    contextHolder,
    searchTerm,
    filterOptions,
    setSearchTerm,
    handleToggleFavorite,
    handleDownloadDataset,
    handleDeleteDataset,
    handleFiltersChange,
  };
}
