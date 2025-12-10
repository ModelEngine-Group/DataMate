import React, { useCallback, useEffect } from "react";
import { Button, Input, Table } from "antd";
import { RightOutlined } from "@ant-design/icons";
import { mapDataset } from "@/pages/DataManagement/dataset.const";
import {
  Dataset,
  DatasetFile,
  DatasetType,
} from "@/pages/DataManagement/dataset.model";
import {
  queryDatasetFilesUsingGet,
  queryDatasetsUsingGet,
} from "@/pages/DataManagement/dataset.api";
import { formatBytes } from "@/utils/unit";
import { useDebouncedEffect } from "@/hooks/useDebouncedEffect";

interface DatasetFileTransferProps
  extends React.HTMLAttributes<HTMLDivElement> {
  open: boolean;
  selectedFilesMap: { [key: string]: DatasetFile };
  onSelectedFilesChange: (filesMap: { [key: string]: DatasetFile }) => void;
  onDatasetSelect?: (dataset: Dataset | null) => void;
}

const fileCols = [
  {
    title: "所属数据集",
    dataIndex: "datasetName",
    key: "datasetName",
    ellipsis: true,
  },
  {
    title: "文件名",
    dataIndex: "fileName",
    key: "fileName",
    ellipsis: true,
  },
  {
    title: "大小",
    dataIndex: "fileSize",
    key: "fileSize",
    ellipsis: true,
    render: formatBytes,
  },
];

