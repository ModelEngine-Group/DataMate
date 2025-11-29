import React, { useMemo, useState, useEffect, FC } from "react";
import {
  Badge,
  Card,
  Progress,
  Button,
  Select,
  Table,
  InputNumber,
  Space,
} from "antd";
import { BarChart3, Filter } from "lucide-react";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";

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
  source: string; // dataset id
  labelFilter?: string;
  dateRange?: number;
}

interface RatioConfigProps {
  ratioType: "dataset" | "label";
  selectedDatasets: string[];
  datasets: Dataset[];
  totalTargetCount: number;
  distributions: Record<string, Record<string, number>>;
  onChange?: (configs: RatioConfigItem[]) => void;
}

const genId = (datasetId: string) =>
  `${datasetId}-${Math.random().toString(36).slice(2, 9)}`;

const RatioConfig: FC<RatioConfigProps> = ({
                                             ratioType,
                                             selectedDatasets,
                                             datasets,
                                             totalTargetCount,
                                             distributions,
                                             onChange,
                                           }) => {
  const [ratioConfigs, setRatioConfigs] = useState<RatioConfigItem[]>([]);

  const totalConfigured = useMemo(
    () => ratioConfigs.reduce((sum, c) => sum + (c.quantity || 0), 0),
    [ratioConfigs]
  );

  const getDatasetLabels = (datasetId: string): string[] => {
    const dist = distributions[String(datasetId)] || {};
    return Object.keys(dist);
  };

  const addConfig = (datasetId: string) => {
    const dataset = datasets.find((d) => String(d.id) === datasetId);
    const newConfig: RatioConfigItem = {
      id: genId(datasetId),
      name: dataset?.name || datasetId,
      type: ratioType,
      quantity: 0,
      percentage: 0,
      source: datasetId,
    };
    const newConfigs = [...ratioConfigs, newConfig];
    setRatioConfigs(newConfigs);
    onChange?.(newConfigs);
  };

  const removeConfig = (configId: string) => {
    const newConfigs = ratioConfigs.filter((c) => c.id !== configId);
    const adjusted = recomputePercentages(newConfigs);
    setRatioConfigs(adjusted);
    onChange?.(adjusted);
  };

  const updateConfig = (
    configId: string,
    updates: Partial<
      Pick<RatioConfigItem, "quantity" | "labelFilter" | "dateRange">
    >
  ) => {
    const newConfigs = ratioConfigs.map((c) =>
      c.id === configId ? { ...c, ...updates } : c
    );
    const adjusted = recomputePercentages(newConfigs);
    setRatioConfigs(adjusted);
    onChange?.(adjusted);
  };

  const recomputePercentages = (configs: RatioConfigItem[]) => {
    return configs.map((c) => ({
      ...c,
      percentage:
        totalTargetCount > 0
          ? Math.round((c.quantity / totalTargetCount) * 100)
          : 0,
    }));
  };

  const generateAutoRatio = () => {
    const selectedCount = selectedDatasets.length;
    if (selectedCount === 0) return;
    const baseQuantity = Math.floor(totalTargetCount / selectedCount);
    const remainder = totalTargetCount % selectedCount;

    let newConfigs: RatioConfigItem[] = ratioConfigs.filter(
      (c) => !selectedDatasets.includes(c.source)
    );

    selectedDatasets.forEach((datasetId, index) => {
      const dataset = datasets.find((d) => String(d.id) === datasetId);
      const quantity = baseQuantity + (index < remainder ? 1 : 0);
      const config: RatioConfigItem = {
        id: genId(datasetId),
        name: dataset?.name || datasetId,
        type: ratioType,
        quantity,
        percentage: Math.round((quantity / totalTargetCount) * 100),
        source: datasetId,
      };
      newConfigs.push(config);
    });

    setRatioConfigs(newConfigs);
    onChange?.(newConfigs);
  };

  useEffect(() => {
    const keep = ratioConfigs.filter((c) =>
      selectedDatasets.includes(c.source)
    );
    if (keep.length !== ratioConfigs.length) {
      const adjusted = recomputePercentages(keep);
      setRatioConfigs(adjusted);
      onChange?.(adjusted);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        <div className="flex items-center gap-2">
          <Button
            type="link"
            size="small"
            onClick={generateAutoRatio}
            disabled={selectedDatasets.length === 0}
          >
            平均分配
          </Button>
        </div>
      </div>

      {selectedDatasets.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">请先选择数据集</p>
        </div>
      ) : (
        <div className="flex-overflow-auto gap-4 p-4">
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
              if (!dataset) return null;

              const datasetConfigs = ratioConfigs.filter(
                (c) => c.source === datasetId
              );

              const labels = getDatasetLabels(datasetId);
              const usedLabels = datasetConfigs
                .map((c) => c.labelFilter)
                .filter(Boolean) as string[];

              const columns = [
                {
                  title: "配比项",
                  dataIndex: "id",
                  key: "id",
                  render: (_: any, record: RatioConfigItem) => (
                    <Space>
                      <Filter size={14} className="text-gray-400" />
                      <span className="text-sm">{record.name}</span>
                    </Space>
                  ),
                },
                {
                  title: "标签筛选",
                  dataIndex: "labelFilter",
                  key: "labelFilter",
                  render: (_: any, record: RatioConfigItem) => {
                    const availableLabels = labels
                      .map((l) => ({ label: l, value: l }))
                      .filter(
                        (opt) =>
                          opt.value === record.labelFilter ||
                          !usedLabels.includes(opt.value)
                      );
                    return (
                      <Select
                        style={{ width: "160px" }}
                        placeholder="选择标签"
                        value={record.labelFilter}
                        options={availableLabels}
                        allowClear
                        onChange={(value) =>
                          updateConfig(record.id, {
                            labelFilter: value || undefined,
                          })
                        }
                      />
                    );
                  },
                },
                {
                  title: "标签更新时间",
                  dataIndex: "dateRange",
                  key: "dateRange",
                  render: (_: any, record: RatioConfigItem) => (
                    <Select
                      style={{ width: "140px" }}
                      placeholder="选择标签更新时间"
                      value={record.dateRange}
                      options={TIME_RANGE_OPTIONS}
                      allowClear
                      onChange={(value) =>
                        updateConfig(record.id, {
                          dateRange: value || undefined,
                        })
                      }
                    />
                  ),
                },
                {
                  title: "数量",
                  dataIndex: "quantity",
                  key: "quantity",
                  render: (_: any, record: RatioConfigItem) => (
                    <InputNumber
                      min={0}
                      max={Math.min(dataset.fileCount || 0, totalTargetCount)}
                      value={record.quantity}
                      onChange={(v) =>
                        updateConfig(record.id, { quantity: Number(v || 0) })
                      }
                    />
                  ),
                },
                {
                  title: "占比",
                  dataIndex: "percentage",
                  key: "percentage",
                  render: (_: any, record: RatioConfigItem) => (
                    <div style={{ minWidth: 140 }}>
                      <div className="text-xs mb-1">
                        {record.percentage ?? 0}%
                      </div>
                      <Progress
                        percent={record.percentage ?? 0}
                        size="small"
                        showInfo={false}
                      />
                    </div>
                  ),
                },
                {
                  title: "操作",
                  dataIndex: "actions",
                  key: "actions",
                  render: (_: any, record: RatioConfigItem) => (
                    <Button danger size="small" onClick={() => removeConfig(record.id)}>
                      删除
                    </Button>
                  ),
                },
              ];

              return (
                <Card key={datasetId} size="small" className="mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{dataset.name}</span>
                      <Badge color="gray">{dataset.fileCount}条</Badge>
                    </div>
                    <div className="text-xs text-gray-500">
                      {datasetConfigs.reduce((s, c) => s + (c.percentage || 0), 0)}%
                    </div>
                  </div>

                  <Table
                    dataSource={datasetConfigs}
                    columns={columns}
                    pagination={false}
                    rowKey="id"
                    size="small"
                    locale={{ emptyText: "暂无配比项，请添加" }}
                  />

                  <div className="flex justify-end mt-3">
                    <Button size="small" onClick={() => addConfig(datasetId)}>
                      添加配比项
                    </Button>
                  </div>
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
