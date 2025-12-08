import { StickyNote } from "lucide-react";
import {AnnotationTaskStatus, AnnotationType, Classification, DataType, TemplateType} from "./annotation.model";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";

export const AnnotationTaskStatusMap = {
  [AnnotationTaskStatus.ACTIVE]: {
    label: "活跃",
    value: AnnotationTaskStatus.ACTIVE,
    color: "#409f17ff",
    icon: <CheckCircleOutlined />,
  },
  [AnnotationTaskStatus.PROCESSING]: {
    label: "处理中",
    value: AnnotationTaskStatus.PROCESSING,
    color: "#2673e5",
    icon: <ClockCircleOutlined />,
  },
  [AnnotationTaskStatus.INACTIVE]: {
    label: "未激活",
    value: AnnotationTaskStatus.INACTIVE,
    color: "#4f4444ff",
    icon: <CloseCircleOutlined />,
  },
};

export function mapAnnotationTask(task: any) {
  // Normalize labeling project id from possible backend field names
  const labelingProjId = task?.labelingProjId || task?.labelingProjectId || task?.projId || task?.labeling_project_id || "";

  const statsArray = task?.statistics
    ? [
      { label: "准确率", value: task.statistics.accuracy ?? "-" },
      { label: "平均时长", value: task.statistics.averageTime ?? "-" },
      { label: "待复核", value: task.statistics.reviewCount ?? "-" },
    ]
    : [];

  return {
    ...task,
    id: task.id,
    // provide consistent field for components
    labelingProjId,
    projId: labelingProjId,
    name: task.name,
    description: task.description || "",
    datasetName: task.datasetName || task.dataset_name || "-",
    createdAt: task.createdAt || task.created_at || "-",
    updatedAt: task.updatedAt || task.updated_at || "-",
    icon: <StickyNote />,
    iconColor: "bg-blue-100",
    status: {
      label:
        task.status === "completed"
          ? "已完成"
          : task.status === "processing"
            ? "进行中"
            : task.status === "skipped"
              ? "已跳过"
              : "待开始",
      color: "bg-blue-100",
    },
    statistics: statsArray,
  };
}

export const DataTypeMap = {
  [DataType.TEXT]: {
    label: "文本",
    value: DataType.TEXT
  },
  [DataType.IMAGE]: {
    label: "图片",
    value: DataType.IMAGE
  },
  [DataType.AUDIO]: {
    label: "音频",
    value: DataType.AUDIO
  },
  [DataType.VIDEO]: {
    label: "视频",
    value: DataType.VIDEO
  },
}

export const ClassificationMap = {
  [Classification.COMPUTER_VERSION]: {
    label: "计算机视觉",
    value: Classification.COMPUTER_VERSION
  },
  [Classification.NLP]: {
    label: "自然语言处理",
    value: Classification.NLP
  },
  [Classification.AUDIO]: {
    label: "音频",
    value: Classification.AUDIO
  },
  [Classification.QUALITY_CONTROL]: {
    label: "质量控制",
    value: Classification.QUALITY_CONTROL
  },
  [Classification.CUSTOM]: {
    label: "自定义",
    value: Classification.CUSTOM
  },
}

export const AnnotationTypeMap = {
  [AnnotationType.CLASSIFICATION]: {
    label: "分类",
    value: AnnotationType.CLASSIFICATION
  },
  [AnnotationType.OBJECT_DETECTION]: {
    label: "目标检测",
    value: AnnotationType.OBJECT_DETECTION
  },
  [AnnotationType.SEGMENTATION]: {
    label: "分割",
    value: AnnotationType.SEGMENTATION
  },
  [AnnotationType.NER]: {
    label: "命名实体识别",
    value: AnnotationType.NER
  },
}

export const TemplateTypeMap = {
  [TemplateType.SYSTEM]: {
    label: "系统内置",
    value: TemplateType.SYSTEM
  },
  [TemplateType.CUSTOM]: {
    label: "自定义",
    value: TemplateType.CUSTOM
  },
}