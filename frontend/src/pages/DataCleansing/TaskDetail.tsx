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
        <div style={{ padding: 16, width: 256 }}>
          <Input
            placeholder="搜索算子名称"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8 }}
          />
          <div style={{ display: "flex", gap: 8 }}>
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
          style={{ width: 16, height: 16 }}
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
          style={{ width: 16, height: 16 }}
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
        <div style={{ padding: 16, width: 256 }}>
          <Input
            placeholder="搜索文件名"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8 }}
          />
          <div style={{ display: "flex", gap: 8 }}>
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
        <span style={{ fontFamily: "monospace", fontSize: 13 }}>{text}</span>
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
        <div style={{ display: "flex", gap: 8 }}>
          {record.status === "已完成" && (
            <Button
              type="link"
              size="small"
              onClick={() => handleViewFileCompare(record)}
            >
              <Eye className="w-4 h-4 mr-1" />
              对比
            </Button>
          )}
          <Button type="link" size="small">
            <Download className="w-4 h-4 mr-1" />
            下载
          </Button>
        </div>
      ),
    },
  ];

  const renderBasicInfo = () => (
    <>
      {/* 执行摘要 */}
      <Card style={{ marginBottom: 24 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: 16,
          }}
        >
          <div
            style={{
              textAlign: "center",
              padding: 16,
              background: "linear-gradient(135deg, #e0edff 0%, #f0f7ff 100%)",
              borderRadius: 8,
            }}
          >
            <Clock
              className="w-8 h-8"
              style={{ color: "#1677ff", marginBottom: 8 }}
            />
            <div style={{ fontSize: 20, fontWeight: 700, color: "#1677ff" }}>
              {runReport.duration}
            </div>
            <div style={{ fontSize: 13, color: "#666" }}>总耗时</div>
          </div>
          <div
            style={{
              textAlign: "center",
              padding: 16,
              background: "linear-gradient(135deg, #e6fffb 0%, #f6ffed 100%)",
              borderRadius: 8,
            }}
          >
            <CheckCircle
              className="w-8 h-8"
              style={{ color: "#52c41a", marginBottom: 8 }}
            />
            <div style={{ fontSize: 20, fontWeight: 700, color: "#52c41a" }}>
              {runReport.successFiles}
            </div>
            <div style={{ fontSize: 13, color: "#666" }}>成功文件</div>
          </div>
          <div
            style={{
              textAlign: "center",
              padding: 16,
              background: "linear-gradient(135deg, #fff1f0 0%, #fff7f7 100%)",
              borderRadius: 8,
            }}
          >
            <AlertCircle
              className="w-8 h-8"
              style={{ color: "#f5222d", marginBottom: 8 }}
            />
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f5222d" }}>
              {runReport.failedFiles}
            </div>
            <div style={{ fontSize: 13, color: "#666" }}>失败文件</div>
          </div>
          <div
            style={{
              textAlign: "center",
              padding: 16,
              background: "linear-gradient(135deg, #f9f0ff 0%, #f0f5ff 100%)",
              borderRadius: 8,
            }}
          >
            <Activity
              className="w-8 h-8"
              style={{ color: "#722ed1", marginBottom: 8 }}
            />
            <div style={{ fontSize: 20, fontWeight: 700, color: "#722ed1" }}>
              95.8%
            </div>
            <div style={{ fontSize: 13, color: "#666" }}>成功率</div>
          </div>
        </div>
      </Card>
      {/* 任务信息和处理进度合并卡片 */}
      <Card>
        {/* 任务基本信息 */}
        <div style={{ marginBottom: 32 }}>
          <h3
            style={{
              fontSize: 18,
              fontWeight: 600,
              color: "#222",
              marginBottom: 16,
            }}
          >
            基本信息
          </h3>
          <Descriptions
            column={2}
            bordered={false}
            size="middle"
            labelStyle={{ fontWeight: 500, color: "#555" }}
            contentStyle={{ fontSize: 14 }}
          >
            <Descriptions.Item label="任务ID">
              <span style={{ fontFamily: "monospace" }}>#{task.id}</span>
            </Descriptions.Item>
            <Descriptions.Item label="任务名称">{task.name}</Descriptions.Item>
            <Descriptions.Item label="源数据集">
              <Button
                type="link"
                size="small"
                style={{ padding: 0, height: "auto" }}
              >
                {task.dataset}
              </Button>
            </Descriptions.Item>
            <Descriptions.Item label="处理后数据集">
              <Button
                type="link"
                size="small"
                style={{ padding: 0, height: "auto" }}
              >
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
              <span style={{ color: "#666" }}>
                {task.description || "暂无描述"}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="处理算子" span={2}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {task.operators.map((op: string, index: number) => (
                  <Badge
                    key={index}
                    style={{
                      background: "#f5f5f5",
                      border: "1px solid #d9d9d9",
                      marginRight: 4,
                    }}
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
          <h3
            style={{
              fontSize: 18,
              fontWeight: 600,
              color: "#222",
              marginBottom: 16,
            }}
          >
            处理进度
          </h3>
          <div style={{ marginBottom: 16 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 14,
                marginBottom: 8,
              }}
            >
              <span>整体进度</span>
              <span>{task.progress}%</span>
            </div>
            <Progress percent={task.progress} showInfo />
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: 16,
              fontSize: 14,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  background: "#52c41a",
                  borderRadius: 6,
                  display: "inline-block",
                }}
              />
              <span>已完成: {task.processedFiles}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  background: "#1677ff",
                  borderRadius: 6,
                  display: "inline-block",
                }}
              />
              <span>处理中: 0</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  background: "#d9d9d9",
                  borderRadius: 6,
                  display: "inline-block",
                }}
              />
              <span>待处理: {task.totalFiles - task.processedFiles}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  background: "#f5222d",
                  borderRadius: 6,
                  display: "inline-block",
                }}
              />
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
      <div
        style={{
          marginBottom: 16,
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        {selectedFileIds.length > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 14, color: "#666" }}>
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
        )}
      </div>
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
      <div style={{ fontFamily: "monospace", fontSize: 13 }}>
        {runLogs.map((log, index) => (
          <div key={index} style={{ display: "flex", gap: 12 }}>
            <span style={{ color: "#888", minWidth: 80 }}>{log.time}</span>
            <span
              style={{
                color:
                  log.level === "ERROR"
                    ? "#f5222d"
                    : log.level === "WARNING"
                    ? "#faad14"
                    : log.level === "SUCCESS"
                    ? "#52c41a"
                    : "#1677ff",
                minWidth: 80,
              }}
            >
              [{log.level}]
            </span>
            <span style={{ color: "#eee" }}>{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div style={{ minHeight: "100vh" }}>
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
        title={
          <span>
            <Eye className="w-4 h-4" style={{ marginRight: 8 }} />
            文件对比 - {selectedFile?.fileName}
          </span>
        }
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 24,
            padding: "24px 0",
          }}
        >
          <div>
            <h4 style={{ fontWeight: 500, color: "#222" }}>清洗前</h4>
            <div
              style={{
                border: "1px solid #eee",
                borderRadius: 8,
                padding: 24,
                background: "#fafafa",
                minHeight: 200,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div style={{ textAlign: "center", color: "#888" }}>
                <div
                  style={{
                    width: 64,
                    height: 64,
                    background: "#d9d9d9",
                    borderRadius: 8,
                    margin: "0 auto 8px",
                  }}
                />
                <div style={{ fontSize: 14 }}>原始文件预览</div>
                <div style={{ fontSize: 12, color: "#aaa" }}>
                  大小: {selectedFile?.originalSize}
                </div>
              </div>
            </div>
            <div style={{ fontSize: 13, color: "#666", marginTop: 12 }}>
              <div>
                <span style={{ fontWeight: 500 }}>文件格式:</span> SVS
              </div>
              <div>
                <span style={{ fontWeight: 500 }}>分辨率:</span> 2048x1536
              </div>
              <div>
                <span style={{ fontWeight: 500 }}>色彩空间:</span> RGB
              </div>
              <div>
                <span style={{ fontWeight: 500 }}>压缩方式:</span> 无压缩
              </div>
            </div>
          </div>
          <div>
            <h4 style={{ fontWeight: 500, color: "#222" }}>清洗后</h4>
            <div
              style={{
                border: "1px solid #eee",
                borderRadius: 8,
                padding: 24,
                background: "#fafafa",
                minHeight: 200,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div style={{ textAlign: "center", color: "#888" }}>
                <div
                  style={{
                    width: 64,
                    height: 64,
                    background: "#91d5ff",
                    borderRadius: 8,
                    margin: "0 auto 8px",
                  }}
                />
                <div style={{ fontSize: 14 }}>处理后文件预览</div>
                <div style={{ fontSize: 12, color: "#aaa" }}>
                  大小: {selectedFile?.processedSize}
                </div>
              </div>
            </div>
            <div style={{ fontSize: 13, color: "#666", marginTop: 12 }}>
              <div>
                <span style={{ fontWeight: 500 }}>文件格式:</span> JPEG
              </div>
              <div>
                <span style={{ fontWeight: 500 }}>分辨率:</span> 512x512
              </div>
              <div>
                <span style={{ fontWeight: 500 }}>色彩空间:</span> RGB
              </div>
              <div>
                <span style={{ fontWeight: 500 }}>压缩方式:</span> JPEG压缩
              </div>
            </div>
          </div>
        </div>
        <div
          style={{ borderTop: "1px solid #eee", marginTop: 24, paddingTop: 16 }}
        >
          <h4 style={{ fontWeight: 500, color: "#222", marginBottom: 12 }}>
            处理效果对比
          </h4>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 16,
              fontSize: 14,
            }}
          >
            <div
              style={{ background: "#f6ffed", padding: 16, borderRadius: 8 }}
            >
              <div style={{ fontWeight: 500, color: "#389e0d" }}>
                文件大小优化
              </div>
              <div style={{ color: "#52c41a" }}>减少了 44.1%</div>
            </div>
            <div
              style={{ background: "#e6f7ff", padding: 16, borderRadius: 8 }}
            >
              <div style={{ fontWeight: 500, color: "#1677ff" }}>处理时间</div>
              <div style={{ color: "#1677ff" }}>{selectedFile?.duration}</div>
            </div>
            <div
              style={{ background: "#f9f0ff", padding: 16, borderRadius: 8 }}
            >
              <div style={{ fontWeight: 500, color: "#722ed1" }}>质量评分</div>
              <div style={{ color: "#722ed1" }}>优秀 (9.2/10)</div>
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
            <FileText className="w-4 h-4" style={{ marginRight: 8 }} />
            文件处理日志 - {selectedFile?.fileName}
          </span>
        }
      >
        <div style={{ padding: "16px 0" }}>
          <div
            style={{
              background: "#111",
              borderRadius: 8,
              padding: 16,
              maxHeight: 400,
              overflowY: "auto",
            }}
          >
            <div style={{ fontFamily: "monospace", fontSize: 13 }}>
              {selectedFile &&
                getFileProcessLog(selectedFile.fileName).map((log, index) => (
                  <div key={index} style={{ display: "flex", gap: 12 }}>
                    <span style={{ color: "#888", minWidth: 80 }}>
                      {log.time}
                    </span>
                    <span style={{ color: "#1677ff", minWidth: 100 }}>
                      [{log.operator}]
                    </span>
                    <span
                      style={{
                        color:
                          log.status === "ERROR"
                            ? "#f5222d"
                            : log.status === "SUCCESS"
                            ? "#52c41a"
                            : "#faad14",
                        minWidth: 80,
                      }}
                    >
                      {log.step}
                    </span>
                    <span style={{ color: "#eee" }}>{log.message}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
