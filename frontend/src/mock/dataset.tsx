import {
  BarChart3,
  FileImage,
  FileText,
  AudioLines,
  Video,
} from "lucide-react";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { DatasetTypeMap, TypeMap } from "@/pages/DataManagement/model";
import { DatasetType, type Dataset } from "@/types/dataset";

export const mockDatasets: Dataset[] = [
  {
    id: 1,
    name: "肺癌WSI病理图像数据集",
    description:
      "来自三甲医院的肺癌全切片病理图像，包含详细的病理标签和分级信息",
    type: "image",
    category: "医学影像",
    size: "1.2TB",
    itemCount: 1247,
    createdAt: "2024-01-15",
    lastModified: "2024-01-23",
    status: "active",
    tags: ["WSI", "病理", "肺癌", "分类", "分级"],
    quality: 94.2,
    isFavorited: true,
    files: [
      {
        id: 1,
        name: "slide_001.svs",
        size: "2.3GB",
        type: "image",
        uploadDate: "2024-01-15",
        path: "/data/slides/slide_001.svs",
      },
      {
        id: 2,
        name: "slide_002.svs",
        size: "2.1GB",
        type: "image",
        uploadDate: "2024-01-15",
        path: "/data/slides/slide_002.svs",
      },
      {
        id: 3,
        name: "annotations.json",
        size: "1.2MB",
        type: "json",
        uploadDate: "2024-01-16",
        path: "/data/annotations.json",
      },
      {
        id: 4,
        name: "metadata.csv",
        size: "45KB",
        type: "csv",
        uploadDate: "2024-01-16",
        path: "/data/metadata.csv",
      },
      {
        id: 5,
        name: "dataset_info.pdf",
        size: "2.1MB",
        type: "pdf",
        uploadDate: "2024-01-15",
        path: "/data/dataset_info.pdf",
      },
    ],
    annotations: {
      total: 1247,
      completed: 1205,
      accuracy: 96.8,
    },
    lineage: {
      source: "三甲医院病理科",
      processing: ["质量检查", "格式标准化", "数据增强", "标签验证"],
      training: {
        model: "ResNet-50",
        accuracy: 92.4,
        f1Score: 91.8,
      },
    },
  },
  {
    id: 2,
    name: "医学文献摘要数据集",
    description: "包含10万篇医学文献摘要，用于医学文本分类和信息抽取任务",
    type: "text",
    category: "医学文本",
    size: "2.3GB",
    itemCount: 100000,
    createdAt: "2024-01-10",
    lastModified: "2024-01-20",
    status: "active",
    tags: ["医学文献", "文本分类", "信息抽取", "NLP"],
    quality: 91.5,
    isFavorited: false,
    files: [
      {
        id: 6,
        name: "abstracts_2023.txt",
        size: "1.1GB",
        type: "text",
        uploadDate: "2024-01-10",
        path: "/data/abstracts/abstracts_2023.txt",
      },
      {
        id: 7,
        name: "abstracts_2022.txt",
        size: "1.2GB",
        type: "text",
        uploadDate: "2024-01-10",
        path: "/data/abstracts/abstracts_2022.txt",
      },
      {
        id: 8,
        name: "keywords.json",
        size: "2.5MB",
        type: "json",
        uploadDate: "2024-01-11",
        path: "/data/abstracts/keywords.json",
      },
    ],
    annotations: {
      total: 100000,
      completed: 95000,
      accuracy: 94.2,
    },
    lineage: {
      source: "PubMed数据库",
      processing: ["文本清洗", "去重", "标准化", "实体标注"],
    },
  },
  {
    id: 3,
    name: "心音异常检测数据集",
    description: "包含正常和异常心音录音，用于心脏疾病筛查和诊断",
    type: "audio",
    category: "医学音频",
    size: "45GB",
    itemCount: 8500,
    createdAt: "2024-01-08",
    lastModified: "2024-01-18",
    status: "processing",
    tags: ["心音", "异常检测", "音频分类", "心脏病"],
    quality: 88.7,
    isFavorited: true,
    files: [
      {
        id: 9,
        name: "normal_001.wav",
        size: "5.6MB",
        type: "audio",
        uploadDate: "2024-01-08",
        path: "/data/heart_sounds/normal_001.wav",
      },
      {
        id: 10,
        name: "abnormal_001.wav",
        size: "5.2MB",
        type: "audio",
        uploadDate: "2024-01-08",
        path: "/data/heart_sounds/abnormal_001.wav",
      },
      {
        id: 11,
        name: "metadata.csv",
        size: "12KB",
        type: "csv",
        uploadDate: "2024-01-09",
        path: "/data/heart_sounds/metadata.csv",
      },
    ],
    annotations: {
      total: 8500,
      completed: 7200,
      accuracy: 92.1,
    },
    lineage: {
      source: "心内科录音设备",
      processing: ["噪声去除", "音频分割", "特征提取"],
    },
  },
  {
    id: 4,
    name: "手术视频分析数据集",
    description: "腹腔镜手术视频片段，用于手术步骤识别和技能评估",
    type: "video",
    category: "医学视频",
    size: "3.2TB",
    itemCount: 1200,
    createdAt: "2024-01-05",
    lastModified: "2024-01-22",
    status: "active",
    tags: ["手术视频", "步骤识别", "技能评估", "腹腔镜"],
    quality: 96.1,
    isFavorited: false,
    files: [
      {
        id: 12,
        name: "surgery_001.mp4",
        size: "1.1GB",
        type: "video",
        uploadDate: "2024-01-05",
        path: "/data/surgery_videos/surgery_001.mp4",
      },
      {
        id: 13,
        name: "surgery_002.mp4",
        size: "1.2GB",
        type: "video",
        uploadDate: "2024-01-05",
        path: "/data/surgery_videos/surgery_002.mp4",
      },
      {
        id: 14,
        name: "steps_annotations.json",
        size: "3.1MB",
        type: "json",
        uploadDate: "2024-01-06",
        path: "/data/surgery_videos/steps_annotations.json",
      },
    ],
    annotations: {
      total: 1200,
      completed: 1200,
      accuracy: 98.2,
    },
    lineage: {
      source: "手术室录像系统",
      processing: ["视频分割", "关键帧提取", "动作标注"],
      training: {
        model: "3D CNN",
        accuracy: 94.7,
        f1Score: 93.2,
      },
    },
  },
  {
    id: 5,
    name: "多模态病历数据集",
    description: "结合文本病历、医学影像和检验报告的综合数据集",
    type: "multimodal",
    category: "多模态医学",
    size: "5.8TB",
    itemCount: 25000,
    createdAt: "2024-01-12",
    lastModified: "2024-01-21",
    status: "active",
    tags: ["多模态", "病历", "影像", "检验报告", "融合"],
    quality: 87.3,
    isFavorited: false,
    files: [
      {
        id: 15,
        name: "patient_001.pdf",
        size: "2.5MB",
        type: "pdf",
        uploadDate: "2024-01-12",
        path: "/data/multimodal/patient_001.pdf",
      },
      {
        id: 16,
        name: "patient_002.pdf",
        size: "2.3MB",
        type: "pdf",
        uploadDate: "2024-01-12",
        path: "/data/multimodal/patient_002.pdf",
      },
      {
        id: 17,
        name: "xray_001.jpg",
        size: "1.8MB",
        type: "image",
        uploadDate: "2024-01-13",
        path: "/data/multimodal/xray_001.jpg",
      },
      {
        id: 18,
        name: "lab_results.csv",
        size: "8KB",
        type: "csv",
        uploadDate: "2024-01-13",
        path: "/data/multimodal/lab_results.csv",
      },
    ],
    annotations: {
      total: 25000,
      completed: 18000,
      accuracy: 91.5,
    },
    lineage: {
      source: "医院信息系统",
      processing: ["数据对齐", "模态融合", "隐私脱敏"],
    },
  },
  {
    id: 6,
    name: "药物说明书文本数据集",
    description: "包含各类药物说明书的结构化文本数据，用于药物信息抽取",
    type: "text",
    category: "药物文本",
    size: "1.2GB",
    itemCount: 45000,
    createdAt: "2024-01-03",
    lastModified: "2024-01-19",
    status: "active",
    tags: ["药物说明书", "信息抽取", "结构化", "药学"],
    quality: 93.8,
    isFavorited: false,
    files: [
      {
        id: 19,
        name: "drug_001.txt",
        size: "650KB",
        type: "text",
        uploadDate: "2024-01-03",
        path: "/data/drug_info/drug_001.txt",
      },
      {
        id: 20,
        name: "drug_002.txt",
        size: "580KB",
        type: "text",
        uploadDate: "2024-01-03",
        path: "/data/drug_info/drug_002.txt",
      },
      {
        id: 21,
        name: "structure.json",
        size: "1.5MB",
        type: "json",
        uploadDate: "2024-01-04",
        path: "/data/drug_info/structure.json",
      },
    ],
    annotations: {
      total: 45000,
      completed: 45000,
      accuracy: 96.5,
    },
  },
  {
    id: 7,
    name: "肺部呼吸音数据集",
    description: "正常和异常肺部呼吸音录音，用于呼吸系统疾病诊断",
    type: "audio",
    category: "医学音频",
    size: "28GB",
    itemCount: 6800,
    createdAt: "2024-01-01",
    lastModified: "2024-01-17",
    status: "archived",
    tags: ["呼吸音", "肺部疾病", "音频诊断", "呼吸科"],
    quality: 89.2,
    isFavorited: false,
    files: [
      {
        id: 22,
        name: "wheezing_001.wav",
        size: "4.8MB",
        type: "audio",
        uploadDate: "2024-01-01",
        path: "/data/lung_sounds/wheezing_001.wav",
      },
      {
        id: 23,
        name: "crackles_001.wav",
        size: "5.1MB",
        type: "audio",
        uploadDate: "2024-01-01",
        path: "/data/lung_sounds/crackles_001.wav",
      },
      {
        id: 24,
        name: "normal_breathing.wav",
        size: "4.5MB",
        type: "audio",
        uploadDate: "2024-01-01",
        path: "/data/lung_sounds/normal_breathing.wav",
      },
      {
        id: 25,
        name: "patient_info.doc",
        size: "1.2MB",
        type: "doc",
        uploadDate: "2024-01-02",
        path: "/data/lung_sounds/patient_info.doc",
      },
    ],
    annotations: {
      total: 6800,
      completed: 6800,
      accuracy: 94.3,
    },
  },
];