// Customize Table Transfer
const DatasetFileTransfer: React.FC<DatasetFileTransferProps> = ({
  open,
  selectedFilesMap,
  onSelectedFilesChange,
  onDatasetSelect,
  ...props
}) => {
  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [datasetSearch, setDatasetSearch] = React.useState<string>("");
  const [datasetPagination, setDatasetPagination] = React.useState<{
    current: number;
    pageSize: number;
    total: number;
  }>({ current: 1, pageSize: 10, total: 0 });

  const [files, setFiles] = React.useState<DatasetFile[]>([]);
  const [filesSearch, setFilesSearch] = React.useState<string>("");
  const [filesPagination, setFilesPagination] = React.useState<{
    current: number;
    pageSize: number;
    total: number;
  }>({ current: 1, pageSize: 10, total: 0 });

  const [showFiles, setShowFiles] = React.useState<boolean>(false);
  const [selectedDataset, setSelectedDataset] = React.useState<Dataset | null>(
    null
  );
  const [datasetSelections, setDatasetSelections] = React.useState<Dataset[]>(
    []
  );

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({
      // Ant Design Table pagination.current is 1-based; ensure backend also receives 1-based value
      page: datasetPagination.current,
      size: datasetPagination.pageSize,
      keyword: datasetSearch,
      type: DatasetType.TEXT,
    });
    setDatasets(data.content.map(mapDataset) || []);
    setDatasetPagination((prev) => ({
      ...prev,
      total: data.totalElements,
    }));
  };

  useDebouncedEffect(
    () => {
      fetchDatasets();
    },
    [datasetSearch, datasetPagination.pageSize, datasetPagination.current],
    300
  );

  const fetchFiles = useCallback(
    async (
      options?: Partial<{ page: number; pageSize: number; keyword: string }>
    ) => {
      if (!selectedDataset) return;
      const page = options?.page ?? filesPagination.current;
      const pageSize = options?.pageSize ?? filesPagination.pageSize;
      const keyword = options?.keyword ?? filesSearch;

      const { data } = await queryDatasetFilesUsingGet(selectedDataset.id, {
        page,
        size: pageSize,
        keyword,
      });
      setFiles(
        (data.content || []).map((item: DatasetFile) => ({
          ...item,
          key: item.id,
          datasetName: selectedDataset.name,
        }))
      );
      setFilesPagination((prev) => ({
        ...prev,
        current: page,
        pageSize,
        total: data.totalElements,
      }));
    },
    [selectedDataset, filesPagination.current, filesPagination.pageSize, filesSearch]
  );

  useEffect(() => {
    // 当数据集变化时，重置文件分页并拉取第一页文件，避免额外的循环请求
    if (selectedDataset) {
      setFilesPagination({ current: 1, pageSize: 10, total: 0 });
      fetchFiles({ page: 1, pageSize: 10 }).catch(() => {});
    } else {
      setFiles([]);
      setFilesPagination({ current: 1, pageSize: 10, total: 0 });
    }
    // 只在 selectedDataset 变化时触发
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDataset]);

  useEffect(() => {
    onDatasetSelect?.(selectedDataset);
  }, [selectedDataset, onDatasetSelect]);

  const toggleSelectFile = (record: DatasetFile) => {
    if (!selectedFilesMap[record.id]) {
      onSelectedFilesChange({
        ...selectedFilesMap,
        [record.id]: record,
      });
    } else {
      const newSelectedFiles = { ...selectedFilesMap };
      delete newSelectedFiles[record.id];
      onSelectedFilesChange(newSelectedFiles);
    }
  };

  useEffect(() => {
    if (!open) {
      // 重置状态
      setDatasets([]);
      setDatasetSearch("");
      setDatasetPagination({ current: 1, pageSize: 10, total: 0 });
      setFiles([]);
      setFilesSearch("");
      setFilesPagination({ current: 1, pageSize: 10, total: 0 });
      setShowFiles(false);
      setSelectedDataset(null);
      setDatasetSelections([]);
      onDatasetSelect?.(null);
    }
  }, [open, onDatasetSelect]);

  const datasetCols = [
    {
      title: "数据集名称",
      dataIndex: "name",
      key: "name",
      ellipsis: true,
    },
    {
      title: "文件数",
      dataIndex: "fileCount",
      key: "fileCount",
      ellipsis: true,
    },
    {
      title: "大小",
      dataIndex: "totalSize",
      key: "totalSize",
      ellipsis: true,
      render: formatBytes,
    },
  ];

  return (
    <div {...props}>
      <div className="grid grid-cols-25 gap-4 w-full">
        <div className="border-card flex flex-col col-span-12">
          <div className="border-bottom p-2 font-bold">选择数据集</div>
          <div className="p-2">
            <Input
              placeholder="搜索数据集名称..."
              value={datasetSearch}
              allowClear
              onChange={(e) => setDatasetSearch(e.target.value)}
            />
          </div>
          <Table
            scroll={{ y: 400 }}
            rowKey="id"
            size="small"
            rowClassName={(record) =>
              selectedDataset?.id === record.id ? "bg-blue-100" : ""
            }
            onRow={(record: Dataset) => ({
              onClick: () => {
                setSelectedDataset(record);
                if (!datasetSelections.find((d) => d.id === record.id)) {
                  setDatasetSelections([...datasetSelections, record]);
                } else {
                  setDatasetSelections(
                    datasetSelections.filter((d) => d.id !== record.id)
                  );
                }
              },
            })}
            dataSource={datasets}
            columns={datasetCols}
            pagination={{
                ...datasetPagination,
                onChange: (page, pageSize) =>
                    setDatasetPagination({
                        current: page,
                        pageSize: pageSize || datasetPagination.pageSize,
                        total: datasetPagination.total,
                    }),
            }}
          />
        </div>
        <RightOutlined />
        <div className="border-card flex flex-col col-span-12">
          <div className="border-bottom p-2 font-bold">选择文件</div>
          <div className="p-2">
            <Input
              placeholder="搜索文件名称..."
              value={filesSearch}
              onChange={(e) => setFilesSearch(e.target.value)}
            />
          </div>
          <Table
            scroll={{ y: 400 }}
            rowKey="id"
            size="small"
            dataSource={files}
            columns={fileCols.slice(1, fileCols.length)}
            pagination={{
              ...filesPagination,
              onChange: (page, pageSize) => {
                const nextPageSize = pageSize || filesPagination.pageSize;
                setFilesPagination((prev) => ({
                  ...prev,
                  current: page,
                  pageSize: nextPageSize,
                }));
                fetchFiles({ page, pageSize: nextPageSize }).catch(() => {});
              },
            }}
            onRow={(record: DatasetFile) => ({
              onClick: () => toggleSelectFile(record),
            })}
            rowSelection={{
              type: "checkbox",
              selectedRowKeys: Object.keys(selectedFilesMap),

              // 单选
              onSelect: (record: DatasetFile) => {
                toggleSelectFile(record);
              },

              // 全选
              onSelectAll: (selected, selectedRows: DatasetFile[]) => {
                if (selected) {
                  // ✔ 全选 -> 将 files 列表全部加入 selectedFilesMap
                  const newMap: Record<string, DatasetFile> = { ...selectedFilesMap };
                  selectedRows.forEach((f) => {
                    newMap[f.id] = f;
                  });
                  onSelectedFilesChange(newMap);
                } else {
                  // ✘ 取消全选 -> 清空 map
                  const newMap = { ...selectedFilesMap };
                  Object.keys(newMap).forEach((id) => {
                    if (files.some((f) => String(f.id) === id)) {
                      // 仅移除当前页对应文件
                      delete newMap[id];
                    }
                  });
                  onSelectedFilesChange(newMap);
                }
              },

              getCheckboxProps: (record: DatasetFile) => ({
                name: record.fileName,
              }),
            }}
          />
        </div>
      </div>
      <Button className="mt-4" onClick={() => setShowFiles(!showFiles)}>
        {showFiles ? "取消预览" : "预览"}
      </Button>
      <div hidden={!showFiles}>
        <Table
          scroll={{ y: 400 }}
          rowKey="id"
          size="small"
          dataSource={Object.values(selectedFilesMap)}
          columns={fileCols}
        />
      </div>
    </div>
  );
};

export default DatasetFileTransfer;
