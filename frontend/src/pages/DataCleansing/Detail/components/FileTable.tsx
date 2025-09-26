import { Button, Modal, Table, Badge, Input } from "antd";
import { Download, FileText } from "lucide-react";
import { useState } from "react";

// 模拟文件列表数据
const fileList = [
  {
    id: 1,
    fileName: "lung_cancer_001.svs",
    originalSize: "15.2MB",
    processedSize: "8.5MB",
    status: "已完成",
    duration: "2分15秒",
    processedAt: "2024-01-20 09:32:40",
  },
  {
    id: 2,
    fileName: "lung_cancer_002.svs",
    originalSize: "18.7MB",
    processedSize: "10.2MB",
    status: "已完成",
    duration: "2分38秒",
    processedAt: "2024-01-20 09:35:18",
  },
  {
    id: 3,
    fileName: "lung_cancer_003.svs",
    originalSize: "12.3MB",
    processedSize: "6.8MB",
    status: "已完成",
    duration: "1分52秒",
    processedAt: "2024-01-20 09:37:10",
  },
  {
    id: 4,
    fileName: "lung_cancer_004.svs",
    originalSize: "20.1MB",
    processedSize: "-",
    status: "失败",
    duration: "0分45秒",
    processedAt: "2024-01-20 09:38:55",
  },
  {
    id: 5,
    fileName: "lung_cancer_005.svs",
    originalSize: "16.8MB",
    processedSize: "9.3MB",
    status: "已完成",
    duration: "2分22秒",
    processedAt: "2024-01-20 09:41:17",
  },
];

