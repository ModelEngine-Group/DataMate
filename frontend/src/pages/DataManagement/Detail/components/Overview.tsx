import { Button, Descriptions, DescriptionsProps, Modal, Table } from "antd";
import { formatBytes, formatDateTime } from "@/utils/unit";
import { Download, Trash2 } from "lucide-react";
import { datasetTypeMap } from "../../dataset.const";

export default function Overview({ dataset, filesOperation, fetchDataset }) {
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
    },
    {
      title: "大小",
      dataIndex: "fileSize",
      key: "fileSize",
      width: 150,
      render: (text) => formatBytes(text),
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
      render: (_, record) => (
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
      ),
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
        <h2 className="text-base font-semibold mt-8">文件列表</h2>
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
