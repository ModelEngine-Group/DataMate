import { useState } from "react";
import {
  Card,
  Button,
  Input,
  Badge,
  Progress,
  Descriptions,
  Table,
  Modal,
  Breadcrumb,
} from "antd";
import {
  Play,
  Pause,
  Eye,
  Clock,
  CheckCircle,
  AlertCircle,
  Database,
  Trash2,
  Download,
  FileText,
  Activity,
} from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import { MOCK_TASKS } from "@/mock/cleansing";
import { Link } from "react-router";

// 任务详情页面组件
export default function CleansingTaskDetail() {
  const task = MOCK_TASKS[0];
  const [activeTab, setActiveTab] = useState("basic");
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

  const handleBatchDownload = () => {
    // 实际下载逻辑
  };

  const handleBatchDeleteFiles = () => {
    // 实际删除逻辑
    setSelectedFileIds([]);
  };

  // 模拟运行报告数据
  const runReport = {
    startTime: "2024-01-20 09:30:15",
    endTime: "2024-01-20 11:45:32",
    duration: "2小时15分钟17秒",
    status: "已完成",
    totalFiles: 1250,
    processedFiles: 1250,
    successFiles: 1198,
    failedFiles: 52,
    operators: [
      {
        name: "格式转换",
        startTime: "09:30:15",
        endTime: "09:58:42",
        duration: "28分27秒",
        status: "成功",
        processedFiles: 1250,
        successRate: 100,
      },
      {
        name: "噪声去除",
        startTime: "09:58:42",
        endTime: "10:35:18",
        duration: "36分36秒",
        status: "成功",
        processedFiles: 1250,
        successRate: 98.2,
      },
      {
        name: "尺寸标准化",
        startTime: "10:35:18",
        endTime: "11:12:05",
        duration: "36分47秒",
        status: "成功",
        processedFiles: 1228,
        successRate: 99.5,
      },
      {
        name: "质量检查",
        startTime: "11:12:05",
        endTime: "11:45:32",
        duration: "33分27秒",
        status: "成功",
        processedFiles: 1222,
        successRate: 97.8,
      },
    ],
  };

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

  // 模拟运行日志
  const runLogs = [
    {
      time: "09:30:15",
      level: "INFO",
      message: "开始执行数据清洗任务: 肺癌WSI图像清洗任务",
    },
    {
      time: "09:30:16",
      level: "INFO",
      message: "加载源数据集: 肺癌WSI病理图像数据集 (1250 文件)",
    },
    { time: "09:30:17", level: "INFO", message: "初始化算子: 格式转换" },
    {
      time: "09:30:18",
      level: "INFO",
      message: "开始处理文件: lung_cancer_001.svs",
    },
    {
      time: "09:30:25",
      level: "SUCCESS",
      message: "文件处理成功: lung_cancer_001.svs -> lung_cancer_001.jpg",
    },
    {
      time: "09:30:26",
      level: "INFO",
      message: "开始处理文件: lung_cancer_002.svs",
    },
    {
      time: "09:30:33",
      level: "SUCCESS",
      message: "文件处理成功: lung_cancer_002.svs -> lung_cancer_002.jpg",
    },
    {
      time: "09:58:42",
      level: "INFO",
      message: "格式转换完成，成功处理 1250/1250 文件",
    },
    { time: "09:58:43", level: "INFO", message: "初始化算子: 噪声去除" },
    {
      time: "09:58:44",
      level: "INFO",
      message: "开始处理文件: lung_cancer_001.jpg",
    },
    {
      time: "09:58:51",
      level: "SUCCESS",
      message: "噪声去除成功: lung_cancer_001.jpg",
    },
    {
      time: "10:15:23",
      level: "WARNING",
      message: "文件质量较低，跳过处理: lung_cancer_156.jpg",
    },
    {
      time: "10:35:18",
      level: "INFO",
      message: "噪声去除完成，成功处理 1228/1250 文件",
    },
    { time: "10:35:19", level: "INFO", message: "初始化算子: 尺寸标准化" },
    {
      time: "11:12:05",
      level: "INFO",
      message: "尺寸标准化完成，成功处理 1222/1228 文件",
    },
    { time: "11:12:06", level: "INFO", message: "初始化算子: 质量检查" },
    {
      time: "11:25:33",
      level: "ERROR",
      message: "质量检查失败: lung_cancer_089.jpg - 分辨率过低",
    },
    {
      time: "11:45:32",
      level: "INFO",
      message: "质量检查完成，成功处理 1198/1222 文件",
    },
    {
      time: "11:45:33",
      level: "SUCCESS",
      message: "数据清洗任务完成！总成功率: 95.8%",
    },
  ];

  const handleViewFileCompare = (file: any) => {
    setSelectedFile(file);
    setShowFileCompareDialog(true);
  };

  const handleViewFileLog = (file: any) => {
    setSelectedFile(file);
    setShowFileLogDialog(true);
  };

  const operatorColumns = [
    {
      title: "序号",
      dataIndex: "index",
      key: "index",
      width: 80,
      render: (text: any, record: any, index: number) => index + 1,
    },
    {
      title: "算子名称",
      dataIndex: "name",
      key: "name",
      filterDropdown: ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
      }: any) => (
        <div className="p-4 w-64">
          <Input
            placeholder="搜索算子名称"
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
        record.name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: "开始时间",
      dataIndex: "startTime",
      key: "startTime",
      sorter: (a: any, b: any) =>
        new Date(a.startTime).getTime() - new Date(b.startTime).getTime(),
    },
    {
      title: "结束时间",
      dataIndex: "endTime",
      key: "endTime",
      sorter: (a: any, b: any) =>
        new Date(a.endTime).getTime() - new Date(b.endTime).getTime(),
    },
    {
      title: "执行时长",
      dataIndex: "duration",
      key: "duration",
    },
    {
      title: "处理文件数",
      dataIndex: "processedFiles",
      key: "processedFiles",
      sorter: (a: any, b: any) => a.processedFiles - b.processedFiles,
    },
    {
      title: "成功率",
      dataIndex: "successRate",
      key: "successRate",
      sorter: (a: any, b: any) => a.successRate - b.successRate,
      render: (rate: number) => `${rate}%`,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      filters: [
        { text: "成功", value: "成功" },
        { text: "失败", value: "失败" },
        { text: "运行中", value: "运行中" },
      ],
      onFilter: (value: string, record: any) => record.status === value,
      render: (status: string) => (
        <Badge
          status={
            status === "成功"
              ? "success"
              : status === "失败"
              ? "error"
              : "processing"
          }
          text={status}
        />
      ),
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

  const renderBasicInfo = () => (
    <>
      {/* 执行摘要 */}
      <Card className="mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <Clock className="w-8 h-8 text-blue-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-blue-500">
              {runReport.duration}
            </div>
            <div className="text-sm text-gray-600">总耗时</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
            <CheckCircle className="w-8 h-8 text-green-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-green-500">
              {runReport.successFiles}
            </div>
            <div className="text-sm text-gray-600">成功文件</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg">
            <AlertCircle className="w-8 h-8 text-red-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-red-500">
              {runReport.failedFiles}
            </div>
            <div className="text-sm text-gray-600">失败文件</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <Activity className="w-8 h-8 text-purple-500 mb-2 mx-auto" />
            <div className="text-xl font-bold text-purple-500">95.8%</div>
            <div className="text-sm text-gray-600">成功率</div>
          </div>
        </div>
      </Card>
      {/* 任务信息和处理进度合并卡片 */}
      <Card>
        {/* 任务基本信息 */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
          <Descriptions
            column={2}
            bordered={false}
            size="middle"
            labelStyle={{ fontWeight: 500, color: "#555" }}
            contentStyle={{ fontSize: 14 }}
          >
            <Descriptions.Item label="任务ID">
              <span className="font-mono">#{task.id}</span>
            </Descriptions.Item>
            <Descriptions.Item label="任务名称">{task.name}</Descriptions.Item>
            <Descriptions.Item label="源数据集">
              <Button type="link" size="small" className="p-0 h-auto">
                {task.dataset}
              </Button>
            </Descriptions.Item>
            <Descriptions.Item label="处理后数据集">
              <Button type="link" size="small" className="p-0 h-auto">
                {task.newDatasetName || task.name + "_processed"}
              </Button>
            </Descriptions.Item>
            <Descriptions.Item label="使用模板">
              {task.template}
            </Descriptions.Item>
            <Descriptions.Item label="批处理大小">
              {task.batchSize || "100"} 文件/批
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {task.startTime}
            </Descriptions.Item>
            <Descriptions.Item label="预计用时">
              {task.estimatedTime}
            </Descriptions.Item>
            <Descriptions.Item label="任务描述" span={2}>
              <span className="text-gray-600">
                {task.description || "暂无描述"}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="处理算子" span={2}>
              <div className="flex flex-wrap gap-1">
                {task.operators.map((op: string, index: number) => (
                  <Badge
                    key={index}
                    className="bg-gray-50 border border-gray-200 mr-1"
                  >
                    {op}
                  </Badge>
                ))}
              </div>
            </Descriptions.Item>
          </Descriptions>
        </div>
        {/* 处理进度 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">处理进度</h3>
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span>整体进度</span>
              <span>{task.progress}%</span>
            </div>
            <Progress percent={task.progress} showInfo />
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full inline-block" />
              <span>已完成: {task.processedFiles}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full inline-block" />
              <span>处理中: 0</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-gray-300 rounded-full inline-block" />
              <span>待处理: {task.totalFiles - task.processedFiles}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-red-500 rounded-full inline-block" />
              <span>失败: 52</span>
            </div>
          </div>
        </div>
      </Card>
    </>
  );

  const renderReport = () => (
    <Table
      columns={operatorColumns}
      dataSource={runReport.operators}
      pagination={false}
      size="middle"
    />
  );

  const renderFileList = () => (
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
    </>
  );

  const renderLogs = () => (
    <div className="text-gray-300 p-4 border border-gray-700 bg-gray-800 rounded-lg">
      <div className="font-mono text-sm">
        {runLogs.map((log, index) => (
          <div key={index} className="flex gap-3">
            <span className="text-gray-500 min-w-20">{log.time}</span>
            <span
              className={`min-w-20 ${
                log.level === "ERROR"
                  ? "text-red-500"
                  : log.level === "WARNING"
                  ? "text-yellow-500"
                  : log.level === "SUCCESS"
                  ? "text-green-500"
                  : "text-blue-500"
              }`}
            >
              [{log.level}]
            </span>
            <span className="text-gray-100">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen">
      <Breadcrumb
        items={[
          {
            title: <Link to="/data/cleansing">数据清洗</Link>,
          },
          {
            title: "清洗任务详情",
          },
        ]}
      />
      <div className="mb-4 mt-4">
        <DetailHeader
          data={{
            id: task.id,
            icon: <Database className="w-8 h-8" />,
            status: {
              label: task.status,
              color: task.status === "已完成" ? "green" : "blue",
            },
            name: task.name,
            description: task.description || "",
            createdAt: task.startTime,
            lastUpdated: task.startTime,
          }}
          statistics={[
            {
              icon: <Clock className="w-4 h-4 text-blue-500" />,
              label: "总耗时",
              value: runReport.duration,
            },
            {
              icon: <CheckCircle className="w-4 h-4 text-green-500" />,
              label: "成功文件",
              value: runReport.successFiles,
            },
            {
              icon: <AlertCircle className="w-4 h-4 text-red-500" />,
              label: "失败文件",
              value: runReport.failedFiles,
            },
            {
              icon: <Activity className="w-4 h-4 text-purple-500" />,
              label: "成功率",
              value: "95.8%",
            },
          ]}
          operations={[
            {
              key: "download",
              label: "下载结果",
              icon: <Download className="w-4 h-4" />,
              onClick: () => {
                /* 下载逻辑 */
              },
            },
            ...(task.status === "运行中"
              ? [
                  {
                    key: "pause",
                    label: "暂停任务",
                    icon: <Pause className="w-4 h-4" />,
                    onClick: () => {
                      /* 暂停逻辑 */
                    },
                  },
                ]
              : []),
            ...(task.status === "队列中"
              ? [
                  {
                    key: "play",
                    label: "执行任务",
                    icon: <Play className="w-4 h-4" />,
                    onClick: () => {
                      /* 执行逻辑 */
                    },
                  },
                ]
              : []),
            {
              key: "delete",
              label: "删除任务",
              icon: <Trash2 className="w-4 h-4" />,
              danger: true,
              onClick: () => {
                /* 删除逻辑 */
              },
            },
          ]}
        />
      </div>
      <Card
        tabList={[
          { key: "basic", tab: "基本信息" },
          { key: "operators", tab: "处理算子" },
          { key: "files", tab: "处理文件" },
          { key: "logs", tab: "运行日志" },
        ]}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        {activeTab === "basic" && renderBasicInfo()}
        {activeTab === "operators" && renderReport()}
        {activeTab === "files" && renderFileList()}
        {activeTab === "logs" && renderLogs()}
      </Card>

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
    </div>
  );
}
