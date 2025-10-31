import React, { useEffect, useState } from "react";
import { Badge, Button, Card, Checkbox, Input, Pagination, Select } from "antd";
import { Database, Search as SearchIcon } from "lucide-react";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";
import { queryDatasetsUsingGet, queryDatasetByIdUsingGet, queryDatasetStatisticsByIdUsingGet } from "@/pages/DataManagement/dataset.api.ts";

interface SelectDatasetProps {
  selectedDatasets: string[];
  ratioType: "dataset" | "label";
  onRatioTypeChange: (val: "dataset" | "label") => void;
  onSelectedDatasetsChange: (next: string[]) => void;
  onDistributionsChange?: (next: Record<string, Record<string, number>>) => void;
  onDatasetsChange?: (list: Dataset[]) => void;
}

const SelectDataset: React.FC<SelectDatasetProps> = ({
  selectedDatasets,
  ratioType,
  onRatioTypeChange,
  onSelectedDatasetsChange,
  onDistributionsChange,
  onDatasetsChange,
}) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [pagination, setPagination] = useState({ page: 1, size: 10, total: 0 });
  const [distributions, setDistributions] = useState<Record<string, Record<string, number>>>({});

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
        setPagination((prev) => ({ ...prev, total: data?.totalElements ?? data?.total ?? 0 }));
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets();
  }, [pagination.page, pagination.size, searchQuery]);

  // Fetch label distributions when in label mode
  useEffect(() => {
    const fetchDistributions = async () => {
      if (ratioType !== "label" || !datasets?.length) return;
      const idsToFetch = datasets.map((d) => String(d.id)).filter((id) => !distributions[id]);
      if (!idsToFetch.length) return;
      try {
        const results = await Promise.all(
          idsToFetch.map(async (id) => {
            try {
              const statRes = await queryDatasetStatisticsByIdUsingGet(id);
              return { id, stats: statRes?.data };
            } catch {
              return { id, stats: null };
            }
          })
        );

        const next: Record<string, Record<string, number>> = { ...distributions };
        for (const { id, stats } of results) {
          let dist: Record<string, number> | undefined = undefined;
          if (stats) {
            const candidates: any[] = [
              (stats as any).labelDistribution,
              (stats as any).tagDistribution,
              (stats as any).label_stats,
              (stats as any).labels,
              (stats as any).distribution,
            ];
            let picked = candidates.find((c) => c && (typeof c === "object" || Array.isArray(c)));
            if (Array.isArray(picked)) {
              const obj: Record<string, number> = {};
              picked.forEach((it: any) => {
                const key = it?.label ?? it?.name ?? it?.tag ?? it?.key;
                const val = it?.count ?? it?.value ?? it?.num ?? it?.total;
                if (key != null && typeof val === "number") obj[String(key)] = val;
              });
              dist = obj;
            } else if (picked && typeof picked === "object") {
              dist = picked as Record<string, number>;
            }
          }
          if (!dist) {
            try {
              const detRes = await queryDatasetByIdUsingGet(id);
              const det = detRes?.data;
              if (det) {
                let picked =
                  (det as any).distribution ||
                  (det as any).labelDistribution ||
                  (det as any).tagDistribution ||
                  (det as any).label_stats ||
                  (det as any).labels ||
                  undefined;
                if (Array.isArray(picked)) {
                  const obj: Record<string, number> = {};
                  picked.forEach((it: any) => {
                    const key = it?.label ?? it?.name ?? it?.tag ?? it?.key;
                    const val = it?.count ?? it?.value ?? it?.num ?? it?.total;
                    if (key != null && typeof val === "number") obj[String(key)] = val;
                  });
                  dist = obj;
                } else if (picked && typeof picked === "object") {
                  dist = picked as Record<string, number>;
                }
              }
            } catch {
              dist = undefined;
            }
          }
          next[String(id)] = dist || {};
        }
        setDistributions(next);
        onDistributionsChange?.(next);
      } catch {
        // ignore
      }
    };
    fetchDistributions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ratioType, datasets]);

  const onToggleDataset = (datasetId: string, checked: boolean) => {
    if (checked) {
      const next = Array.from(new Set([...selectedDatasets, datasetId]));
      onSelectedDatasetsChange(next);
    } else {
      onSelectedDatasetsChange(selectedDatasets.filter((id) => id !== datasetId));
    }
  };

  const onClearSelection = () => {
    onSelectedDatasetsChange([]);
  };

  return (
    <div className="col-span-5">
      <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
        <Database className="w-5 h-5" />
        数据集选择
      </h2>
      <Card>
        <div className="flex items-center gap-4 mb-4">
            <span className="text-sm">配比方式:</span>
            <Select
              style={{ width: 120 }}
              value={ratioType}
              onChange={(v) => onRatioTypeChange(v)}
              options={[
                { label: "按数据集", value: "dataset" },
                { label: "按标签", value: "label" },
              ]}
            />
        </div>
          <Input
            prefix={<SearchIcon className="text-gray-400" />}
            placeholder="搜索数据集"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPagination((p) => ({ ...p, page: 1 }));
            }}
          />
        <div style={{ maxHeight: 500, overflowY: "auto" }}>
          {loading && (
            <div className="text-center text-gray-500 py-8">正在加载数据集...</div>
          )}
          {!loading &&
            datasets.map((dataset) => {
              const idStr = String(dataset.id);
              const checked = selectedDatasets.includes(idStr);
              return (
                <Card
                  key={dataset.id}
                  size="small"
                  className={`mb-2 cursor-pointer ${checked ? "border-blue-500" : "hover:border-blue-200"}`}
                  onClick={() => onToggleDataset(idStr, !checked)}
                >
                  <div className="flex items-start gap-3">
                    <Checkbox
                      checked={checked}
                      onChange={(e) => onToggleDataset(idStr, e.target.checked)}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">{dataset.name}</span>
                        <Badge color="blue">{dataset.datasetType}</Badge>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{dataset.description}</div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{dataset.fileCount}条</span>
                        <span>{dataset.size}</span>
                      </div>
                      {ratioType === "label" && (
                        <div className="mt-2">
                          {distributions[idStr] ? (
                            Object.entries(distributions[idStr]).length > 0 ? (
                              <div className="flex flex-wrap gap-2 text-xs">
                                {Object.entries(distributions[idStr])
                                  .slice(0, 8)
                                  .map(([tag, count]) => (
                                    <Badge key={tag} color="gray">{`${tag}: ${count}`}</Badge>
                                  ))}
                              </div>
                            ) : (
                              <div className="text-xs text-gray-400">未检测到标签分布</div>
                            )
                          ) : (
                            <div className="text-xs text-gray-400">加载标签分布...</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
        </div>
        <div className="flex justify-between mt-3 items-center">
          <span className="text-sm text-gray-600">已选择 {selectedDatasets.length} 个数据集</span>
          <div className="flex items-center gap-3">
            <Button size="small" onClick={onClearSelection}>
              清空选择
            </Button>
            <Pagination
              size="small"
              current={pagination.page}
              pageSize={pagination.size}
              total={pagination.total}
              showSizeChanger
              onChange={(p, ps) => setPagination((prev) => ({ ...prev, page: p, size: ps }))}
            />
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SelectDataset;