export default function FileTable() {
  const [showFileCompareDialog, setShowFileCompareDialog] = useState(false);
  const [showFileLogDialog, setShowFileLogDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<number[]>([]);
  const handleSelectAllFiles = (checked: boolean) => {
    if (checked) {
      setSelectedFileIds(fileList.map((file) => file.id));
    } else {
      setSelectedFileIds([]);
    }
  };

  const handleSelectFile = (fileId: number, checked: boolean) => {
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

  const handleBatchDeleteFiles = () => {
    // 实际删除逻辑
    setSelectedFileIds([]);
  };
  const handleViewFileLog = (file: any) => {
    setSelectedFile(file);
    setShowFileLogDialog(true);
  };

  // 模拟单个文件的处理日志
  const getFileProcessLog = (fileName: string) => [
    {
      time: "09:30:18",
      step: "开始处理",
      operator: "格式转换",
      status: "INFO",
      message: `开始处理文件: ${fileName}`,
    },
    {
      time: "09:30:19",
      step: "文件验证",
      operator: "格式转换",
      status: "INFO",
      message: "验证文件格式和完整性",
    },
    {
      time: "09:30:20",
      step: "格式解析",
      operator: "格式转换",
      status: "INFO",
      message: "解析SVS格式文件",
    },
    {
      time: "09:30:25",
      step: "格式转换",
      operator: "格式转换",
      status: "SUCCESS",
      message: "成功转换为JPEG格式",
    },
    {
      time: "09:30:26",
      step: "噪声检测",
      operator: "噪声去除",
      status: "INFO",
      message: "检测图像噪声水平",
    },
    {
      time: "09:30:28",
      step: "噪声去除",
      operator: "噪声去除",
      status: "INFO",
      message: "应用高斯滤波去除噪声",
    },
    {
      time: "09:30:31",
      step: "噪声去除完成",
      operator: "噪声去除",
      status: "SUCCESS",
      message: "噪声去除处理完成",
    },
    {
      time: "09:30:32",
      step: "尺寸检测",
      operator: "尺寸标准化",
      status: "INFO",
      message: "检测当前图像尺寸: 2048x1536",
    },
    {
      time: "09:30:33",
      step: "尺寸调整",
      operator: "尺寸标准化",
      status: "INFO",
      message: "调整图像尺寸至512x512",
    },
    {
      time: "09:30:35",
      step: "尺寸标准化完成",
      operator: "尺寸标准化",
      status: "SUCCESS",
      message: "图像尺寸标准化完成",
    },
    {
      time: "09:30:36",
      step: "质量检查",
      operator: "质量检查",
      status: "INFO",
      message: "检查图像质量指标",
    },
    {
      time: "09:30:38",
      step: "分辨率检查",
      operator: "质量检查",
      status: "SUCCESS",
      message: "分辨率符合要求",
    },
    {
      time: "09:30:39",
      step: "清晰度检查",
      operator: "质量检查",
      status: "SUCCESS",
      message: "图像清晰度良好",
    },
    {
      time: "09:30:40",
      step: "处理完成",
      operator: "质量检查",
      status: "SUCCESS",
      message: `文件 ${fileName} 处理完成`,
    },
  ];

  const fileColumns = [
    {
      title: (
        <input
          type="checkbox"
          checked={
            selectedFileIds.length === fileList.length && fileList.length > 0
          }
          onChange={(e) => handleSelectAllFiles(e.target.checked)}
          className="w-4 h-4"
        />
      ),
      dataIndex: "select",
      key: "select",
      width: 50,
      render: (text: string, record: any) => (
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
      dataIndex: "fileName",
      key: "fileName",
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
        record.fileName.toLowerCase().includes(value.toLowerCase()),
      render: (text: string) => (
        <span className="font-mono text-sm">{text}</span>
      ),
    },
    {
      title: "清洗前大小",
      dataIndex: "originalSize",
      key: "originalSize",
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
    },
    {
      title: "清洗后大小",
      dataIndex: "processedSize",
      key: "processedSize",
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
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      filters: [
        { text: "已完成", value: "已完成" },
        { text: "失败", value: "失败" },
        { text: "处理中", value: "处理中" },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === "已完成"
              ? "success"
              : status === "失败"
              ? "error"
              : "processing"
          }
          text={status}
        />
      ),
    },
    {
      title: "执行耗时",
      dataIndex: "duration",
      key: "duration",
      sorter: (a: any, b: any) => {
        const getTimeInSeconds = (duration: string) => {
          const parts = duration.split(/[分秒]/);
          const minutes = Number.parseInt(parts[0]) || 0;
          const seconds = Number.parseInt(parts[1]) || 0;
          return minutes * 60 + seconds;
        };
        return getTimeInSeconds(a.duration) - getTimeInSeconds(b.duration);
      },
    },
    {
      title: "操作",
      key: "action",
      render: (text: string, record: any) => (
        <div className="flex">
          <Button
            type="link"
            size="small"
            onClick={() => handleViewFileLog(record)}
          >
            日志
          </Button>
          {record.status === "已完成" && (
            <Button
              type="link"
              size="small"
              onClick={() => handleViewFileCompare(record)}
            >
              对比
            </Button>
          )}
          <Button type="link" size="small">
            下载
          </Button>
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
        dataSource={fileList}
        pagination={{ pageSize: 10, showSizeChanger: true }}
        size="middle"
        rowKey="id"
      />

      {/* 文件日志弹窗 */}
      <Modal
        open={showFileLogDialog}
        onCancel={() => setShowFileLogDialog(false)}
        footer={null}
        width={700}
        title={
          <span>
            <FileText className="w-4 h-4 mr-2 inline" />
            文件处理日志 - {selectedFile?.fileName}
          </span>
        }
      >
        <div className="py-4">
          <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
            <div className="font-mono text-sm">
              {selectedFile &&
                getFileProcessLog(selectedFile.fileName).map((log, index) => (
                  <div key={index} className="flex gap-3">
                    <span className="text-gray-500 min-w-20">{log.time}</span>
                    <span className="text-blue-400 min-w-24">
                      [{log.operator}]
                    </span>
                    <span
                      className={`min-w-20 ${
                        log.status === "ERROR"
                          ? "text-red-400"
                          : log.status === "SUCCESS"
                          ? "text-green-400"
                          : "text-yellow-400"
                      }`}
                    >
                      {log.step}
                    </span>
                    <span className="text-gray-100">{log.message}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </Modal>
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
            <h4 className="font-medium text-gray-900">清洗前</h4>
            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-48 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-gray-300 rounded-lg mx-auto mb-2" />
                <div className="text-sm">原始文件预览</div>
                <div className="text-xs text-gray-400">
                  大小: {selectedFile?.originalSize}
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-3 space-y-1">
              <div>
                <span className="font-medium">文件格式:</span> SVS
              </div>
              <div>
                <span className="font-medium">分辨率:</span> 2048x1536
              </div>
              <div>
                <span className="font-medium">色彩空间:</span> RGB
              </div>
              <div>
                <span className="font-medium">压缩方式:</span> 无压缩
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">清洗后</h4>
            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-48 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-blue-300 rounded-lg mx-auto mb-2" />
                <div className="text-sm">处理后文件预览</div>
                <div className="text-xs text-gray-400">
                  大小: {selectedFile?.processedSize}
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-3 space-y-1">
              <div>
                <span className="font-medium">文件格式:</span> JPEG
              </div>
              <div>
                <span className="font-medium">分辨率:</span> 512x512
              </div>
              <div>
                <span className="font-medium">色彩空间:</span> RGB
              </div>
              <div>
                <span className="font-medium">压缩方式:</span> JPEG压缩
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-gray-200 mt-6 pt-4">
          <h4 className="font-medium text-gray-900 mb-3">处理效果对比</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="font-medium text-green-700">文件大小优化</div>
              <div className="text-green-600">减少了 44.1%</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="font-medium text-blue-700">处理时间</div>
              <div className="text-blue-600">{selectedFile?.duration}</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="font-medium text-purple-700">质量评分</div>
              <div className="text-purple-600">优秀 (9.2/10)</div>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
