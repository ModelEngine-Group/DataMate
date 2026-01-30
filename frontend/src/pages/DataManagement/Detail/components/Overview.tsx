import { App, Button, Descriptions, DescriptionsProps, Modal, Table, Input, Spin } from "antd";
import { formatBytes, formatDateTime } from "@/utils/unit";
import { Download, Trash2, Folder, File } from "lucide-react";
import { datasetTypeMap } from "../../dataset.const";

export default function Overview({ dataset, filesOperation, fetchDataset }) {
  const { modal, message } = App.useApp();
  const {
    fileList,
    pagination,
    selectedFiles,
    setSelectedFiles,
    previewVisible,
    previewFileName,
    previewContent,
    previewUrl,
    previewFileDetail,
    previewLoading,
    setPreviewVisible,
    handleDeleteFile,
    handleDownloadFile,
    handleBatchDeleteFiles,
    handleBatchExport,
    handleCreateDirectory,
    handleDownloadDirectory,
    handleDeleteDirectory,
    handleRenameFile,
    handleRenameDirectory,
    handlePreviewFile,
  } = filesOperation;

  // 文件列表多选配置
  const rowSelection = {
    onChange: (selectedRowKeys: React.Key[], selectedRows: any[]) => {
      setSelectedFiles(selectedRowKeys as number[]);
      console.log(
        `selectedRowKeys: ${selectedRowKeys}`,
        "selectedRows: ",
        selectedRows
      );
    },
  };
  // 基本信息
  const items: DescriptionsProps["items"] = [
    {
      key: "id",
      label: "ID",
      children: dataset.id,
    },
    {
      key: "name",
      label: "名称",
      children: dataset.name,
    },
    {
      key: "fileCount",
      label: "文件数",
      children: dataset.fileCount || 0,
    },
    {
      key: "size",
      label: "数据大小",
      children: dataset.size || "0 B",
    },

    {
      key: "datasetType",
      label: "类型",
      children: datasetTypeMap[dataset?.datasetType]?.label || "未知",
    },
    {
      key: "status",
      label: "状态",
      children: dataset?.status?.label || "未知",
    },
    {
      key: "createdBy",
      label: "创建者",
      children: dataset.createdBy || "未知",
    },
    {
      key: "targetLocation",
      label: "存储路径",
      children: dataset.targetLocation || "未知",
    },
    {
      key: "pvcName",
      label: "存储名称",
      children: dataset.pvcName || "未知",
    },
    {
      key: "createdAt",
      label: "创建时间",
      children: dataset.createdAt,
    },
    {
      key: "updatedAt",
      label: "更新时间",
      children: dataset.updatedAt,
    },
    {
      key: "description",
      label: "描述",
      children: dataset.description || "无",
    },
  ];

  // 文件列表列定义
  const columns = [
    {
      title: "文件名",
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
            >
              {content}
            </Button>
          );
        }

        return (
            <Button
              type="link"
              onClick={() => handlePreviewFile(record)}
            >
              {content}
            </Button>
          );
      },
    },
    {
      title: "大小",
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
      title: "包含文件数",
      dataIndex: "fileCount",
      key: "fileCount",
      width: 120,
      render: (text: number, record: any) => {
        const isDirectory = record.id.startsWith('directory-');
        if (!isDirectory) {
          return "-";
        }
        return record.fileCount ?? 0;
      },
    },
    {
      title: "上传时间",
      dataIndex: "uploadTime",
      key: "uploadTime",
      width: 200,
      render: (text) => formatDateTime(text),
    },
    {
      title: "标签",
      dataIndex: "tags",
      key: "tags",
      width: 220,
      render: (value: any, record: any) => {
        const isDirectory = typeof record.id === "string" && record.id.startsWith("directory-");
        if (isDirectory) return "-";

        let raw = value;
        if (!raw) return "-";

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

        if (!Array.isArray(raw) || raw.length === 0) return "-";

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

        if (!labels.length) return "-";
        return labels.join(", ");
      },
    },
    {
      title: "标签更新时间",
      dataIndex: "tagsUpdatedAt",
      key: "tagsUpdatedAt",
      width: 200,
      render: (text: any, record: any) => {
        const isDirectory = typeof record.id === "string" && record.id.startsWith("directory-");
        if (isDirectory) return "-";
        if (!text) return "-";
        return formatDateTime(text);
      },
    },
    {
      title: "操作",
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
                下载
              </Button>
              <Button
                size="small"
                type="link"
                onClick={() => {
                  let newDirName = record.fileName;
                  modal.confirm({
                    title: '重命名文件夹',
                    content: (
                      <Input
                        autoFocus
                        defaultValue={record.fileName}
                        onChange={(e) => {
                          newDirName = e.target.value?.trim();
                        }}
                      />
                    ),
                    okText: '确定',
                    cancelText: '取消',
                    onOk: async () => {
                      if (!newDirName) {
                        message.warning('请输入文件夹名称');
                        return Promise.reject();
                      }
                      await handleRenameDirectory(fullPath, record.fileName, newDirName);
                      fetchDataset();
                    },
                  });
                }}
              >
                重命名
              </Button>
              <Button
                size="small"
                type="link"
                onClick={() => {
                  modal.confirm({
                    title: '确认删除文件夹？',
                    content: `删除文件夹 "${record.fileName}" 将同时删除其中的所有文件和子文件夹，此操作不可恢复。`,
                    okText: '删除',
                    okType: 'danger',
                    cancelText: '取消',
                    onOk: async () => {
                      await handleDeleteDirectory(fullPath, record.fileName);
                      fetchDataset();
                    },
                  });
                }}
              >
                删除
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
            下载
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
                title: '重命名文件',
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
                okText: '确定',
                cancelText: '取消',
                onOk: async () => {
                  if (!newBaseName) {
                    message.warning('请输入文件名称');
                    return Promise.reject();
                  }
                  await handleRenameFile(record, newBaseName);
                  fetchDataset();
                },
              });
            }}
          >
            重命名
          </Button>
          <Button
            size="small"
            type="link"
            onClick={async () => {
              await handleDeleteFile(record);
              fetchDataset()
            }
          }
          >
            删除
          </Button>
        </div>
      )},
    },
  ];

  return (
    <>
      <div className=" flex flex-col gap-4">
        {/* 基本信息 */}
        <Descriptions
          title="基本信息"
          layout="vertical"
          size="small"
          items={items}
          column={5}
        />

        {/* 文件列表 */}
        <div className="flex items-center justify-between mt-8 mb-2">
          <h2 className="text-base font-semibold">文件列表</h2>
          <Button
            type="primary"
            size="small"
            onClick={() => {
              let dirName = "";
              modal.confirm({
                title: "新建文件夹",
                content: (
                  <Input
                    autoFocus
                    placeholder="请输入文件夹名称"
                    onChange={(e) => {
                      dirName = e.target.value?.trim();
                    }}
                  />
                ),
                okText: "确定",
                cancelText: "取消",
                onOk: async () => {
                  if (!dirName) {
                    message.warning("请输入文件夹名称");
                    return Promise.reject();
                  }
                  await handleCreateDirectory(dirName);
                },
              });
            }}
          >
            新建文件夹
          </Button>
        </div>
        {selectedFiles.length > 0 && (
          <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <span className="text-sm text-blue-700 font-medium">
              已选择 {selectedFiles.length} 个文件
            </span>
            <Button
              onClick={handleBatchExport}
              className="ml-auto bg-transparent"
            >
              <Download className="w-4 h-4 mr-2" />
              批量导出
            </Button>
            <Button
              onClick={handleBatchDeleteFiles}
              className="text-red-600 hover:text-red-700 hover:bg-red-50 bg-transparent"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              批量删除
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
                  返回上一级
                </span>
              </Button>
            )}
            {filesOperation.pagination.prefix && (
              <span className="ml-2 text-gray-600">当前路径: {filesOperation.pagination.prefix}</span>
            )}
          </div>
          <Table
            size="middle"
            rowKey="id"
            columns={columns}
            dataSource={fileList}
            // rowSelection={rowSelection}
            scroll={{ x: "max-content", y: 600 }}
            pagination={{
              ...pagination,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (page, pageSize) => {
                filesOperation.fetchFiles(filesOperation.pagination.prefix, page, pageSize);
              }
            }}
          />
        </div>
      </div>
      {/* 文件预览弹窗 */}
      <Modal
        title={`文件预览：${previewFileName}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={1000}
      >
        <div className="flex gap-4" style={{ minHeight: 400 }}>
          {/* 左侧预览区域 */}
          <div className="flex-1 border border-gray-200 rounded-md p-3 flex items-center justify-center overflow-auto bg-gray-50">
            {previewLoading ? (
              <Spin />
            ) : previewUrl ? (
              <img
                src={previewUrl}
                alt={previewFileName}
                style={{
                  maxWidth: "100%",
                  maxHeight: 500,
                  objectFit: "contain",
                }}
              />
            ) : previewContent ? (
              <pre
                style={{
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  fontSize: 14,
                  color: "#222",
                  maxHeight: 500,
                }}
              >
                {previewContent}
              </pre>
            ) : (
              <span className="text-gray-500 text-sm">
                暂无预览内容，或当前文件类型暂不支持预览。
              </span>
            )}
          </div>

          {/* 右侧文件信息（来自 t_dm_dataset_files） */}
          <div className="w-72 border border-gray-200 rounded-md p-3 bg-white overflow-auto">
            <h3 className="text-sm font-semibold mb-3">文件信息</h3>
            <div className="space-y-2 text-xs text-gray-700">
              <div>
                <span className="text-gray-500">文件名：</span>
                <span>{previewFileDetail?.fileName || previewFileName}</span>
              </div>
              {previewFileDetail?.originalName && (
                <div>
                  <span className="text-gray-500">原始文件名：</span>
                  <span>{previewFileDetail.originalName}</span>
                </div>
              )}
              {previewFileDetail?.fileType && (
                <div>
                  <span className="text-gray-500">文件类型：</span>
                  <span>{previewFileDetail.fileType}</span>
                </div>
              )}
              {typeof previewFileDetail?.fileSize === "number" && (
                <div>
                  <span className="text-gray-500">文件大小：</span>
                  <span>{formatBytes(previewFileDetail.fileSize || 0)}</span>
                </div>
              )}
              {previewFileDetail?.status && (
                <div>
                  <span className="text-gray-500">状态：</span>
                  <span>{previewFileDetail.status}</span>
                </div>
              )}
              {previewFileDetail?.tags && (
                <div>
                  <span className="text-gray-500">标签：</span>
                  <span>
                    {(() => {
                      let raw = previewFileDetail.tags as any;
                      if (!raw) return "-";

                      if (typeof raw === "string") {
                        try {
                          raw = JSON.parse(raw);
                        } catch {
                          return raw;
                        }
                      }

                      if (!Array.isArray(raw) || raw.length === 0) return "-";

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

                      if (!labels.length) return "-";
                      return labels.join(", ");
                    })()}
                  </span>
                </div>
              )}
              {previewFileDetail?.tagsUpdatedAt && (
                <div>
                  <span className="text-gray-500">标签更新时间：</span>
                  <span>{formatDateTime(previewFileDetail.tagsUpdatedAt)}</span>
                </div>
              )}
              {previewFileDetail?.uploadTime && (
                <div>
                  <span className="text-gray-500">上传时间：</span>
                  <span>{formatDateTime(previewFileDetail.uploadTime)}</span>
                </div>
              )}
              {previewFileDetail?.uploadedBy && (
                <div>
                  <span className="text-gray-500">上传者：</span>
                  <span>{previewFileDetail.uploadedBy}</span>
                </div>
              )}
              {previewFileDetail?.filePath && (
                <div>
                  <span className="text-gray-500">文件路径：</span>
                  <span>{previewFileDetail.filePath}</span>
                </div>
              )}
              {previewFileDetail?.description && (
                <div>
                  <span className="text-gray-500">描述：</span>
                  <span>{previewFileDetail.description}</span>
                </div>
              )}
              <div>
                <span className="text-gray-500">标注信息：</span>
                <span>
                  {(() => {
                    const raw = (previewFileDetail?.annotation 
                      ?? previewFileDetail?.metadata 
                      ?? previewFileDetail?.tags) as any;
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
    </>
  );
}
