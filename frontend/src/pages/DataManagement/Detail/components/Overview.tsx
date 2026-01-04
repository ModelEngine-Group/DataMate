import { App, Button, Descriptions, DescriptionsProps, Modal, Table, Input } from "antd";
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
    setPreviewVisible,
    handleDeleteFile,
    handleDownloadFile,
    handleBatchDeleteFiles,
    handleBatchExport,
    handleCreateDirectory,
    handleDownloadDirectory,
    handleDeleteDirectory,
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

        const content = (
          <div className="flex items-center">
            {isDirectory ? (
              <Folder className="mr-2 text-blue-500" size={iconSize} />
            ) : (
              <File className="mr-2 text-black" size={iconSize} />
            )}
            <span className="truncate text-black">{text}</span>
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
              onClick={(e) => {}}
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
        width={700}
      >
        <pre
          style={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
            fontSize: 14,
            color: "#222",
          }}
        >
          {previewContent}
        </pre>
      </Modal>
    </>
  );
}
