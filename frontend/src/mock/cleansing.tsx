import type { OperatorI } from "@/types/cleansing";
import {
  DatabaseOutlined,
  FilterOutlined,
  BarChartOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  PictureOutlined,
  CalculatorOutlined,
  ClusterOutlined,
  AimOutlined,
  SwapOutlined,
} from "@ant-design/icons";

export const MOCK_TASKS = [
  {
    id: 1,
    name: "肺癌WSI图像清洗",
    description: "肺癌WSI病理图像数据集的标准化清洗任务",
    dataset: "肺癌WSI病理图像数据集",
    newDatasetName: "肺癌WSI图像_清洗后",
    template: "医学影像标准清洗",
    batchSize: 100,
    status: "运行中",
    progress: 60,
    startTime: "2024-01-20 09:30:15",
    estimatedTime: "2小时",
    totalFiles: 1250,
    processedFiles: 750,
    operators: ["格式转换", "噪声去除", "尺寸标准化", "质量检查"],
  },
  {
    id: 2,
    name: "病理WSI图像处理",
    description: "WSI病理切片图像的专业清洗流程",
    dataset: "WSI切片数据集",
    newDatasetName: "WSI切片_清洗后",
    template: "病理WSI图像处理",
    batchSize: 100,
    status: "已完成",
    progress: 100,
    startTime: "2024-01-18 14:10:00",
    estimatedTime: "1小时30分",
    totalFiles: 800,
    processedFiles: 800,
    operators: ["格式转换", "色彩校正", "分辨率调整", "组织区域提取"],
  },
  {
    id: 3,
    name: "医学文本清洗",
    description: "医学文本数据的标准化清洗流程",
    dataset: "医学文本数据集",
    newDatasetName: "医学文本_清洗后",
    template: "医学文本清洗",
    batchSize: 200,
    status: "队列中",
    progress: 0,
    startTime: "待开始",
    estimatedTime: "预计2小时",
    totalFiles: 1000,
    processedFiles: 0,
    operators: ["编码转换", "格式统一", "敏感信息脱敏", "质量过滤"],
  },
];

export const MOCK_TEMPLATES = [
  {
    id: "medical-image",
    name: "医学影像标准清洗",
    description: "专用于医学影像的标准化清洗流程，包含格式转换、质量检查等步骤",
    operators: [
      "DICOM解析",
      "格式标准化",
      "窗宽窗位调整",
      "噪声去除",
      "质量检查",
    ],
    category: "医学影像",
    usage: 156,
    color: "blue",
  },
  {
    id: "pathology-wsi",
    name: "病理WSI图像处理",
    description: "WSI病理切片图像的专业清洗流程，优化病理诊断数据质量",
    operators: ["格式转换", "色彩校正", "分辨率调整", "组织区域提取"],
    category: "病理学",
    usage: 89,
    color: "green",
  },
  {
    id: "text-cleaning",
    name: "医学文本清洗",
    description: "医学文本数据的标准化清洗流程，确保文本数据的一致性和质量",
    operators: ["编码转换", "格式统一", "敏感信息脱敏", "质量过滤"],
    category: "文本处理",
    usage: 234,
    color: "purple",
  },
  {
    id: "general-image",
    name: "通用图像清洗",
    description: "适用于各类图像数据的通用清洗流程，提供基础的图像处理功能",
    operators: ["质量检查", "重复检测", "异常过滤", "格式转换"],
    category: "通用",
    usage: 445,
    color: "orange",
  },
  {
    id: "audio-processing",
    name: "音频数据清洗",
    description: "专门针对医学音频数据的清洗和预处理流程",
    operators: ["噪声去除", "格式转换", "音量标准化", "质量检测"],
    category: "音频处理",
    usage: 67,
    color: "pink",
  },
  {
    id: "multimodal-clean",
    name: "多模态数据清洗",
    description: "处理包含多种数据类型的综合清洗流程",
    operators: ["数据分类", "格式统一", "质量检查", "关联验证"],
    category: "多模态",
    usage: 123,
    color: "geekblue",
  },
];

// 模板类型选项
export const templateTypes = [
  {
    value: "text",
    label: "文本",
    icon: "📝",
    description: "处理文本数据的清洗模板",
  },
  {
    value: "image",
    label: "图片",
    icon: "🖼️",
    description: "处理图像数据的清洗模板",
  },
  {
    value: "video",
    label: "视频",
    icon: "🎥",
    description: "处理视频数据的清洗模板",
  },
  {
    value: "audio",
    label: "音频",
    icon: "🎵",
    description: "处理音频数据的清洗模板",
  },
  {
    value: "image-to-text",
    label: "图片转文本",
    icon: "🔄",
    description: "图像识别转文本的处理模板",
  },
];

// 算子分类
export const OPERATOR_CATEGORIES = {
  data: { name: "数据清洗", icon: <DatabaseOutlined />, color: "#1677ff" },
  ml: { name: "机器学习", icon: <ThunderboltOutlined />, color: "#722ed1" },
  vision: { name: "计算机视觉", icon: <PictureOutlined />, color: "#52c41a" },
  nlp: { name: "自然语言处理", icon: <FileTextOutlined />, color: "#faad14" },
  analysis: { name: "数据分析", icon: <BarChartOutlined />, color: "#f5222d" },
  transform: { name: "数据转换", icon: <SwapOutlined />, color: "#13c2c2" },
  io: { name: "输入输出", icon: <FileTextOutlined />, color: "#595959" },
  math: { name: "数学计算", icon: <CalculatorOutlined />, color: "#fadb14" },
};

