import {Button, Modal, Table, Badge, Input, Popover} from "antd";
import { Download } from "lucide-react";
import {useEffect, useState} from "react";
import {useParams} from "react-router";
import {TaskStatus} from "@/pages/DataCleansing/cleansing.model.ts";
import {getTaskStatusMap} from "@/pages/DataCleansing/cleansing.const.tsx";
import { useTranslation } from "react-i18next";

// 渲染 JSON 值的辅助组件
function JsonValue({ value, depth = 0 }: { value: any; depth?: number }) {
  if (value === null) {
    return <span className="text-gray-500">null</span>;
  }
  if (value === undefined) {
    return <span className="text-gray-500">undefined</span>;
  }
  if (typeof value === 'boolean') {
    return <span className="text-purple-600">{value.toString()}</span>;
  }
  if (typeof value === 'number') {
    return <span className="text-blue-600">{value}</span>;
  }
  if (typeof value === 'string') {
    // 处理换行符，保留空白格式
    const lines = value.split('\n');
    if (lines.length > 1) {
      return (
        <span className="text-green-700">
          {lines.map((line, i) => (
            <span key={i}>
              {line}
              {i < lines.length - 1 && <br />}
            </span>
          ))}
        </span>
      );
    }
    return <span className="text-green-700">{value}</span>;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-gray-500">[]</span>;
    }
    return (
      <div className="pl-3 border-l-2 border-gray-200">
        {value.map((item, i) => (
          <div key={i} className="py-0.5">
            <span className="text-gray-400 mr-1">[{i}]</span>
            <JsonValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === 'object') {
    const keys = Object.keys(value);
    if (keys.length === 0) {
      return <span className="text-gray-500">{"{}"}</span>;
    }
    return (
      <div className="pl-3 border-l-2 border-gray-200">
        {keys.map((key) => (
          <div key={key} className="py-0.5">
            <span className="text-blue-800 font-medium">{key}</span>
            <span className="text-gray-500 mx-1">:</span>
            <JsonValue value={value[key]} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

// 模拟文件列表数据
export default function FileTable({result, fetchTaskResult}) {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const [showFileCompareDialog, setShowFileCompareDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);

  useEffect(() => {
    fetchTaskResult();
  }, [id]);

  const handleSelectAllFiles = (checked: boolean) => {
    if (checked) {
      setSelectedFileIds(result.map((file) => file.srcFileId));
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
  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/cleaning/tasks/${id}/result/download`);
      if (!response.ok) {
        throw new Error('Download failed');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `task_${id}_files.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      message.error(t("dataCleansing.detail.fileTable.downloadFilesFailed"));
    }
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
          checked={selectedFileIds.includes(record.srcFileId)}
          onChange={(e) => handleSelectFile(record.srcFileId, e.target.checked)}
          className="w-4 h-4"
        />
      ),
    },
    {
      title: t("dataCleansing.detail.fileTable.fileName"),
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
            placeholder={t("dataCleansing.detail.fileTable.searchFileName")}
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              {t("dataCleansing.actions.search")}
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              {t("dataCleansing.actions.reset")}
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
      title: t("dataCleansing.detail.fileTable.processedFileName"),
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
            placeholder={t("dataCleansing.detail.fileTable.searchFileName")}
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              {t("dataCleansing.actions.search")}
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              {t("dataCleansing.actions.reset")}
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
      title: t("dataCleansing.detail.fileTable.fileType"),
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
            placeholder={t("dataCleansing.detail.fileTable.searchFileType")}
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              {t("dataCleansing.actions.search")}
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              {t("dataCleansing.actions.reset")}
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
      title: t("dataCleansing.detail.fileTable.processedFileType"),
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
            placeholder={t("dataCleansing.detail.fileTable.searchFileType")}
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            className="mb-2"
          />
          <div className="flex gap-2">
            <Button size="small" onClick={() => confirm()}>
              {t("dataCleansing.actions.search")}
            </Button>
            <Button size="small" onClick={() => clearFilters()}>
              {t("dataCleansing.actions.reset")}
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
      title: t("dataCleansing.detail.fileTable.beforeSize"),
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
      title: t("dataCleansing.detail.fileTable.afterSize"),
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
      title: t("dataCleansing.detail.fileTable.result"),
      dataIndex: "result",
      key: "result",
      width: 120,
      render: (text: string, record: any) => {
        // 如果结果为空或特殊值，则不展示
        if (!text || text === '' || text === '{}' || text === '[]' ||
            text === 'null' || text === 'undefined' || text.trim() === '') {
          return <span className="text-gray-400">-</span>;
        }

        // 尝试解析JSON
        try {
          const parsed = JSON.parse(text);

          // 如果是空对象或空数组则不展示
          if (Array.isArray(parsed) && parsed.length === 0) {
            return <span className="text-gray-400">-</span>;
          }
          if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed) && Object.keys(parsed).length === 0) {
            return <span className="text-gray-400">-</span>;
          }

          // 检查 reason 字段：如果只有 reason 且为 null/空，则不展示
          if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {

            const keys = Object.keys(parsed);
            // 如果只有 reason 字段且为空
            if (keys.length > 0 && keys.includes('reason')) {
              const reason = parsed['reason'];
              if (reason === null || reason === undefined || reason === '' ||
                  (typeof reason === 'string' && reason.trim() === '')) {
                return <span className="text-gray-400">-</span>;
              }
            }
          }

          // 有内容需要展示，显示 {...} 点击查看详情
          return (
            <Popover
              content={
                <div className="max-w-md max-h-64 overflow-auto text-sm bg-gray-50 p-3 rounded">
                  <JsonValue value={parsed} />
                </div>
              }
              title={t("dataCleansing.detail.fileTable.resultDetail")}
              trigger="click"
            >
              <span className="font-mono text-sm text-blue-600 cursor-pointer hover:text-blue-800 underline">
                {"{...}"}
              </span>
            </Popover>
          );
        } catch {
          // 普通字符串：如果为空则不展示
          if (text.trim() === '') {
            return <span className="text-gray-400">-</span>;
          }
          // 有内容的普通字符串，点击查看详情（支持换行）
          const lines = text.split('\n');
          return (
            <Popover
              content={
                <div className="max-w-md max-h-64 overflow-auto text-sm bg-gray-50 p-3 rounded whitespace-pre-wrap">
                  {lines.map((line, i) => (
                    <span key={i}>
                      {line}
                      {i < lines.length - 1 && <br />}
                    </span>
                  ))}
                </div>
              }
              title={t("dataCleansing.detail.fileTable.resultDetail")}
              trigger="click"
            >
              <span className="font-mono text-sm text-blue-600 cursor-pointer hover:text-blue-800 underline">
                {"{...}"}
              </span>
            </Popover>
          );
        }
      }
    },
    {
      title: t("dataCleansing.detail.fileTable.status"),
      dataIndex: "status",
      key: "status",
      filters: [
        { text: t("dataCleansing.status.completed"), value: "COMPLETED" },
        { text: t("dataCleansing.status.failed"), value: "FAILED" },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === "COMPLETED"
              ? "success"
              : "error"
          }
          text={getTaskStatusMap(t)[status as TaskStatus].label}
        />
      ),
    },
    {
      title: t("dataCleansing.detail.fileTable.actions"),
      key: "action",
      width: 150,
      render: (_text: string, record: any) => (
        <div className="flex">
          {record.status === "COMPLETED" ? (
            <Button
              type="link"
              size="small"
              onClick={() => handleViewFileCompare(record)}
            >
              {t("dataCleansing.actions.compare")}
            </Button>
          ) : (
            <Button
              type="link"
              size="small"
              disabled
            >
              {t("dataCleansing.actions.compare")}
            </Button>
          )}
          <Button
            type="link"
            size="small"
            onClick={() => handleDownload()}
          >
            {t("dataCleansing.actions.download")}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      {selectedFileIds.length > 0 && (
        <div className="mb-4 flex justify-between items-center">
          <span className="text-sm text-gray-600">
            {t("dataCleansing.detail.fileTable.selectedFilesCount", { count: selectedFileIds.length })}
          </span>
          <Button
            onClick={handleDownload}
            size="small"
            type="primary"
            icon={<Download className="w-4 h-4 mr-2" />}
          >
            {t("dataCleansing.actions.download")}
          </Button>
        </div>
      )}
      <Table
        columns={fileColumns}
        dataSource={result}
        pagination={{ pageSize: 10, showSizeChanger: true }}
        size="middle"
        rowKey={(record) => record.srcFileId || record.instanceId}
      />

      {/* 文件对比弹窗 */}
      <Modal
        open={showFileCompareDialog}
        onCancel={() => setShowFileCompareDialog(false)}
        footer={null}
        width={900}
        title={<span>{t("dataCleansing.detail.fileTable.compareDialogTitle", {fileName: selectedFile?.fileName})}</span>}
      >
        <div className="grid grid-cols-2 gap-6 py-6">
          <div>
            <h4 className="font-medium text-gray-900">{t("dataCleansing.detail.fileTable.beforeProcessing")}</h4>
            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-48 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-gray-300 rounded-lg mx-auto mb-2" />
                <div className="text-sm">{t("dataCleansing.detail.fileTable.originalFilePreview")}</div>
                <div className="text-xs text-gray-400">
                  {t("dataCleansing.detail.fileTable.size")}: {formatFileSize(selectedFile?.srcSize)}
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-3 space-y-1">
              <div>
                <span className="font-medium">{t("dataCleansing.detail.fileTable.fileFormat")}:</span> {selectedFile?.srcType}
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{t("dataCleansing.detail.fileTable.afterProcessing")}</h4>
            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-48 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-blue-300 rounded-lg mx-auto mb-2" />
                <div className="text-sm">{t("dataCleansing.detail.fileTable.processedFilePreview")}</div>
                <div className="text-xs text-gray-400">
                  {t("dataCleansing.detail.fileTable.size")}: {formatFileSize(selectedFile?.destSize)}
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-3 space-y-1">
              <div>
                <span className="font-medium">{t("dataCleansing.detail.fileTable.fileFormat")}:</span> {selectedFile?.destType}
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-gray-200 mt-6 pt-4">
          <h4 className="font-medium text-gray-900 mb-3">{t("dataCleansing.detail.fileTable.processingEffect")}</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="font-medium text-green-700">{t("dataCleansing.detail.fileTable.sizeOptimization")}</div>
              <div className="text-green-600">{t("dataCleansing.detail.fileTable.reduced", {percent: (100 * (selectedFile?.srcSize - selectedFile?.destSize) / selectedFile?.srcSize).toFixed(2)})}</div>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
