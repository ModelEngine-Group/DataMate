import React from "react";
import { Badge, Card, Input, Progress } from "antd";
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
  ratioConfigs: RatioConfigItem[];
  totalTargetCount: number;
  distributions: Record<string, Record<string, number>>;
  onUpdateDatasetQuantity: (datasetId: string, quantity: number) => void;
  onUpdateLabelQuantity: (datasetId: string, label: string, quantity: number) => void;
}

const RatioConfig: React.FC<RatioConfigProps> = ({
  ratioType,
  selectedDatasets,
  datasets,
  ratioConfigs,
  totalTargetCount,
  distributions,
  onUpdateDatasetQuantity,
  onUpdateLabelQuantity,
}) => {
  const totalConfigured = ratioConfigs.reduce((sum, c) => sum + (c.quantity || 0), 0);

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">配比设置</span>
        <span className="text-xs text-gray-500">
          已配置: {totalConfigured} / {totalTargetCount}
        </span>
      </div>
      {selectedDatasets.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">请先选择数据集</p>
        </div>
      ) : (
        <div style={{ maxHeight: 500, overflowY: "auto" }}>
          {selectedDatasets.map((datasetId) => {
            const dataset = datasets.find((d) => String(d.id) === datasetId);
            const config = ratioConfigs.find((c) => c.source === datasetId);
            const currentQuantity = config?.quantity || 0;
            if (!dataset) return null;
            return (
              <Card key={datasetId} size="small" className="mb-2">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{dataset.name}</span>
                    <Badge color="gray">{dataset.fileCount}条</Badge>
                  </div>
                  <div className="text-xs text-gray-500">{config?.percentage || 0}%</div>
                </div>
                {ratioType === "dataset" ? (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs">数量:</span>
                      <Input
                        type="number"
                        value={currentQuantity}
                        onChange={(e) => onUpdateDatasetQuantity(datasetId, Number(e.target.value))}
                        style={{ width: 80 }}
                        min={0}
                        max={Math.min(dataset.fileCount || 0, totalTargetCount)}
                      />
                      <span className="text-xs text-gray-500">条</span>
                    </div>
                    <Progress
                      percent={Math.round((currentQuantity / totalTargetCount) * 100)}
                      size="small"
                    />
                  </div>
                ) : (
                  <div>
                    {!distributions[String(dataset.id)] ? (
                      <div className="text-xs text-gray-400">加载标签分布...</div>
                    ) : Object.entries(distributions[String(dataset.id)]).length === 0 ? (
                      <div className="text-xs text-gray-400">该数据集暂无标签</div>
                    ) : (
                      <div className="flex flex-col gap-2">
                        {Object.entries(distributions[String(dataset.id)]).map(([label, count]) => {
                          const sourceKey = `${datasetId}_${label}`;
                          const labelConfig = ratioConfigs.find((c) => c.source === sourceKey);
                          const labelQuantity = labelConfig?.quantity || 0;
                          return (
                            <div key={label} className="flex items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <Badge color="gray">{label}</Badge>
                                <span className="text-xs text-gray-500">{count}条</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs">数量:</span>
                                <Input
                                  type="number"
                                  value={labelQuantity}
                                  onChange={(e) => onUpdateLabelQuantity(datasetId, label, Number(e.target.value))}
                                  style={{ width: 80 }}
                                  min={0}
                                  max={Math.min(Number(count) || 0, totalTargetCount)}
                                />
                                <span className="text-xs text-gray-500">条</span>
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
      )}
    </div>
  );
};

export default RatioConfig;
