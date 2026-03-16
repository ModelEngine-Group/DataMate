import { App, Button, Modal, Table, Input, Spin } from "antd";
import { formatBytes, formatDateTime } from "@/utils/unit";
import { Download, Trash2, Folder, File } from "lucide-react";
import { getDatasetTypeMap } from "../../dataset.const";
import DeleteConfirmModal from "@/components/DeleteConfirmModal";
import FilePreview from "@/components/file-preview";
import { useTranslation } from "react-i18next";
import { useState } from "react";

export default function Overview({ dataset, filesOperation, fetchDataset }) {
  const { modal, message } = App.useApp();
  const { t } = useTranslation();
  const datasetTypeMap = getDatasetTypeMap(t);

  // 删除确认弹窗状态
  const [deleteModal, setDeleteModal] = useState<{
    visible: boolean;
    type: "file" | "directory" | "batch";
    fileName: string;
    count?: number;
    handler: () => void | Promise<void>;
  }>({
    visible: false,
    type: "file",
    fileName: "",
    handler: () => {},
  });

  // 批量删除确认弹窗状态
  const [batchDeleteModal, setBatchDeleteModal] = useState<{
    visible: boolean;
    count: number;
  }>({
    visible: false,
    count: 0,
  });

  const {
    fileList,
    pagination,
    selectedFiles,
    setSelectedFiles,
    clearSelection,
    previewVisible,
    previewFileName,
    previewContent,
    previewUrl,
    previewBlob,
    previewFileDetail,
    previewLoading,
    handlePreviewFile,
    setPreviewVisible,
    handleDeleteFile,
    handleDownloadFile,
    handleBatchDeleteFiles,
    handleBatchExport,
    handleSelectionChange,
    handleCreateDirectory,
    handleDownloadDirectory,
    handleDeleteDirectory,
    handleRenameFile,
    handleRenameDirectory,
  } = filesOperation;

  // 文件列表多选配置（支持跨页选择）
  const rowSelection = {
    selectedRowKeys: selectedFiles,
    onChange: handleSelectionChange,
    preserveSelectedRowKeys: true, // 关键：跨页时保持选中状态
    getCheckboxProps: (record: any) => ({
      // 目录和文件都可以选择
      name: record.fileName,
    }),
  };

  // 显示删除确认弹窗
  const showDeleteConfirm = (
    type: "file" | "directory",
    fileName: string,
    handler: () => void | Promise<void>
  ) => {
    setDeleteModal({
      visible: true,
      type,
      fileName,
      handler,
    });
  };

  // 执行删除操作
  const handleConfirmDelete = async () => {
    await deleteModal.handler();
    setDeleteModal({ visible: false, type: "file", fileName: "", handler: () => {} });
  };

  const handleCancelDelete = () => {
    setDeleteModal({ visible: false, type: "file", fileName: "", handler: () => {} });
  };

  // 显示批量删除确认弹窗
  const showBatchDeleteConfirm = () => {
    if (selectedFiles.length === 0) {
      message.warning({ content: "请先选择要删除的文件" });
      return;
    }
    setBatchDeleteModal({
      visible: true,
      count: selectedFiles.length,
    });
  };

  // 执行批量删除
  const handleConfirmBatchDelete = async () => {
    setBatchDeleteModal({ visible: false, count: 0 });
    await handleBatchDeleteFiles();
  };

  // 文件列表列定义
  const columns = [
    {
      title: t("dataManagement.columns.fileName"),
      dataIndex: "fileName",
      key: "fileName",
      fixed: "left",
      render: (text: string, record: any) => {
        const isDirectory = record.id.startsWith('directory-');
        const iconSize = 16;

        // 如果是通过文件夹上传生成的路径（包含目录），仅展示文件名部分
        const displayName = text?.split('/')?.filter(Boolean).pop() || text;

        const content = (
          <div className="flex items-center">
            {isDirectory ? (
              <Folder className="mr-2 text-blue-500" size={iconSize} />
            ) : (
              <File className="mr-2 text-black" size={iconSize} />
            )}
            <span className="truncate text-black">{displayName}</span>
          </div>
        );

        if (isDirectory) {
          return (
            <Button
              type="link"
              onClick={(e) => {
                const currentPath = filesOperation.pagination.prefix || '';
                // 文件夹路径必须以斜杠结尾
                const newPath = `${currentPath}${record.fileName}/`;
                filesOperation.fetchFiles(newPath, 1, filesOperation.pagination.pageSize);
              }}
              className="hover:text-blue-600 transition-colors duration-200"
              style={{
                padding: 0,
                height: 'auto',
                fontWeight: 500
              }}
            >
              <div className="flex items-center group">
                <Folder className="mr-2 text-blue-500 group-hover:text-blue-600 transition-colors" size={iconSize} />
                <span className="truncate underline-transparent group-hover:underline group-hover:text-blue-600 transition-all">
                  {displayName}
                </span>
              </div>
            </Button>
          );
        }

        return (
            <Button
              type="link"
              onClick={() => handlePreviewFile(record)}
              className="hover:text-blue-600 transition-colors duration-200"
              style={{
                padding: 0,
                height: 'auto',
                fontWeight: 500
              }}
            >
              <div className="flex items-center group">
                <File className="mr-2 text-black group-hover:text-blue-600 transition-colors" size={iconSize} />
                <span className="truncate underline-transparent group-hover:underline group-hover:text-blue-600 transition-all">
                  {displayName}
                </span>
              </div>
            </Button>
          );
      },
    },
    {
      title: t("dataManagement.columns.fileSize"),
      dataIndex: "fileSize",
      key: "fileSize",
      width: 150,
      render: (text: number, record: any) => {
        const isDirectory = record.id.startsWith('directory-');
        if (isDirectory) {
          return formatBytes(record.fileSize || 0);
        }
        return formatBytes(text)
      },
    },
    {
      title: t("dataManagement.columns.filesInFolder"),
      dataIndex: "fileCount",
      key: "fileCount",
      width: 120,
      render: (text: number, record: any) => {
        const isDirectory = record.id.startsWith('directory-');
        if (!isDirectory) {
          return t("dataManagement.defaults.empty");
        }
        return record.fileCount ?? 0;
      },
    },
    {
      title: t("dataManagement.columns.uploadTime"),
      dataIndex: "uploadTime",
      key: "uploadTime",
      width: 200,
      render: (text) => formatDateTime(text),
    },
    {
      title: t("dataManagement.columns.tags"),
      dataIndex: "tags",
      key: "tags",
      width: 220,
      render: (value: any, record: any) => {
        const isDirectory = typeof record.id === "string" && record.id.startsWith("directory-");
        if (isDirectory) return t("dataManagement.defaults.empty");

        let raw = value;
        if (!raw) return t("dataManagement.defaults.empty");

        // 后端目前将 tags 作为 JSON 字符串存储在 t_dm_dataset_files.tags 中
        // 这里尝试解析为 FileTag 数组结构 [{ type, from_name, values: { [type]: [...] } }]
        if (typeof raw === "string") {
          try {
            raw = JSON.parse(raw);
          } catch {
            // 解析失败则直接展示原始字符串
            return raw;
          }
        }

        if (!Array.isArray(raw) || raw.length === 0) return t("dataManagement.defaults.empty");

        const labels: string[] = [];
        raw.forEach((tag: any) => {
          const type = tag?.type;
          const valuesObj = tag?.values || {};
          const tagValues = (type && valuesObj[type]) || [];

          if (Array.isArray(tagValues)) {
            tagValues.forEach((item) => {
              if (typeof item === "string" && !labels.includes(item)) {
                labels.push(item);
              }
            });
          } else if (typeof tagValues === "string" && !labels.includes(tagValues)) {
            labels.push(tagValues);
          }
        });

        if (!labels.length) return t("dataManagement.defaults.empty");
        return labels.join(", ");
      },
    },
    {
      title: t("dataManagement.columns.tagsUpdatedAt"),
      dataIndex: "tagsUpdatedAt",
      key: "tagsUpdatedAt",
      width: 200,
      render: (text: any, record: any) => {
        const isDirectory = typeof record.id === "string" && record.id.startsWith("directory-");
        if (isDirectory) return t("dataManagement.defaults.empty");
        if (!text) return t("dataManagement.defaults.empty");
        return formatDateTime(text);
      },
    },
    {
      title: t("dataManagement.columns.actions"),
      key: "action",
      width: 180,
      fixed: "right",
      render: (_, record) => {
        const isDirectory = record.id.startsWith('directory-');
        
        if (isDirectory) {
          const currentPath = filesOperation.pagination.prefix || '';
          const fullPath = `${currentPath}${record.fileName}/`;
          
          return (
            <div className="flex">
              <Button
                size="small"
                type="link"
                onClick={() => handleDownloadDirectory(fullPath, record.fileName)}
              >
                {t("dataManagement.actions.download")}
              </Button>
              <Button
                size="small"
                type="link"
                onClick={() => {
                  let newDirName = record.fileName;
                  modal.confirm({
                    title: t("dataManagement.actions.renameFolder"),
                    content: (
                      <Input
                        autoFocus
                        defaultValue={record.fileName}
                        onChange={(e) => {
                          newDirName = e.target.value?.trim();
                        }}
                      />
                    ),
                    okText: t("dataManagement.actions.confirm"),
                    cancelText: t("dataManagement.actions.cancel"),
                    onOk: async () => {
                      if (!newDirName) {
                        message.warning(t("dataManagement.placeholders.folderName"));
                        return Promise.reject();
                      }
                      try {
                        await handleRenameDirectory(fullPath, record.fileName, newDirName);
                        fetchDataset();
                      } catch (error) {
                        // 错误已经在 handleRenameDirectory 中处理，这里只需要阻止 modal 关闭
                        return Promise.reject();
                      }
                    },
                  });
                }}
              >
                {t("dataManagement.actions.rename")}
              </Button>
              <Button
                size="small"
                type="link"
                onClick={() =>
                  showDeleteConfirm(
                    "directory",
                    record.fileName,
                    async () => {
                      await handleDeleteDirectory(fullPath, record.fileName);
                      fetchDataset();
                    }
                  )
                }
              >
                {t("dataManagement.actions.delete")}
              </Button>
            </div>
          );
        }
        
        return (
        <div className="flex">
          <Button
            size="small"
            type="link"
            onClick={() => handleDownloadFile(record)}
          >
            {t("dataManagement.actions.download")}
          </Button>
          <Button
            size="small"
            type="link"
            onClick={() => {
              const originalName = record.fileName || '';
              const dotIndex = originalName.lastIndexOf('.');
              const baseName = dotIndex > 0 ? originalName.slice(0, dotIndex) : originalName;
              const ext = dotIndex > 0 ? originalName.slice(dotIndex) : '';
              let newBaseName = baseName;

              modal.confirm({
                title: t("dataManagement.actions.renameFile"),
                content: (
                  <div className="space-y-2">
                    <Input
                      autoFocus
                      defaultValue={baseName}
                      addonAfter={ext}
                      onChange={(e) => {
                        newBaseName = e.target.value?.trim();
                      }}
                    />
                  </div>
                ),
                okText: t("dataManagement.actions.confirm"),
                cancelText: t("dataManagement.actions.cancel"),
                onOk: async () => {
                  if (!newBaseName) {
                    message.warning(t("dataManagement.placeholders.fileName"));
                    return Promise.reject();
                  }
                  try {
                    await handleRenameFile(record, newBaseName);
                    fetchDataset();
                  } catch (error) {
                    // 错误已经在 handleRenameFile 中处理，这里只需要阻止 modal 关闭
                    return Promise.reject();
                  }
                },
              });
            }}
          >
            {t("dataManagement.actions.rename")}
          </Button>
          <Button
            size="small"
            type="link"
            onClick={() =>
              showDeleteConfirm(
                "file",
                record.fileName,
                async () => {
                  await handleDeleteFile(record);
                  fetchDataset();
                }
              )
            }
          >
            {t("dataManagement.actions.delete")}
          </Button>
        </div>
      )},
    },
  ];

  return (
    <>
      <div className=" flex flex-col gap-4">
        {/* 文件列表 */}
        <div className="flex items-center justify-between mt-8 mb-2">
          <h2 className="text-base font-semibold">
            {t("dataManagement.detail.sectionFileList")}
          </h2>
          <Button
            type="primary"
            size="small"
            onClick={() => {
              let dirName = "";
              modal.confirm({
                title: t("dataManagement.actions.createFolder"),
                content: (
                  <Input
                    autoFocus
                    placeholder={t("dataManagement.placeholders.folderName")}
                    onChange={(e) => {
                      dirName = e.target.value?.trim();
                    }}
                  />
                ),
                okText: t("dataManagement.actions.confirm"),
                cancelText: t("dataManagement.actions.cancel"),
                onOk: async () => {
                  if (!dirName) {
                    message.warning(t("dataManagement.placeholders.folderName"));
                    return Promise.reject();
                  }
                  await handleCreateDirectory(dirName);
                },
              });
            }}
          >
            {t("dataManagement.actions.createFolder")}
          </Button>
        </div>
        {selectedFiles.length > 0 && (
          <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <span className="text-sm text-blue-700 font-medium">
              已选择 {selectedFiles.length} 项
              {(() => {
                const dirCount = selectedFiles.filter(id => typeof id === 'string' && id.startsWith('directory-')).length;
                const fileCount = selectedFiles.length - dirCount;
                if (dirCount > 0 && fileCount > 0) {
                  return ` (${fileCount} 个文件, ${dirCount} 个文件夹)`;
                } else if (dirCount > 0) {
                  return ` (${dirCount} 个文件夹)`;
                } else if (fileCount > 0) {
                  return ` (${fileCount} 个文件)`;
                }
                return '';
              })()}
            </span>
            <Button
              onClick={clearSelection}
              className="ml-auto"
            >
              取消选择
            </Button>
            <Button
              onClick={handleBatchExport}
              className="bg-white"
            >
              <Download className="w-4 h-4 mr-2" />
              {t("dataManagement.actions.batchExport")}
            </Button>
            <Button
              onClick={showBatchDeleteConfirm}
              danger
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {t("dataManagement.actions.batchDelete")}
            </Button>
          </div>
        )}
        <div className="overflow-x-auto">
          <div className="mb-2">
            {(filesOperation.pagination.prefix || '') !== '' && (
              <Button
                type="link"
                onClick={() => {
                  // 获取上一级目录
                  const currentPath = filesOperation.pagination.prefix || '';
                  // 移除末尾的斜杠，然后按斜杠分割
                  const trimmedPath = currentPath.replace(/\/$/, '');
                  const pathParts = trimmedPath.split('/');
                  // 移除最后一个目录名
                  pathParts.pop();
                  // 重新组合路径，如果还有内容则加斜杠，否则为空
                  const parentPath = pathParts.length > 0 ? `${pathParts.join('/')}/` : '';
                  filesOperation.fetchFiles(parentPath, 1, filesOperation.pagination.pageSize);
                }}
                className="p-0"
              >
                <span className="flex items-center text-blue-500">
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 19l-7-7m0 0l7-7m-7 7h18"
                    />
                  </svg>
                  {t("dataManagement.detail.goUp")}
                </span>
              </Button>
            )}
            {filesOperation.pagination.prefix && (
              <span className="ml-2 text-gray-600">
                {t("dataManagement.detail.currentPath", {
                  path: filesOperation.pagination.prefix,
                })}
              </span>
            )}
          </div>
          <Table
            size="middle"
            rowKey="id"
            columns={columns}
            dataSource={fileList}
            rowSelection={rowSelection}
            scroll={{ x: "max-content" }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showTotal: (total) => t("dataManagement.detail.totalItems", { total }),
              showSizeChanger: true,
              pageSizeOptions: [10, 20, 50, 100],
              onChange: (page, pageSize) => {
                filesOperation.fetchFiles(filesOperation.pagination.prefix, page, pageSize);
              }
            }}
          />
        </div>
      </div>
      {/* 文件预览弹窗 */}
      <Modal
        title={t("dataManagement.detail.previewTitle", { name: previewFileName })}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={1200}
        styles={{ body: { padding: 0 } }}
      >
        <div className="flex gap-4" style={{ minHeight: 600, height: 600 }}>
          {/* 左侧预览区域 */}
          <div className="flex-1 border border-gray-200 rounded-md overflow-hidden">
            <FilePreview
              fileName={previewFileName}
              content={previewContent}
              blobUrl={previewUrl}
              blob={previewBlob}
              loading={previewLoading}
            />
          </div>

          {/* 右侧文件信息（来自 t_dm_dataset_files） */}
          <div className="w-72 border border-gray-200 rounded-md p-3 bg-white overflow-auto">
            <h3 className="text-sm font-semibold mb-3">
              {t("dataManagement.detail.previewInfoTitle")}
            </h3>
            <div className="space-y-2 text-xs text-gray-700">
              <div>
                <span className="text-gray-500">
                  {t("dataManagement.labels.fileName")}：
                </span>
                <span>{previewFileDetail?.fileName || previewFileName}</span>
              </div>
              {previewFileDetail?.originalName && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.originalName")}：
                  </span>
                  <span>{previewFileDetail.originalName}</span>
                </div>
              )}
              {previewFileDetail?.fileType && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.fileType")}：
                  </span>
                  <span>{previewFileDetail.fileType}</span>
                </div>
              )}
              {typeof previewFileDetail?.fileSize === "number" && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.fileSize")}：
                  </span>
                  <span>{formatBytes(previewFileDetail.fileSize || 0)}</span>
                </div>
              )}
              {previewFileDetail?.status && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.status")}：
                  </span>
                  <span>{previewFileDetail.status}</span>
                </div>
              )}
              {previewFileDetail?.tags && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.tags")}：
                  </span>
                  <span>
                    {(() => {
                      let raw = previewFileDetail.tags as any;
                      if (!raw) return t("dataManagement.defaults.empty");

                      if (typeof raw === "string") {
                        try {
                          raw = JSON.parse(raw);
                        } catch {
                          return raw;
                        }
                      }

                      if (!Array.isArray(raw) || raw.length === 0) {
                        return t("dataManagement.defaults.empty");
                      }

                      const labels: string[] = [];
                      raw.forEach((tag: any) => {
                        const type = tag?.type;
                        const valuesObj = tag?.values || {};
                        const tagValues = (type && valuesObj[type]) || [];

                        if (Array.isArray(tagValues)) {
                          tagValues.forEach((item) => {
                            if (typeof item === "string" && !labels.includes(item)) {
                              labels.push(item);
                            }
                          });
                        } else if (typeof tagValues === "string" && !labels.includes(tagValues)) {
                          labels.push(tagValues);
                        }
                      });

                      if (!labels.length) return t("dataManagement.defaults.empty");
                      return labels.join(", ");
                    })()}
                  </span>
                </div>
              )}
              {previewFileDetail?.tagsUpdatedAt && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.tagsUpdatedAt")}：
                  </span>
                  <span>{formatDateTime(previewFileDetail.tagsUpdatedAt)}</span>
                </div>
              )}
              {previewFileDetail?.uploadTime && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.uploadTime")}：
                  </span>
                  <span>{formatDateTime(previewFileDetail.uploadTime)}</span>
                </div>
              )}
              {previewFileDetail?.uploadedBy && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.uploadedBy")}：
                  </span>
                  <span>{previewFileDetail.uploadedBy}</span>
                </div>
              )}
              {previewFileDetail?.filePath && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.filePath")}：
                  </span>
                  <span>{previewFileDetail.filePath}</span>
                </div>
              )}
              {previewFileDetail?.description && (
                <div>
                  <span className="text-gray-500">
                    {t("dataManagement.labels.description")}：
                  </span>
                  <span>{previewFileDetail.description}</span>
                </div>
              )}
              <div>
                <span className="text-gray-500">
                  {t("dataManagement.labels.annotation")}：
                </span>
                <span>
                  {(() => {
                    const raw = previewFileDetail?.tags as any;
                    if (!raw) return "-";

                    if (typeof raw === "string") {
                      return raw;
                    }

                    try {
                      return JSON.stringify(raw);
                    } catch {
                      return "-";
                    }
                  })()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Modal>
      {/* 删除确认弹窗 */}
      <DeleteConfirmModal
        visible={deleteModal.visible}
        title={
          deleteModal.type === "directory"
            ? t("dataManagement.confirm.deleteFolderTitle")
            : t("dataManagement.confirm.deleteFileTitle")
        }
        message={
          deleteModal.type === "directory"
            ? t("dataManagement.confirm.deleteFolderDesc", { itemName: deleteModal.fileName })
            : t("dataManagement.confirm.deleteFileDesc", { itemName: deleteModal.fileName })
        }
        itemName={deleteModal.fileName}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
      />

      {/* 批量删除确认弹窗 */}
      <Modal
        title={t("dataManagement.confirm.batchDeleteTitle")}
        open={batchDeleteModal.visible}
        onOk={handleConfirmBatchDelete}
        onCancel={() => setBatchDeleteModal({ visible: false, count: 0 })}
        okText={t("dataManagement.confirm.deleteConfirm")}
        cancelText={t("dataManagement.confirm.deleteCancel")}
        okButtonProps={{ danger: true }}
      >
        <p>
          {t("dataManagement.confirm.batchDeleteDesc", {
            count: batchDeleteModal.count,
          })}
        </p>
      </Modal>
    </>
  );
}
