import { StickyNote } from "lucide-react";
import {AnnotationTaskStatus, AnnotationType, Classification, DataType, TemplateType} from "./annotation.model";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";

export type TFunction = (key: string, options?: any) => string;

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

// Internationalization helper functions
export function getAnnotationTaskStatusMap(t?: TFunction) {
  const tFn = t || ((key: string) => key);
  return {
    [AnnotationTaskStatus.ACTIVE]: {
      label: tFn('dataAnnotation.const.status.active'),
      value: AnnotationTaskStatus.ACTIVE,
      color: "#409f17ff",
      icon: <CheckCircleOutlined />,
    },
    [AnnotationTaskStatus.PROCESSING]: {
      label: tFn('dataAnnotation.const.status.processing'),
      value: AnnotationTaskStatus.PROCESSING,
      color: "#2673e5",
      icon: <ClockCircleOutlined />,
    },
    [AnnotationTaskStatus.INACTIVE]: {
      label: tFn('dataAnnotation.const.status.inactive'),
      value: AnnotationTaskStatus.INACTIVE,
      color: "#4f4444ff",
      icon: <CloseCircleOutlined />,
    },
  };
}

export function getDataTypeMap(t?: TFunction) {
  const tFn = t || ((key: string) => key);
  return {
    [DataType.TEXT]: {
      label: tFn('dataAnnotation.const.dataType.text'),
      value: DataType.TEXT
    },
    [DataType.IMAGE]: {
      label: tFn('dataAnnotation.const.dataType.image'),
      value: DataType.IMAGE
    },
    [DataType.AUDIO]: {
      label: tFn('dataAnnotation.const.dataType.audio'),
      value: DataType.AUDIO
    },
    [DataType.VIDEO]: {
      label: tFn('dataAnnotation.const.dataType.video'),
      value: DataType.VIDEO
    },
  };
}

export function getClassificationMap(t?: TFunction) {
  const tFn = t || ((key: string) => key);
  return {
    [Classification.COMPUTER_VERSION]: {
      label: tFn('dataAnnotation.const.classification.cv'),
      value: Classification.COMPUTER_VERSION
    },
    [Classification.NLP]: {
      label: tFn('dataAnnotation.const.classification.nlp'),
      value: Classification.NLP
    },
    [Classification.AUDIO]: {
      label: tFn('dataAnnotation.const.classification.audio'),
      value: Classification.AUDIO
    },
    [Classification.QUALITY_CONTROL]: {
      label: tFn('dataAnnotation.const.classification.qualityControl'),
      value: Classification.QUALITY_CONTROL
    },
    [Classification.CUSTOM]: {
      label: tFn('dataAnnotation.const.classification.custom'),
      value: Classification.CUSTOM
    },
  };
}

export function getAnnotationTypeMap(t?: TFunction) {
  const tFn = t || ((key: string) => key);
  return {
    [AnnotationType.CLASSIFICATION]: {
      label: tFn('dataAnnotation.const.annotationType.classification'),
      value: AnnotationType.CLASSIFICATION
    },
    [AnnotationType.OBJECT_DETECTION]: {
      label: tFn('dataAnnotation.const.annotationType.objectDetection'),
      value: AnnotationType.OBJECT_DETECTION
    },
    [AnnotationType.SEGMENTATION]: {
      label: tFn('dataAnnotation.const.annotationType.segmentation'),
      value: AnnotationType.SEGMENTATION
    },
    [AnnotationType.NER]: {
      label: tFn('dataAnnotation.const.annotationType.ner'),
      value: AnnotationType.NER
    },
  };
}

export function getTemplateTypeMap(t?: TFunction) {
  const tFn = t || ((key: string) => key);
  return {
    [TemplateType.SYSTEM]: {
      label: tFn('dataAnnotation.const.templateType.system'),
      value: TemplateType.SYSTEM
    },
    [TemplateType.CUSTOM]: {
      label: tFn('dataAnnotation.const.templateType.custom'),
      value: TemplateType.CUSTOM
    },
  };
}

export function mapAnnotationTask(task: any, t?: TFunction) {
  // Normalize labeling project id from possible backend field names
  const labelingProjId = task?.labelingProjId || task?.labelingProjectId || task?.projId || task?.labeling_project_id || "";

  const tFn = t || ((key: string) => key);

  const statsArray = task?.statistics
    ? [
      { label: tFn('dataAnnotation.const.stats.accuracy'), value: task.statistics.accuracy ?? tFn('common.placeholders.empty') },
      { label: tFn('dataAnnotation.const.stats.averageTime'), value: task.statistics.averageTime ?? tFn('common.placeholders.empty') },
      { label: tFn('dataAnnotation.const.stats.reviewCount'), value: task.statistics.reviewCount ?? tFn('common.placeholders.empty') },
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
    datasetName: task.datasetName || task.dataset_name || tFn('common.placeholders.empty'),
    createdAt: task.createdAt || task.created_at || tFn('common.placeholders.empty'),
    updatedAt: task.updatedAt || task.updated_at || tFn('common.placeholders.empty'),
    icon: <StickyNote />,
    iconColor: "bg-blue-100",
    status: {
      label:
        task.status === "completed"
          ? tFn('dataAnnotation.const.status.completed')
          : task.status === "processing"
            ? tFn('dataAnnotation.const.status.processing')
            : task.status === "skipped"
              ? tFn('dataAnnotation.const.status.skipped')
              : tFn('dataAnnotation.const.status.pending'),
      color: "bg-blue-100",
    },
    statistics: statsArray,
  };
}