export const statisticsData = [
  {
    title: "文本",
    value: 132,
  },
  {
    title: "图片",
    value: 435,
  },
  {
    title: "视频",
    value: 342,
  },
  {
    title: "音频",
    value: 123,
  },
];

export const mockTags = [
  "预训练",
  "微调",
  "评测",
  "WSI",
  "病理",
  "肺癌",
  "分类",
  "分级",
  "医学文献",
  "文本分类",
  "信息抽取",
  "NLP",
  "心音",
  "异常检测",
  "音频分类",
  "心脏病",
  "手术视频",
  "步骤识别",
  "技能评估",
  "腹腔镜",
  "多模态",
  "病历",
  "影像",
  "检验报告",
  "融合",
  "药物说明书",
  "结构化",
  "药学",
  "呼吸音",
  "肺部疾病",
  "音频诊断",
  "呼吸科",
];

export const datasetTypes = Object.values(DatasetTypeMap).map((type) => ({
  ...type,
  options: type.children?.map(
    (subType) => TypeMap[subType as keyof typeof TypeMap]
  ),
}));

export const mockFiles = [
  {
    id: 1,
    name: "lung_cancer_001.jpg",
    type: "image",
    size: "2.4MB",
    status: "labeled",
    labels: ["癌症", "腺癌", "T2期"],
    uploadedAt: "2024-01-15 10:30",
    confidence: 0.95,
  },
  {
    id: 2,
    name: "lung_cancer_002.jpg",
    type: "image",
    size: "1.8MB",
    status: "pending",
    labels: ["待标注"],
    uploadedAt: "2024-01-16 14:20",
    confidence: null,
  },
  {
    id: 3,
    name: "pathology_report_001.txt",
    type: "text",
    size: "15KB",
    status: "labeled",
    labels: ["病理报告", "恶性", "分化程度G2"],
    uploadedAt: "2024-01-17 09:15",
    confidence: 0.88,
  },
  {
    id: 4,
    name: "ct_scan_001.dcm",
    type: "dicom",
    size: "45MB",
    status: "reviewing",
    labels: ["CT影像", "肺部", "结节"],
    uploadedAt: "2024-01-18 16:45",
    confidence: 0.92,
  },
];

