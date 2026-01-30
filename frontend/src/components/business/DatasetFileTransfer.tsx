import React, { useCallback, useEffect } from "react";
import { Button, Input, Table, message } from "antd";
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
  datasetTypeFilter?: DatasetType;
  /**
   * 允许选择的文件扩展名白名单（小写，包含点号，例如 ".jpg"）。
   * - 若不设置，则不过滤扩展名；
   * - 若设置，则仅展示和选择这些扩展名的文件（包括“全选当前数据集”）。
   */
  allowedFileExtensions?: string[];
  /**
   * 是否强制“单数据集模式”：
   * - 为 true 时，仅允许从同一个数据集选择文件；
   * - 当已选文件来自某个数据集时，尝试从其他数据集勾选文件会被阻止并提示。
   */
  singleDatasetOnly?: boolean;
  /**
   * 固定可选数据集 ID：
   * - 设置后，左侧数据集列表只展示该数据集；
   * - 主要用于“编辑任务数据集”场景，锁定为任务创建时的数据集。
   */
  fixedDatasetId?: string | number;
  /**
   * 锁定的文件ID集合：
   * - 在左侧文件列表中，这些文件的勾选框会变成灰色且不可交互；
   * - 点击整行也不会改变其选中状态；
   * - 主要用于“编辑任务数据集”场景下锁死任务初始文件。
   */
  lockedFileIds?: string[];
  /**
   * 整体禁用开关：
   * - 为 true 时，禁止切换数据集和选择文件，仅用于展示当前配置；
   * - 可配合上层逻辑（如“需先选模板再选数据集”）使用。
   */
  disabled?: boolean;
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
  datasetTypeFilter,
  allowedFileExtensions,
  singleDatasetOnly,
  fixedDatasetId,
  lockedFileIds,
  disabled,
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
  const [selectingAll, setSelectingAll] = React.useState<boolean>(false);

  const lockedIdSet = React.useMemo(() => {
    return new Set((lockedFileIds || []).map((id) => String(id)));
  }, [lockedFileIds]);

  // 在单数据集模式下，根据已选文件反推“当前锁定的数据集ID”
  const lockedDatasetId = React.useMemo(() => {
    if (!singleDatasetOnly) return undefined;
    const ids = new Set(
      Object.values(selectedFilesMap)
        .map((file: any) => file?.datasetId)
        .filter((id) => id !== undefined && id !== null && id !== "")
        .map((id) => String(id))
    );
    if (ids.size === 1) {
      return Array.from(ids)[0];
    }
    return undefined;
  }, [singleDatasetOnly, selectedFilesMap]);

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({
      // Ant Design Table pagination.current is 1-based; ensure backend also receives 1-based value
      page: datasetPagination.current,
      size: datasetPagination.pageSize,
      keyword: datasetSearch,
      // 后端在大多数环境下支持按 type 过滤；若未生效，前端仍会基于 datasetTypeFilter 再做一次兜底筛选
      type: datasetTypeFilter,
    });

    let mapped: any[] = (data.content || []).map(mapDataset);

    // 兜底：在前端再按 datasetTypeFilter 过滤一次，确保只展示指定类型的数据集
    if (datasetTypeFilter) {
      mapped = mapped.filter(
        (ds: any) => ds.datasetType === datasetTypeFilter
      );
    }

    const filtered =
      fixedDatasetId !== undefined && fixedDatasetId !== null
        ? mapped.filter((ds: Dataset) => String(ds.id) === String(fixedDatasetId))
        : mapped;

    setDatasets(filtered);
    setDatasetPagination((prev) => ({
      ...prev,
      total: filtered.length,
    }));
  };

  useDebouncedEffect(
    () => {
      fetchDatasets();
    },
    [datasetSearch, datasetPagination.pageSize, datasetPagination.current, datasetTypeFilter],
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
      const mapped = (data.content || []).map((item: DatasetFile) => ({
        ...item,
        id: item.id,
        key: String(item.id), // rowKey 使用字符串，确保与 selectedRowKeys 类型一致
        // 记录所属数据集，方便后续在“全不选”时只清空当前数据集的选择
        // DatasetFile 接口是后端模型，这里在前端扩展 datasetId 字段
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        datasetId: selectedDataset.id,
        datasetName: selectedDataset.name,
      }));

      const filtered =
        allowedFileExtensions && allowedFileExtensions.length > 0
          ? mapped.filter((file) => {
              const ext =
                file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
              return allowedFileExtensions.includes(ext);
            })
          : mapped;

      setFiles(filtered);
      setFilesPagination((prev) => ({
        ...prev,
        current: page,
        pageSize,
        total: data.totalElements,
      }));
    },
    [selectedDataset, filesPagination.current, filesPagination.pageSize, filesSearch, allowedFileExtensions]
  );

  useEffect(() => {
    // 当数据集变化时，重置文件分页并拉取第一页文件，避免额外的循环请求
    if (selectedDataset) {
      setFilesPagination({ current: 1, pageSize: 10, total: 0 });
      // 与其它页面保持一致，后端使用 1-based page 参数，这里传 1 获取第一页
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

  // 在 fixedDatasetId 场景下，数据集列表加载完成后自动选中该数据集
  useEffect(() => {
    if (!open) return;
    if (fixedDatasetId === undefined || fixedDatasetId === null) return;
    if (selectedDataset) return;
    if (!datasets.length) return;

    const target = datasets.find((ds) => String(ds.id) === String(fixedDatasetId));
    if (target) {
      setSelectedDataset(target);
    }
  }, [open, fixedDatasetId, datasets, selectedDataset]);

  const handleSelectAllInDataset = useCallback(async () => {
    if (!selectedDataset) {
      message.warning("请先选择一个数据集");
      return;
    }

    // 单数据集模式下，如果当前已选文件来自其他数据集，则阻止一键全选
    if (singleDatasetOnly) {
      const existingIds = new Set(
        Object.values(selectedFilesMap)
          .map((file: any) => file?.datasetId)
          .filter((id) => id !== undefined && id !== null && id !== "")
          .map((id) => String(id)),
      );
      const currentId = String(selectedDataset.id);
      if (existingIds.size > 0 && (!existingIds.has(currentId) || existingIds.size > 1)) {
        message.warning("当前仅支持从一个数据集选择文件，请先清空已选文件后再切换数据集");
        return;
      }
    }

    try {
      setSelectingAll(true);

      const pageSize = 1000; // 分批拉取，避免后端单页限制
      let page = 1; // 与其它页面保持一致，使用 1-based page 参数
      let total = 0;
      const allFiles: DatasetFile[] = [];

      while (true) {
        const { data } = await queryDatasetFilesUsingGet(selectedDataset.id, {
          page,
          size: pageSize,
        });

        const mapped: DatasetFile[] = (data.content || []).map(
          (item: DatasetFile) => ({
            ...item,
            key: item.id,
            // 同样为批量全选结果打上 datasetId 标记
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            datasetId: selectedDataset.id,
            datasetName: selectedDataset.name,
          }),
        );

        const content: DatasetFile[] =
          allowedFileExtensions && allowedFileExtensions.length > 0
            ? mapped.filter((file) => {
                const ext =
                  file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
                return allowedFileExtensions.includes(ext);
              })
            : mapped;

        if (!content.length) {
          break;
        }

        allFiles.push(...content);
        // 优先用后端的 totalElements，否则用当前累积数
        total = typeof data.totalElements === "number" ? data.totalElements : allFiles.length;

        // 如果这一页数量小于 pageSize，说明已经拿完；否则继续下一页
        if (content.length < pageSize) {
          break;
        }

        page += 1;
      }

      const newMap: { [key: string]: DatasetFile } = { ...selectedFilesMap };
      allFiles.forEach((file) => {
        if (file && file.id != null) {
          newMap[String(file.id)] = file;
        }
      });

      onSelectedFilesChange(newMap);

      const count = allFiles.length;
      if (count > 0) {
        message.success(`已选中当前数据集的全部 ${count} 个文件`);
      } else {
        message.info("当前数据集下没有可选文件");
      }
    } catch (error) {
      console.error("Failed to select all files in dataset", error);
      message.error("全选整个数据集失败，请稍后重试");
    } finally {
      setSelectingAll(false);
    }
  }, [selectedDataset, selectedFilesMap, onSelectedFilesChange]);

  const toggleSelectFile = (record: DatasetFile) => {
    // 被锁定的文件不允许在此组件中被增删
    if (lockedIdSet.has(String(record.id))) {
      return;
    }

    // 单数据集模式：禁止从多个数据集混选文件
    if (singleDatasetOnly && !selectedFilesMap[record.id]) {
      const recordDatasetId = (record as any).datasetId;
      const existingIds = new Set(
        Object.values(selectedFilesMap)
          .map((file: any) => file?.datasetId)
          .filter((id) => id !== undefined && id !== null && id !== "")
          .map((id) => String(id)),
      );
      const recId = recordDatasetId !== undefined && recordDatasetId !== null ? String(recordDatasetId) : undefined;
      if (existingIds.size > 0 && recId && !existingIds.has(recId)) {
        message.warning("当前仅支持从一个数据集选择文件，请先清空已选文件后再切换数据集");
        return;
      }
    }

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
      render: (text: string, record: Dataset) => {
        const active = selectedDataset?.id === record.id;
        return (
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex h-3 w-3 rounded-full border transition-colors duration-150 ${
                active ? "border-blue-500 bg-blue-500" : "border-gray-300 bg-white"
              }`}
            />
            <span className="truncate" title={text}>
              {text}
            </span>
          </div>
        );
      },
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
              onChange={(e) => !disabled && setDatasetSearch(e.target.value)}
              disabled={disabled}
            />
          </div>
          <Table
            scroll={{ y: 400 }}
            rowKey="id"
            size="small"
            rowClassName={(record) => {
              const isActive = selectedDataset?.id === record.id;
              const hasSelection = Object.keys(selectedFilesMap).length > 0;
              const isLockedOtherDataset =
                !!singleDatasetOnly &&
                !!lockedDatasetId &&
                hasSelection &&
                String(record.id) !== lockedDatasetId;
              return `cursor-pointer ${
                isActive ? "bg-blue-100" : ""
              } ${isLockedOtherDataset ? "text-gray-400 cursor-not-allowed" : ""}`;
            }}
            onRow={(record: Dataset) => ({
              onClick: () => {
                  if (disabled) return;

                  // 单数据集模式：当已有选中文件且尝试切换到其他数据集时，直接提示并阻止切换
                  const hasSelection =
                    singleDatasetOnly &&
                    Object.keys(selectedFilesMap).length > 0 &&
                    !!lockedDatasetId;
                  if (
                    hasSelection &&
                    String(record.id) !== String(lockedDatasetId)
                  ) {
                    message.warning(
                      "当前仅支持从一个数据集选择文件，请先清空已选文件后再切换数据集"
                    );
                    return;
                  }
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
                    !disabled &&
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
          <div className="border-bottom p-2 font-bold flex justify-between items-center">
            <span>选择文件</span>
            <Button
              type="link"
              size="small"
              onClick={() => !disabled && handleSelectAllInDataset()}
              disabled={!selectedDataset || !!disabled}
              loading={selectingAll}
            >
              全选当前数据集
            </Button>
          </div>
          <div className="p-2">
            <Input
              placeholder="搜索文件名称..."
              value={filesSearch}
              onChange={(e) => setFilesSearch(e.target.value)}
            />
          </div>
          <Table
            scroll={{ y: 400 }}
            rowKey={(record) => String(record.id)}
            size="small"
            dataSource={files}
            columns={fileCols.slice(1, fileCols.length)}
            pagination={{
              ...filesPagination,
              onChange: (page, pageSize) => {
                  if (disabled) return;
                const nextPageSize = pageSize || filesPagination.pageSize;
                setFilesPagination((prev) => ({
                  ...prev,
                  current: page,
                  pageSize: nextPageSize,
                }));
                // 前端分页与后端统一使用 1-based page 参数
                fetchFiles({ page, pageSize: nextPageSize }).catch(() => {});
              },
            }}
            onRow={(record: DatasetFile) => ({
              onClick: () => {
                if (disabled) return;
                toggleSelectFile(record);
              },
            })}
            rowSelection={{
              type: "checkbox",
              selectedRowKeys: Object.keys(selectedFilesMap),
              preserveSelectedRowKeys: true,

              // 单选
              onSelect: (record: DatasetFile) => {
                if (disabled) return;
                toggleSelectFile(record);
              },

              // 全选 - 改为全选整个数据集而不是当前页
              onSelectAll: (selected, selectedRows: DatasetFile[]) => {
                if (disabled) return;
                if (selected) {
                  // 点击表头“全选”时，改为一键全选当前数据集的全部文件
                  // 而不是只选中当前页
                  handleSelectAllInDataset();
                } else {
                  // 取消表头“全选”时，只清空当前数据集的已选文件，保留其它数据集
                  if (!selectedDataset) return;

                  const nextMap: { [key: string]: DatasetFile } = {};
                  Object.entries(selectedFilesMap).forEach(([key, file]) => {
                    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                    // @ts-ignore
                    const fileDatasetId = file.datasetId;
                    if (fileDatasetId !== selectedDataset.id) {
                      nextMap[key] = file;
                    }
                  });

                  onSelectedFilesChange(nextMap);
                }
              },

              getCheckboxProps: (record: DatasetFile) => ({
                name: record.fileName,
                disabled: !!disabled || lockedIdSet.has(String(record.id)),
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
