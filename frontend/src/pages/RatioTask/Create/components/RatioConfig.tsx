import React, { useMemo, useState, useEffect, FC } from "react";
import {
  Badge,
  Card,
  Button,
  Select,
  Table,
  InputNumber,
  DatePicker
} from "antd";
import { BarChart3 } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";

const TIME_RANGE_OPTIONS = [
  { label: '最近1天', value: 1 },
  { label: '最近3天', value: 3 },
  { label: '最近7天', value: 7 },
  { label: '最近15天', value: 15 },
  { label: '最近30天', value: 30 },
];

interface LabelFilter {
  label: string;
  value: string;
}

interface RatioConfigItem {
  id: string;
  name: string;
  type: "dataset" | "label";
  quantity: number;
  percentage: number;
  source: string; // dataset id
  labelFilter?: LabelFilter;
  dateRange?: [Date | null, Date | null] | null;
}

interface RatioConfigProps {
  ratioType: "dataset" | "label";
  selectedDatasets: string[];
  datasets: Dataset[];
  totalTargetCount: number;
  // distributions now: { datasetId: { labelName: { labelValue: count } } }
  distributions: Record<string, Record<string, Record<string, number>>>;
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
  const { t } = useTranslation();
  const [ratioConfigs, setRatioConfigs] = useState<RatioConfigItem[]>([]);

  const totalConfigured = useMemo(
    () => ratioConfigs.reduce((sum, c) => sum + (c.quantity || 0), 0),
    [ratioConfigs]
  );

  const getDatasetLabels = (datasetId: string): string[] => {
    const dist = distributions[String(datasetId)] || {};
    return Object.keys(dist);
  };

  const getLabelValues = (datasetId: string, label: string): string[] => {
    return Object.keys(distributions[String(datasetId)]?.[label] || {});
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
          {t("ratioTask.create.ratioConfig.title")}
          <span className="text-xs text-gray-500 ml-1">
            ({t("ratioTask.create.ratioConfig.configuredCount", { configured: totalConfigured, total: totalTargetCount })})
          </span>
        </span>
        <div className="flex items-center gap-2">
          <Button
            type="link"
            size="small"
            onClick={generateAutoRatio}
            disabled={selectedDatasets.length === 0}
          >
            {t("ratioTask.create.ratioConfig.averageDistribute")}
          </Button>
        </div>
      </div>

      {selectedDatasets.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">{t("ratioTask.create.ratioConfig.selectDatasetFirst")}</p>
        </div>
      ) : (
        <div className="flex-overflow-auto gap-4 p-4">
          {ratioConfigs.length > 0 && (
            <div className="p-3 bg-gray-50 rounded-lg mb-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">{t("ratioTask.create.ratioConfig.totalRatioCount")}</span>
                  <span className="ml-2 font-medium">
                    {ratioConfigs
                      .reduce((sum, config) => sum + config.quantity, 0)
                      .toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">{t("ratioTask.create.ratioConfig.targetCount")}</span>
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

              // helper: used values per label for this dataset (exclude a given row when needed)
              const getUsedValuesForLabel = (label: string, excludeId?: string) => {
                return new Set(
                  datasetConfigs
                    .filter((c) => c.id !== excludeId && c.labelFilter?.label === label)
                    .map((c) => c.labelFilter?.value)
                    .filter(Boolean) as string[]
                );
              };

              const columns = [
                {
                  title: t("ratioTask.create.ratioConfig.label"),
                  dataIndex: "labelFilter",
                  key: "labelFilter",
                  render: (_: any, record: RatioConfigItem) => {
                    const availableLabels = labels
                      .map((l) => ({
                        label: l,
                        value: l,
                        disabled: getLabelValues(datasetId, l).every((v) => getUsedValuesForLabel(l, record.id).has(v)),
                      }))
                    return (
                      <Select
                        style={{ width: "160px" }}
                        placeholder={t("ratioTask.create.ratioConfig.selectLabel")}
                        value={record.labelFilter?.label}
                        options={availableLabels}
                        allowClear
                        onChange={(value) => {
                          if (!value) {
                            updateConfig(record.id, { labelFilter: undefined });
                          } else {
                            // reset value when label changes
                            updateConfig(record.id, {
                              labelFilter: { label: value, value: "" },
                            });
                          }
                        }}
                      />
                    );
                  },
                },
                {
                  title: t("ratioTask.create.ratioConfig.labelValue"),
                  dataIndex: "labelValue",
                  key: "labelValue",
                  render: (_: any, record: RatioConfigItem) => {
                    const selectedLabel = record.labelFilter?.label;
                    const options = selectedLabel
                      ? getLabelValues(datasetId, selectedLabel).map((v) => ({
                        label: v,
                        value: v,
                        disabled: datasetConfigs.some(
                          (c) =>
                            c.id !== record.id &&
                            c.labelFilter?.label === selectedLabel &&
                            c.labelFilter?.value === v
                        ),
                      }))
                      : [];
                    return (
                      <Select
                        style={{ width: "180px" }}
                        placeholder={t("ratioTask.create.ratioConfig.selectLabelValue")}
                        value={record.labelFilter?.value || undefined}
                        options={options}
                        allowClear
                        disabled={!selectedLabel}
                        onChange={(value) => {
                          if (!selectedLabel) return;
                          updateConfig(record.id, {
                            labelFilter: {
                              label: selectedLabel,
                              value: value || "",
                            },
                          });
                        }}
                      />
                    );
                  },
                },
                {
                  title: t("ratioTask.create.ratioConfig.labelUpdateTime"),
                  dataIndex: "dateRange",
                  key: "dateRange",
                  render: (_: any, record: RatioConfigItem) => {
                    return (
                      <DatePicker.RangePicker
                        value={record.dateRange as any}
                        onChange={(date) => {
                          updateConfig(record.id, { dateRange: date });
                        }}
                        placeholder={[t("ratioTask.create.ratioConfig.dateStart"), t("ratioTask.create.ratioConfig.dateEnd")]}
                        allowClear
                      />
                    );
                  },
                },
                {
                  title: t("ratioTask.create.ratioConfig.quantity"),
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
                  title: t("ratioTask.create.ratioConfig.actions"),
                  dataIndex: "actions",
                  key: "actions",
                  render: (_: any, record: RatioConfigItem) => (
                    <Button danger size="small" onClick={() => removeConfig(record.id)}>
                      {t("ratioTask.create.ratioConfig.delete")}
                    </Button>
                  ),
                },
              ];

              return (
                <Card key={datasetId} size="small" className="mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{dataset.name}</span>
                      <Badge color="gray">{dataset.fileCount}{t("ratioTask.create.ratioConfig.itemSuffix")}</Badge>
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
                    locale={{ emptyText: t("ratioTask.create.ratioConfig.emptyText") }}
                  />

                  <div className="flex justify-end mt-3">
                    <Button size="small" onClick={() => addConfig(datasetId)}>
                      {t("ratioTask.create.ratioConfig.addRatioItem")}
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