export const getStatusBadge = (status: string) => {
  const statusConfig = {
    active: {
      label: "活跃",
      color: "#409f17ff",
      icon: <CheckCircleOutlined />,
    },
    processing: {
      label: "处理中",
      color: "#2673e5",
      icon: <ClockCircleOutlined />,
    },
    archived: { label: "已归档", color: "#333333", icon: <DatabaseOutlined /> },
  };
  return (
    statusConfig[status as keyof typeof statusConfig] || statusConfig.active
  );
};

export const getTypeIcon = (type: string) => {
  const iconMap = {
    image: FileImage,
    text: FileText,
    audio: AudioLines,
    video: Video,
    multimodal: BarChart3,
    ...Object.keys(TypeMap).reduce((acc, key) => {
      acc[key] = TypeMap[key as keyof typeof TypeMap].icon;
      return acc;
    }, {}),
  };
  const IconComponent = iconMap[type as keyof typeof iconMap] || FileImage;
  return <IconComponent className="w-4 h-4" />;
};

export const getTypeColor = (type: string) => {
  const colorMap = {
    image: "bg-blue-100",
    text: "bg-green-100",
    audio: "bg-purple-100",
    video: "bg-blue-100",
    multimodal: "bg-orange-100",
    [DatasetType.EVAL]: "bg-blue-100",
    [DatasetType.PRETRAIN]: "bg-green-100",
    [DatasetType.FINE_TUNE]: "bg-purple-100",
    [DatasetType.EVAL_GSM8K]: "bg-orange-100",
    [DatasetType.EVAL_IMDB]: "bg-pink-100",
  };
  return colorMap[type as keyof typeof colorMap] || "bg-blue-100";
};
