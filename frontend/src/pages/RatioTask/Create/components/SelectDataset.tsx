// typescript
import React, { useEffect, useState } from "react";
import { Badge, Button, Card, Checkbox, Input, Pagination } from "antd";
import { Search as SearchIcon } from "lucide-react";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";
import {
  queryDatasetsUsingGet,
  queryDatasetByIdUsingGet,
} from "@/pages/DataManagement/dataset.api.ts";

interface SelectDatasetProps {
  selectedDatasets: string[];
  onSelectedDatasetsChange: (next: string[]) => void;
  // distributions now: { datasetId: { labelName: { labelValue: count } } }
  onDistributionsChange?: (
    next: Record<string, Record<string, Record<string, number>>>
  ) => void;
  onDatasetsChange?: (list: Dataset[]) => void;
}

const SelectDataset: React.FC<SelectDatasetProps> = ({
                                                       selectedDatasets,
                                                       onSelectedDatasetsChange,
                                                       onDistributionsChange,
                                                       onDatasetsChange,
                                                     }) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [pagination, setPagination] = useState({ page: 1, size: 10, total: 0 });
  const [distributions, setDistributions] = useState<
    Record<string, Record<string, Record<string, number>>>
  >({});

  // Helper: flatten nested distribution for preview and filter logic
  const flattenDistribution = (
    dist?: Record<string, Record<string, number>>
  ): Array<{ label: string; value: string; count: number }> => {
    if (!dist) return [];
    const items: Array<{ label: string; value: string; count: number }> = [];
    Object.entries(dist).forEach(([label, values]) => {
      if (values && typeof values === "object") {
        Object.entries(values).forEach(([val, cnt]) => {
          items.push({ label, value: val, count: cnt });
        });
      }
    });
    return items;
  };

  // Fetch dataset list
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        setLoading(true);
        const { data } = await queryDatasetsUsingGet({
          page: pagination.page,
          size: pagination.size,
          keyword: searchQuery?.trim() || undefined,
        });
        const list = data?.content || data?.data || [];
        setDatasets(list);
        onDatasetsChange?.(list);
        setPagination((prev) => ({
          ...prev,
          total: data?.totalElements ?? data?.total ?? 0,
        }));
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets().then(() => {});
  }, [pagination.page, pagination.size, searchQuery]);

  // Fetch label distributions when datasets change
  useEffect(() => {
    const fetchDistributions = async () => {
      if (!datasets?.length) return;
      const idsToFetch = datasets
        .map((d) => String(d.id))
        .filter((id) => !distributions[id]);
      if (!idsToFetch.length) return;
      try {
        const next: Record<
          string,
          Record<string, Record<string, number>>
        > = { ...distributions };
        for (const id of idsToFetch) {
          let dist: Record<string, Record<string, number>> | undefined =
            undefined;
          try {
            const detRes = await queryDatasetByIdUsingGet(id);
            const det = detRes?.data;
            if (det) {
              const picked = det?.distribution;
              if (picked && typeof picked === "object") {
                // Assume picked is now { labelName: { labelValue: count } }
                dist = picked as Record<string, Record<string, number>>;
              }
            }
          } catch {
            dist = undefined;
          }
          next[String(id)] = dist || {};
        }
        setDistributions(next);
        onDistributionsChange?.(next);
      } catch {
        // ignore
      }
    };
    fetchDistributions().then(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasets]);

  const onToggleDataset = (datasetId: string, checked: boolean) => {
    if (checked) {
      const next = Array.from(new Set([...selectedDatasets, datasetId]));
      onSelectedDatasetsChange(next);
    } else {
      onSelectedDatasetsChange(
        selectedDatasets.filter((id) => id !== datasetId)
      );
    }
  };

  const onClearSelection = () => {
    onSelectedDatasetsChange([]);
  };

  return (
    <div className="border-card flex-1 flex flex-col min-w-[320px]">
      <div className="flex items-center justify-between p-4 border-bottom">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">
            选择数据集
            <span className="text-xs text-gray-500">
              (已选择: {selectedDatasets.length}/{pagination.total})
            </span>
          </span>
        </div>
        <Button type="link" size="small" onClick={onClearSelection}>
          清空选择
        </Button>
      </div>
      <div className="flex-overflow-auto gap-4 p-4">
        <Input
          prefix={<SearchIcon className="text-gray-400" />}
          placeholder="搜索数据集"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setPagination((p) => ({ ...p, page: 1 }));
          }}
        />
        <div className="flex-1 overflow-auto">
          {loading && (
            <div className="text-center text-gray-500 py-8">
              正在加载数据集...
            </div>
          )}
          {!loading &&
            datasets.map((dataset) => {
              const idStr = String(dataset.id);
              const checked = selectedDatasets.includes(idStr);
              const distFor = distributions[idStr];
              const flat = flattenDistribution(distFor);
              return (
                <Card
                  key={dataset.id}
                  size="small"
                  className={`cursor-pointer ${
                    checked ? "border-blue-500" : "hover:border-blue-200"
                  }`}
                  onClick={() => onToggleDataset(idStr, !checked)}
                >
                  <div className="flex items-start gap-3">
                    <Checkbox
                      checked={checked}
                      onChange={(e) => onToggleDataset(idStr, e.target.checked)}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">
                          {dataset.name}
                        </span>
                        <Badge color="blue">{dataset.datasetType}</Badge>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {dataset.description}
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{dataset.fileCount}条</span>
                        <span>{dataset.size}</span>
                      </div>
                      <div className="mt-2">
                        {distFor ? (
                          flat.length > 0 ? (
                            <div className="flex flex-wrap gap-2 text-xs">
                              {flat.slice(0, 8).map((it) => (
                                <Badge
                                  key={`${it.label}_${it.value}`}
                                  color="gray"
                                >{`${it.label}/${it.value}: ${it.count}`}</Badge>
                              ))}
                            </div>
                          ) : (
                            <div className="text-xs text-gray-400">
                              未检测到标签分布
                            </div>
                          )
                        ) : (
                          <div className="text-xs text-gray-400">
                            加载标签分布...
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
        </div>
        <div className="flex justify-between mt-3 items-center">
          <div className="flex items-center gap-3">
            <Pagination
              size="small"
              current={pagination.page}
              pageSize={pagination.size}
              total={pagination.total}
              showSizeChanger
              onChange={(p, ps) =>
                setPagination((prev) => ({ ...prev, page: p, size: ps }))
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SelectDataset;