// 模拟算子模板
const generateOperatorTemplates = (): OperatorI[] => {
  const templates: OperatorI[] = [
    {
      id: "data_reader_mysql",
      name: "MySQL读取",
      type: "data_reader",
      category: "data",
      icon: <DatabaseOutlined />,
      description: "从MySQL数据库读取数据",
      tags: ["数据库", "读取", "MySQL"],
      isPopular: true,
      params: {
        host: { type: "input", label: "主机地址", value: "localhost" },
        port: { type: "input", label: "端口", value: "3306" },
        database: { type: "input", label: "数据库名", value: "" },
        table: { type: "input", label: "表名", value: "" },
        limit: {
          type: "range",
          label: "读取行数",
          value: [1000],
          min: 100,
          max: 10000,
          step: 100,
        },
      },
    },
    {
      id: "data_reader_csv",
      name: "CSV读取",
      type: "data_reader",
      category: "data",
      icon: <FileTextOutlined />,
      description: "读取CSV文件数据",
      tags: ["文件", "读取", "CSV"],
      isPopular: true,
      params: {
        filepath: { type: "input", label: "文件路径", value: "" },
        encoding: {
          type: "select",
          label: "编码",
          value: "utf-8",
          options: ["utf-8", "gbk", "ascii"],
        },
        delimiter: { type: "input", label: "分隔符", value: "," },
      },
    },
    {
      id: "data_filter",
      name: "数据过滤",
      type: "filter",
      category: "data",
      icon: <FilterOutlined />,
      description: "根据条件过滤数据行",
      tags: ["过滤", "条件", "筛选"],
      isPopular: true,
      params: {
        column: { type: "input", label: "过滤字段", value: "" },
        operator: {
          type: "select",
          label: "操作符",
          value: "equals",
          options: [
            "equals",
            "not_equals",
            "greater_than",
            "less_than",
            "contains",
          ],
        },
        value: { type: "input", label: "过滤值", value: "" },
      },
    },
    {
      id: "linear_regression",
      name: "线性回归",
      type: "ml_model",
      category: "ml",
      icon: <ThunderboltOutlined />,
      description: "训练线性回归模型",
      tags: ["回归", "监督学习", "预测"],
      isPopular: true,
      params: {
        features: {
          type: "checkbox",
          label: "特征列",
          value: [],
          options: ["feature1", "feature2", "feature3"],
        },
        target: { type: "input", label: "目标列", value: "" },
        test_size: {
          type: "range",
          label: "测试集比例",
          value: [0.2],
          min: 0.1,
          max: 0.5,
          step: 0.1,
        },
      },
    },
    {
      id: "random_forest",
      name: "随机森林",
      type: "ml_model",
      category: "ml",
      icon: <ClusterOutlined />,
      description: "训练随机森林模型",
      tags: ["分类", "回归", "集成学习"],
      params: {
        n_estimators: {
          type: "range",
          label: "树的数量",
          value: [100],
          min: 10,
          max: 500,
          step: 10,
        },
        max_depth: {
          type: "range",
          label: "最大深度",
          value: [10],
          min: 3,
          max: 20,
          step: 1,
        },
        features: {
          type: "checkbox",
          label: "特征列",
          value: [],
          options: ["feature1", "feature2", "feature3"],
        },
      },
    },
    {
      id: "image_resize",
      name: "图像缩放",
      type: "image_transform",
      category: "vision",
      icon: <PictureOutlined />,
      description: "调整图像尺寸",
      tags: ["图像", "缩放", "预处理"],
      params: {
        width: { type: "input", label: "宽度", value: "224" },
        height: { type: "input", label: "高度", value: "224" },
        method: {
          type: "select",
          label: "缩放方法",
          value: "bilinear",
          options: ["bilinear", "nearest", "bicubic"],
        },
      },
    },
    {
      id: "object_detection",
      name: "目标检测",
      type: "vision_model",
      category: "vision",
      icon: <AimOutlined />,
      description: "检测图像中的目标对象",
      tags: ["检测", "目标", "YOLO"],
      params: {
        model: {
          type: "select",
          label: "模型",
          value: "yolov5",
          options: ["yolov5", "yolov8", "rcnn"],
        },
        confidence: {
          type: "range",
          label: "置信度阈值",
          value: [0.5],
          min: 0.1,
          max: 1.0,
          step: 0.1,
        },
        classes: {
          type: "checkbox",
          label: "检测类别",
          value: [],
          options: ["person", "car", "dog", "cat"],
        },
      },
    },
  ];

  // 生成更多算子以模拟100+的场景
  const additionalTemplates: OperatorTemplate[] = [];
  const categories = Object.keys(
    OPERATOR_CATEGORIES
  ) as (keyof typeof OPERATOR_CATEGORIES)[];
  for (let i = 0; i < 95; i++) {
    const category = categories[i % categories.length];
    additionalTemplates.push({
      id: `operator_${i + 8}`,
      name: `算子${i + 8}`,
      type: `type_${i + 8}`,
      category,
      icon: <ThunderboltOutlined />,
      description: `这是第${i + 8}个算子的描述`,
      tags: [`标签${(i % 5) + 1}`, `功能${(i % 3) + 1}`],
      isPopular: i % 10 === 0,
      params: {
        param1: { type: "input", label: "参数1", value: "" },
        param2: {
          type: "select",
          label: "参数2",
          value: "option1",
          options: ["option1", "option2", "option3"],
        },
      },
    });
  }
  return [...templates, ...additionalTemplates];
};

export const operatorList = generateOperatorTemplates();
