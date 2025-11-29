import React, { useEffect } from "react";
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

  useDebouncedEffect(
    () => {
      fetchDatasets();
    },
    [datasetSearch, datasetPagination.pageSize, datasetPagination.current],
    300
  );

  const fetchFiles = async () => {
    if (!selectedDataset) return;
    const { data } = await queryDatasetFilesUsingGet(selectedDataset.id, {
      page: filesPagination.current - 1,
      size: filesPagination.pageSize,
      keyword: filesSearch,
    });
    setFiles(
      data.content.map((item) => ({
        ...item,
        key: item.id,
        datasetName: selectedDataset.name,
      })) || []
    );
    setFilesPagination((prev) => ({
      ...prev,
      total: data.totalElements,
    }));
  };

  useEffect(() => {
    if (selectedDataset) {
      fetchFiles();
    }
  }, [selectedDataset]);

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
    }
  }, [open]);

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
            pagination={datasetPagination}
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
            pagination={filesPagination}
            onRow={(record: DatasetFile) => ({
              onClick: () => toggleSelectFile(record),
            })}
            rowSelection={{
              type: "checkbox",
              onSelectAll: (selected, _, changeRows) => {
                const newSelectedFiles = { ...selectedFilesMap };
                if (selected) {
                  changeRows.forEach((row) => {
                    newSelectedFiles[row.id] = row;
                  });
                } else {
                  changeRows.forEach((row) => {
                    delete newSelectedFiles[row.id];
                  });
                }
                onSelectedFilesChange(newSelectedFiles);
              },
              selectedRowKeys: Object.keys(selectedFilesMap),
              onSelect: toggleSelectFile,
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
