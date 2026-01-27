import {Button, Modal, Table, Badge, Input, Popover} from "antd";
import { Download } from "lucide-react";
import {useEffect, useState} from "react";
import {useParams} from "react-router";
import {TaskStatus} from "@/pages/DataCleansing/cleansing.model.ts";
import {TaskStatusMap} from "@/pages/DataCleansing/cleansing.const.tsx";

// 模拟文件列表数据
export default function FileTable({result, fetchTaskResult}) {
  const { id = "" } = useParams();
  const [showFileCompareDialog, setShowFileCompareDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);

  useEffect(() => {
    fetchTaskResult();
  }, [id]);

  const handleSelectAllFiles = (checked: boolean) => {
    if (checked) {
      setSelectedFileIds(result.map((file) => file.instanceId));
    } else {
      setSelectedFileIds([]);
    }
  };

  const handleSelectFile = (fileId: string, checked: boolean) => {
    if (checked) {
      setSelectedFileIds([...selectedFileIds, fileId]);
    } else {
      setSelectedFileIds(selectedFileIds.filter((id) => id !== fileId));
    }
  };
  const handleViewFileCompare = (file: any) => {
    setSelectedFile(file);
    setShowFileCompareDialog(true);
  };
  const handleBatchDownload = () => {
    // 实际下载逻辑
  };

  function formatFileSize(bytes: number, decimals: number = 2): string {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
  }

  const fileColumns = [
    {
      title: (
        <input
          type="checkbox"
          checked={
            selectedFileIds.length === result?.length && result?.length > 0
          }
          onChange={(e) => handleSelectAllFiles(e.target.checked)}
          className="w-4 h-4"
        />
      ),
      dataIndex: "select",
      key: "select",
      width: 50,
      render: (_text: string, record: any) => (
        <input
          type="checkbox"
          checked={selectedFileIds.includes(record.id)}
          onChange={(e) => handleSelectFile(record.id, e.target.checked)}
          className="w-4 h-4"
        />
      ),
    },
    {
      title: "文件名",
      dataIndex: "srcName",
      key: "srcName",
      width: 200,
      filterDropdown: ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
      }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索文件名"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              搜索
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              重置
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) =>
        record.srcName.toLowerCase().includes(value.toLowerCase()),
      render: (text: string) => (
        <span>{text?.replace(/\.[^/.]+$/, "")}</span>
      ),
    },
    {
      title: "处理后文件名",
      dataIndex: "destName",
      key: "destName",
      width: 200,
      filterDropdown: ({
                         setSelectedKeys,
                         selectedKeys,
                         confirm,
                         clearFilters,
                       }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索文件名"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              搜索
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              重置
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) =>
        record.destName.toLowerCase().includes(value.toLowerCase()),
      render: (text: string) => (
        <span>{text?.replace(/\.[^/.]+$/, "")}</span>
      ),
    },
    {
      title: "文件类型",
      dataIndex: "srcType",
      key: "srcType",
      filterDropdown: ({
                         setSelectedKeys,
                         selectedKeys,
                         confirm,
                         clearFilters,
                       }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索文件类型"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              搜索
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              重置
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) =>
        record.srcType.toLowerCase().includes(value.toLowerCase()),
      render: (text: string) => (
        <span className="font-mono text-sm">{text}</span>
      ),
    },
    {
      title: "处理后文件类型",
      dataIndex: "destType",
      key: "destType",
      filterDropdown: ({
                         setSelectedKeys,
                         selectedKeys,
                         confirm,
                         clearFilters,
                       }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索文件类型"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              搜索
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              重置
            </Button>
          </div>
        </div>
      ),
      onFilter: (value: string, record: any) =>
        record.destType.toLowerCase().includes(value.toLowerCase()),
      render: (text: string) => (
        <span className="font-mono text-sm">{text || "-"}</span>
      ),
    },
    {
      title: "处理前大小",
      dataIndex: "srcSize",
      key: "srcSize",
      sorter: (a: any, b: any) => {
        const getSizeInBytes = (size: string) => {
          if (!size || size === "-") return 0;
          const num = Number.parseFloat(size);
          if (size.includes("GB")) return num * 1024 * 1024 * 1024;
          if (size.includes("MB")) return num * 1024 * 1024;
          if (size.includes("KB")) return num * 1024;
          return num;
        };
        return getSizeInBytes(a.originalSize) - getSizeInBytes(b.originalSize);
      },
      render: (number: number) => (
        <span className="font-mono text-sm">{formatFileSize(number)}</span>
      ),
    },
    {
      title: "处理后大小",
      dataIndex: "destSize",
      key: "destSize",
      sorter: (a: any, b: any) => {
        const getSizeInBytes = (size: string) => {
          if (!size || size === "-") return 0;
          const num = Number.parseFloat(size);
          if (size.includes("GB")) return num * 1024 * 1024 * 1024;
          if (size.includes("MB")) return num * 1024 * 1024;
          if (size.includes("KB")) return num * 1024;
          return num;
        };
        return (
          getSizeInBytes(a.processedSize) - getSizeInBytes(b.processedSize)
        );
      },
      render: (number: number) => (
        <span className="font-mono text-sm">{formatFileSize(number)}</span>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      filters: [
        { text: "已完成", value: "COMPLETED" },
        { text: "失败", value: "FAILED" },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === "COMPLETED"
              ? "success"
              : "error"
          }
          text={TaskStatusMap[status as TaskStatus].label}
        />
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 200,
      render: (_text: string, record: any) => (
        <div className="flex">
          {record.status === "COMPLETED" ? (
            <Button
              type="link"
              size="small"
              onClick={() => handleViewFileCompare(record)}
            >
              对比
            </Button>
          ) : (
            <Button
              type="link"
              size="small"
              disabled
            >
              对比
            </Button>
          )}
          <Popover content="暂未开放">
              <Button type="link" size="small" disabled>下载</Button>
          </Popover>
        </div>
      ),
    },
  ];

  return (
    <>
      {selectedFileIds.length > 0 && (
        <div className="mb-4 flex justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              已选择 {selectedFileIds.length} 个文件
            </span>
            <Button
              onClick={handleBatchDownload}
              size="small"
              type="primary"
              icon={<Download className="w-4 h-4 mr-2" />}
            >
              批量下载
            </Button>
          </div>
        </div>
      )}
      <Table
        columns={fileColumns}
        dataSource={result}
        pagination={{ pageSize: 10, showSizeChanger: true }}
        size="middle"
        rowKey="id"
      />

      {/* 文件对比弹窗 */}
      <Modal
        open={showFileCompareDialog}
        onCancel={() => setShowFileCompareDialog(false)}
        footer={null}
        width={900}
        title={<span>文件对比 - {selectedFile?.fileName}</span>}
      >
        <div className="grid grid-cols-2 gap-6 py-6">
          <div>
            <h4 className="font-medium text-gray-900">处理前</h4>
            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-48 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-gray-300 rounded-lg mx-auto mb-2" />
                <div className="text-sm">原始文件预览</div>
                <div className="text-xs text-gray-400">
                  大小: {formatFileSize(selectedFile?.srcSize)}
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-3 space-y-1">
              <div>
                <span className="font-medium">文件格式:</span> {selectedFile?.srcType}
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">处理后</h4>
            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-48 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-blue-300 rounded-lg mx-auto mb-2" />
                <div className="text-sm">处理后文件预览</div>
                <div className="text-xs text-gray-400">
                  大小: {formatFileSize(selectedFile?.destSize)}
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-3 space-y-1">
              <div>
                <span className="font-medium">文件格式:</span> {selectedFile?.destType}
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-gray-200 mt-6 pt-4">
          <h4 className="font-medium text-gray-900 mb-3">处理效果对比</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="font-medium text-green-700">文件大小优化</div>
              <div className="text-green-600">减少了 {(100 * (selectedFile?.srcSize - selectedFile?.destSize) / selectedFile?.srcSize).toFixed(2)}%</div>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
