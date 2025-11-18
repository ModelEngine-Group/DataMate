import React, { useMemo, useState } from "react";
import { Badge, Card, Input, Progress, Button, Divider } from "antd";
import { BarChart3 } from "lucide-react";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";

interface RatioConfigItem {
  id: string;
  name: string;
  type: "dataset" | "label";
  quantity: number;
  percentage: number;
  source: string;
}

interface RatioConfigProps {
  ratioType: "dataset" | "label";
  selectedDatasets: string[];
  datasets: Dataset[];
  totalTargetCount: number;
  distributions: Record<string, Record<string, number>>;
  onChange?: (configs: RatioConfigItem[]) => void;
}

const RatioConfig: React.FC<RatioConfigProps> = ({
  ratioType,
  selectedDatasets,
  datasets,
  totalTargetCount,
  distributions,
  onChange,
}) => {
  const [ratioConfigs, setRatioConfigs] = useState<RatioConfigItem[]>([]);

  // 配比项总数
  const totalConfigured = useMemo(
    () => ratioConfigs.reduce((sum, c) => sum + (c.quantity || 0), 0),
    [ratioConfigs]
  );

  // 更新数据集配比项
  const updateDatasetQuantity = (datasetId: string, quantity: number) => {
    setRatioConfigs((prev) => {
      const existingIndex = prev.findIndex(
        (config) => config.source === datasetId
      );
      const totalOtherQuantity = prev
        .filter((config) => config.source !== datasetId)
        .reduce((sum, config) => sum + config.quantity, 0);

      const dataset = datasets.find((d) => String(d.id) === datasetId);
      const newConfig: RatioConfigItem = {
        id: datasetId,
        name: dataset?.name || datasetId,
        type: ratioType,
        quantity: Math.min(quantity, totalTargetCount - totalOtherQuantity),
        percentage: Math.round((quantity / totalTargetCount) * 100),
        source: datasetId,
      };

      let newConfigs;
      if (existingIndex >= 0) {
        newConfigs = [...prev];
        newConfigs[existingIndex] = newConfig;
      } else {
        newConfigs = [...prev, newConfig];
      }
      onChange?.(newConfigs);
      return newConfigs;
    });
  };

  // 自动平均分配
  const generateAutoRatio = () => {
    const selectedCount = selectedDatasets.length;
    if (selectedCount === 0) return;
    const baseQuantity = Math.floor(totalTargetCount / selectedCount);
    const remainder = totalTargetCount % selectedCount;
    const newConfigs = selectedDatasets.map((datasetId, index) => {
      const dataset = datasets.find((d) => String(d.id) === datasetId);
      const quantity = baseQuantity + (index < remainder ? 1 : 0);
      return {
        id: datasetId,
        name: dataset?.name || datasetId,
        type: ratioType,
        quantity,
        percentage: Math.round((quantity / totalTargetCount) * 100),
        source: datasetId,
      };
    });
    setRatioConfigs(newConfigs);
    onChange?.(newConfigs);
  };

  // 标签模式下，更新某数据集的某个标签的数量
  const updateLabelQuantity = (
    datasetId: string,
    label: string,
    quantity: number
  ) => {
    const sourceKey = `${datasetId}_${label}`;
    setRatioConfigs((prev) => {
      const existingIndex = prev.findIndex((c) => c.source === sourceKey);
      const totalOtherQuantity = prev
        .filter((c) => c.source !== sourceKey)
        .reduce((sum, c) => sum + c.quantity, 0);
      const dist = distributions[datasetId] || {};
      const labelMax = dist[label] ?? Infinity;
      const cappedQuantity = Math.max(
        0,
        Math.min(quantity, totalTargetCount - totalOtherQuantity, labelMax)
      );
      const newConfig: RatioConfigItem = {
        id: sourceKey,
        name: label,
        type: "label",
        quantity: cappedQuantity,
        percentage: Math.round((cappedQuantity / totalTargetCount) * 100),
        source: sourceKey,
      };
      let newConfigs;
      if (existingIndex >= 0) {
        newConfigs = [...prev];
        newConfigs[existingIndex] = newConfig;
      } else {
        newConfigs = [...prev, newConfig];
      }
      onChange?.(newConfigs);
      return newConfigs;
    });
  };

  // 选中数据集变化时，移除未选中的配比项
  React.useEffect(() => {
    setRatioConfigs((prev) => {
      const next = prev.filter((c) => {
        const id = String(c.source);
        const dsId = id.includes("_") ? id.split("_")[0] : id;
        return selectedDatasets.includes(dsId);
      });
      if (next !== prev) onChange?.(next);
      return next;
    });
    // eslint-disable-next-line
  }, [selectedDatasets]);

  return (
    <div className="border-card flex-1 flex flex-col min-w-[320px]">
      <div className="flex items-center justify-between p-4 border-bottom">
        <span className="text-sm font-bold">
          配比配置
          <span className="text-xs text-gray-500">
            (已配置:{totalConfigured}/{totalTargetCount}条)
          </span>
        </span>
        <Button
          type="link"
          size="small"
          onClick={generateAutoRatio}
          disabled={selectedDatasets.length === 0}
        >
          平均分配
        </Button>
      </div>
      {selectedDatasets.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">请先选择数据集</p>
        </div>
      ) : (
        <div className="flex-overflow-auto gap-4 p-4">
          {/* 配比预览 */}
          {ratioConfigs.length > 0 && (
            <div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">总配比数量:</span>
                    <span className="ml-2 font-medium">
                      {ratioConfigs
                        .reduce((sum, config) => sum + config.quantity, 0)
                        .toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">目标数量:</span>
                    <span className="ml-2 font-medium">
                      {totalTargetCount.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">配比项目:</span>
                    <span className="ml-2 font-medium">
                      {ratioConfigs.length}个
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div className="flex-1 overflow-auto">
            {selectedDatasets.map((datasetId) => {
              const dataset = datasets.find((d) => String(d.id) === datasetId);
              const config = ratioConfigs.find((c) => c.source === datasetId);
              const currentQuantity = config?.quantity || 0;
              if (!dataset) return null;
              return (
                <Card key={datasetId} size="small" className="mb-2">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {dataset.name}
                      </span>
                      <Badge color="gray">{dataset.fileCount}条</Badge>
                    </div>
                    <div className="text-xs text-gray-500">
                      {config?.percentage || 0}%
                    </div>
                  </div>
                  {ratioType === "dataset" ? (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs">数量:</span>
                        <Input
                          type="number"
                          value={currentQuantity}
                          onChange={(e) =>
                            updateDatasetQuantity(
                              datasetId,
                              Number(e.target.value)
                            )
                          }
                          style={{ width: 80 }}
                          min={0}
                          max={Math.min(
                            dataset.fileCount || 0,
                            totalTargetCount
                          )}
                        />
                        <span className="text-xs text-gray-500">条</span>
                      </div>
                      <Progress
                        percent={Math.round(
                          (currentQuantity / totalTargetCount) * 100
                        )}
                        size="small"
                      />
                    </div>
                  ) : (
                    <div>
                      {!distributions[String(dataset.id)] ? (
                        <div className="text-xs text-gray-400">
                          加载标签分布...
                        </div>
                      ) : Object.entries(distributions[String(dataset.id)])
                          .length === 0 ? (
                        <div className="text-xs text-gray-400">
                          该数据集暂无标签
                        </div>
                      ) : (
                        <div className="flex flex-col gap-2">
                          {Object.entries(
                            distributions[String(dataset.id)]
                          ).map(([label, count]) => {
                            const sourceKey = `${datasetId}_${label}`;
                            const labelConfig = ratioConfigs.find(
                              (c) => c.source === sourceKey
                            );
                            const labelQuantity = labelConfig?.quantity || 0;
                            return (
                              <div
                                key={label}
                                className="flex items-center justify-between gap-2"
                              >
                                <div className="flex items-center gap-2">
                                  <Badge color="gray">{label}</Badge>
                                  <span className="text-xs text-gray-500">
                                    {count}条
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs">数量:</span>
                                  <Input
                                    type="number"
                                    value={labelQuantity}
                                    onChange={(e) =>
                                      updateLabelQuantity(
                                        datasetId,
                                        label,
                                        Number(e.target.value)
                                      )
                                    }
                                    style={{ width: 80 }}
                                    min={0}
                                    max={Math.min(
                                      Number(count) || 0,
                                      totalTargetCount
                                    )}
                                  />
                                  <span className="text-xs text-gray-500">
                                    条
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default RatioConfig;
