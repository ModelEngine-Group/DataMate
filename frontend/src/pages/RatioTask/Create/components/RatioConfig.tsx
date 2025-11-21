import React, { useMemo, useState } from "react";
import { Badge, Card, Input, Progress, Button, DatePicker, Select } from "antd";
import { BarChart3, Filter, Clock } from "lucide-react";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

const TIME_RANGE_OPTIONS = [
  { label: '最近1天', value: 1 },
  { label: '最近3天', value: 3 },
  { label: '最近7天', value: 7 },
  { label: '最近15天', value: 15 },
  { label: '最近30天', value: 30 },
];

interface RatioConfigItem {
  id: string;
  name: string;
  type: "dataset" | "label";
  quantity: number;
  percentage: number;
  source: string;
  labelFilter?: string;
  dateRange?: string;
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
  const [datasetFilters, setDatasetFilters] = useState<Record<string, {
    labelFilter?: string;
    dateRange?: string;
  }>>({});

  // 配比项总数
  const totalConfigured = useMemo(
    () => ratioConfigs.reduce((sum, c) => sum + (c.quantity || 0), 0),
    [ratioConfigs]
  );

  // 获取数据集的标签列表
  const getDatasetLabels = (datasetId: string): string[] => {
    const dist = distributions[String(datasetId)] || {};
    return Object.keys(dist);
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
        labelFilter: datasetFilters[datasetId]?.labelFilter,
        dateRange: datasetFilters[datasetId]?.dateRange,
      };
    });
    setRatioConfigs(newConfigs);
    onChange?.(newConfigs);
  };

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
        labelFilter: datasetFilters[datasetId]?.labelFilter,
        dateRange: datasetFilters[datasetId]?.dateRange,
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

  // 更新筛选条件
  const updateFilters = (datasetId: string, updates: {
    labelFilter?: string;
    dateRange?: [string, string];
  }) => {
    setDatasetFilters(prev => ({
      ...prev,
      [datasetId]: {
        ...prev[datasetId],
        ...updates,
      }
    }));
  };

  // 渲染筛选器
  const renderFilters = (datasetId: string) => {
    const labels = getDatasetLabels(datasetId);
    const config = ratioConfigs.find(c => c.source === datasetId);
    const filters = datasetFilters[datasetId] || {};

    return (
      <div className="mb-3 p-2 bg-gray-50 rounded">
        <div className="flex items-center gap-2 mb-2">
          <Filter size={14} className="text-gray-400" />
          <span className="text-xs font-medium">筛选条件</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-gray-500 mb-1">标签筛选</div>
            <Select
              style={{ width: '100%' }}
              placeholder="选择标签"
              value={filters.labelFilter}
              onChange={(value) => updateFilters(datasetId, { labelFilter: value })}
              allowClear
              onClear={() => updateFilters(datasetId, { labelFilter: undefined })}
            >
              {labels.map(label => (
                <Option key={label} value={label}>{label}</Option>
              ))}
            </Select>
          </div>

          <div>
            <div className="text-xs text-gray-500 mb-1">标签更新时间</div>
            <Select
              style={{ width: '100%' }}
              placeholder="选择标签更新时间"
              value={filters.dateRange}
              onChange={(dates) => updateFilters(datasetId, { dateRange: dates })}
              allowClear
              onClear={() => updateFilters(datasetId, { dateRange: undefined })}
            >
              {TIME_RANGE_OPTIONS.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </div>
        </div>
      </div>
    );
  };

  // 选中数据集变化时，初始化筛选条件
  React.useEffect(() => {
    const initialFilters: Record<string, any> = {};
    selectedDatasets.forEach(datasetId => {
      const config = ratioConfigs.find(c => c.source === datasetId);
      if (config) {
        initialFilters[datasetId] = {
          labelFilter: config.labelFilter,
          dateRange: config.dateRange,
        };
      }
    });
    setDatasetFilters(prev => ({ ...prev, ...initialFilters }));
  }, [selectedDatasets]);

  return (
    <div className="border-card flex-1 flex flex-col min-w-[320px]">
      <div className="flex items-center justify-between p-4 border-bottom">
        <span className="text-sm font-bold">
          配比配置
          <span className="text-xs text-gray-500 ml-1">
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
            <div className="p-3 bg-gray-50 rounded-lg mb-4">
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
              </div>
            </div>
          )}

          <div className="flex-1 overflow-auto space-y-4">
            {selectedDatasets.map((datasetId) => {
              const dataset = datasets.find((d) => String(d.id) === datasetId);
              const config = ratioConfigs.find((c) => c.source === datasetId);
              const currentQuantity = config?.quantity || 0;

              if (!dataset) return null;

              return (
                <Card key={datasetId} size="small" className="mb-4">
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

                  {/* 筛选条件 */}
                  {renderFilters(datasetId)}

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
                      style={{ width: 100 }}
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
