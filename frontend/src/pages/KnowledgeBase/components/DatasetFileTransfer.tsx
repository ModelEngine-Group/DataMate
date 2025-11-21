import React, { useEffect } from "react";
import { Input, Table } from "antd";
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

interface DatasetFileTransferProps
  extends React.HTMLAttributes<HTMLDivElement> {
  open: boolean;
  selectedMap: Record<string, DatasetFile[]>;
  onSelectedChange: (filesMap: Record<string, DatasetFile[]>) => void;
}

// Customize Table Transfer
const DatasetFileTransfer: React.FC<DatasetFileTransferProps> = ({
  open,
  selectedMap,
  onSelectedChange,
  ...props
}) => {
  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [datasetSearch, setDatasetSearch] = React.useState<string>("");
  const [datasetPagination, setDatasetPagination] = React.useState<{
    current: number;
    pageSize: number;
    total: number;
  }>({ current: 1, pageSize: 1000, total: 0 });

  const [expandedRowKeys, setExpandedRowKeys] = React.useState<React.Key[]>([]);

  const [loadedFiles, setLoadedFiles] = React.useState<
    Record<string, DatasetFile[]>
  >({});
  const [filesSearch, setFilesSearch] = React.useState<string>("");
  const [filesPagination, setFilesPagination] = React.useState<{
    current: number;
    pageSize: number;
    total: number;
  }>({ current: 1, pageSize: 10, total: 0 });

  const selectedFiles = React.useMemo(() => {
    const files: DatasetFile[] = [];
    Object.values(selectedMap).forEach((fileList) => {
      files.push(...fileList);
    });
    return files;
  }, [selectedMap]);

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({
      page: datasetPagination.current - 1,
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

  useEffect(() => {
    if (open) {
      fetchDatasets();
    }
  }, [open]);

  const fetchFiles = async (dataset: Dataset) => {
    if (!dataset || loadedFiles[dataset.id]) return;
    const { data } = await queryDatasetFilesUsingGet(dataset.id, {
      page: filesPagination.current - 1,
      size: 1000,
      keyword: filesSearch,
    });
    setLoadedFiles((prev) => ({
      ...prev,
      [dataset.id]: data.content,
    }));
    setFilesPagination((prev) => ({
      ...prev,
      total: data.totalElements,
    }));
    return data.content;
  };

  const onExpand = (expanded: boolean, record: Dataset) => {
    if (expanded) {
      fetchFiles(record);
      setExpandedRowKeys([...expandedRowKeys, record.id]);
    } else {
      setExpandedRowKeys(expandedRowKeys.filter((key) => key !== record.id));
    }
  };

  const toggleSelectFile = (dataset: Dataset, record: DatasetFile) => {
    const datasetFiles = selectedMap[dataset.id] || [];
    const hasSelected = datasetFiles.find((file) => file.id === record.id);
    let files = [...datasetFiles];
    if (!hasSelected) {
      files.push(record);
    } else {
      files = datasetFiles.filter((file) => file.id !== record.id);
    }

    const newMap = { ...selectedMap, [dataset.id]: files };
    if (files.length === 0) {
      delete newMap[dataset.id];
    }
    onSelectedChange(newMap);
  };

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

  const fileCols = [
    {
      title: "文件名",
      dataIndex: "fileName",
      key: "fileName",
      ellipsis: true,
    },
    {
      title: "大小",
      dataIndex: "size",
      key: "size",
      ellipsis: true,
      render: formatBytes,
    },
  ];
  return (
    <div className="grid grid-cols-25 gap-4 w-full" {...props}>
      <div className="border-card flex flex-col col-span-12">
        <div className="border-bottom p-2 font-bold">选择数据集文件</div>
        <div className="p-2">
          <Input
            placeholder="搜索数据集名称..."
            value={datasetSearch}
            onChange={(e) => setDatasetSearch(e.target.value)}
          />
        </div>
        <Table
          scroll={{ y: 400 }}
          rowKey="id"
          size="small"
          onRow={(record: Dataset) => ({
            onClick: () => {
              const isExpanded = expandedRowKeys.includes(record.id);
              onExpand(!isExpanded, record);
            },
          })}
          dataSource={datasets}
          columns={datasetCols}
          pagination={datasetPagination}
          rowSelection={{
            type: "checkbox",
            selectedRowKeys: Object.keys(selectedMap),
            onSelect: async (record, isSelected) => {
              let files = [];
              if (!loadedFiles[record.id]) {
                files = await fetchFiles(record);
              } else {
                files = loadedFiles[record.id];
              }

              const newMap = { ...selectedMap };
              if (isSelected) {
                newMap[record.id] = files;
              } else {
                delete newMap[record.id];
              }
              onSelectedChange(newMap);
            },
          }}
          expandable={{
            expandedRowKeys,
            onExpand,
            expandedRowRender: (dataset) => (
              <Table
                scroll={{ y: 400 }}
                rowKey="id"
                size="small"
                dataSource={loadedFiles[dataset.id] || []}
                columns={fileCols}
                pagination={filesPagination}
                onRow={(record: DatasetFile) => ({
                  onClick: () => toggleSelectFile(dataset, record),
                })}
                rowSelection={{
                  type: "checkbox",
                  selectedRowKeys: Object.values(
                    selectedMap[dataset.id] || {}
                  ).map((file) => file.id),
                  onSelect: (record) => toggleSelectFile(dataset, record),
                }}
              />
            ),
          }}
        />
      </div>
      <RightOutlined />
      <div className="border-card flex flex-col col-span-12">
        <div className="border-bottom p-2 font-bold">
          已选文件（{selectedFiles.length}）
        </div>
        <div className="p-2">
          <Input
            placeholder="搜索文件名称..."
            value={filesSearch}
            onChange={(e) => setFilesSearch(e.target.value)}
          />
        </div>
        <Table
          size="small"
          scroll={{ y: 400 }}
          rowKey="id"
          dataSource={selectedFiles}
          columns={fileCols}
        />
      </div>
    </div>
  );
};

export default DatasetFileTransfer;
