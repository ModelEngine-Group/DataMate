import React, { useMemo } from "react";
import { Table } from "antd";
import { TransferItem } from "antd/es/transfer";
import RatioConfig from "./RatioConfig";
import useFetchData from "@/hooks/useFetchData";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import {
  datasetTypeMap,
  mapDataset,
} from "@/pages/DataManagement/dataset.const";
import { SearchControls } from "@/components/SearchControls";

const leftColumns = [
  {
    dataIndex: "name",
    title: "名称",
    ellipsis: true,
  },
  {
    dataIndex: "datasetType",
    title: "类型",
    ellipsis: true,
    width: 100,
    render: (type: string) => datasetTypeMap[type].label,
  },
  {
    dataIndex: "size",
    title: "大小",
    width: 100,
    ellipsis: true,
  },
];

export default function RatioTransfer(props: {
  distributions: Record<string, Record<string, number>>;
  ratioTaskForm: any;
  updateRatioConfig: (datasetId: string, quantity: number) => void;
  updateLabelRatioConfig: (
    datasetId: string,
    label: string,
    quantity: number
  ) => void;
}) {
  const {
    updateLabelRatioConfig,
    updateRatioConfig,
    ratioTaskForm,
    distributions,
  } = props;
  const {
    tableData: datasets,
    loading,
    pagination,
    searchParams,
    setSearchParams,
    handleFiltersChange,
  } = useFetchData(queryDatasetsUsingGet, mapDataset);

  const [selectedDatasets, setSelectedDatasets] = React.useState<
    TransferItem[]
  >([]);

  const selectedRowKeys = useMemo(() => {
    return selectedDatasets.map((item) => item.key);
  }, [selectedDatasets]);

  const [listDisabled, setListDisabled] = React.useState(false);

  const generateAutoRatio = () => {
    const selectedCount = ratioTaskForm.selectedDatasets.length;
    if (selectedCount === 0) return;

    const baseQuantity = Math.floor(
      ratioTaskForm.totalTargetCount / selectedCount
    );
    const remainder = ratioTaskForm.totalTargetCount % selectedCount;

    const newConfigs = ratioTaskForm.selectedDatasets.map(
      (datasetId, index) => {
        const quantity = baseQuantity + (index < remainder ? 1 : 0);
        return {
          id: datasetId,
          name: datasetId,
          type: ratioTaskForm.ratioType,
          quantity,
          percentage: Math.round(
            (quantity / ratioTaskForm.totalTargetCount) * 100
          ),
          source: datasetId,
        };
      }
    );
    setRatioTaskForm((prev) => ({ ...prev, ratioConfigs: newConfigs }));
  };

  return (
    <div className="flex">
      <div className="border-card flex-1 mr-4">
        <h3 className="p-2 border-bottom">{`${selectedDatasets.length} / ${datasets.length} 项`}</h3>
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={(keyword) =>
            setSearchParams({ ...searchParams, keyword })
          }
          searchPlaceholder="搜索数据集名称..."
          filters={[
            {
              key: "type",
              label: "数据集类型",
              options: [
                { value: "dataset", label: "按数据集" },
                { value: "tag", label: "按标签" },
              ],
            },
          ]}
          onFiltersChange={handleFiltersChange}
          onClearFilters={() =>
            setSearchParams({ ...searchParams, filter: {} })
          }
          showViewToggle={false}
          showReload={false}
          className="m-4"
        />
        <Table
          rowSelection={{
            onChange: (_, selectedRows) => {
              setSelectedDatasets(selectedRows);
            },
            selectedRowKeys,
            selections: [
              Table.SELECTION_ALL,
              Table.SELECTION_INVERT,
              Table.SELECTION_NONE,
            ],
          }}
          columns={leftColumns}
          dataSource={datasets}
          loading={loading}
          pagination={pagination}
          size="small"
          rowKey="id"
          style={{ pointerEvents: listDisabled ? "none" : undefined }}
          onRow={(record) => ({
            onClick: () => {
              if (record.disabled || listDisabled) {
                return;
              }
              setSelectedDatasets((prev) => {
                if (prev.includes(record.key)) {
                  return prev.filter((k) => k !== record.key);
                }
                return [...prev, record.key];
              });
            },
          })}
        />
      </div>
      <div className="border-card flex-1">
        <RatioConfig
          datasets={selectedDatasets}
          ratioTaskForm={ratioTaskForm}
          distributions={distributions}
          onUpdateDatasetQuantity={updateRatioConfig}
          onUpdateLabelQuantity={updateLabelRatioConfig}
        />
      </div>
    </div>
  );
}
