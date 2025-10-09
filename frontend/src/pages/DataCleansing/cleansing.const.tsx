import { JobStatus, TemplateType } from "@/pages/DataCleansing/cleansing.interface";
import {
  ClockCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  StopOutlined,
} from "@ant-design/icons";

export const templateTypesMap = {
  [TemplateType.TEXT]: {
    label: "文本",
    value: TemplateType.TEXT,
    icon: "📝",
    description: "处理文本数据的清洗模板",
  },
  [TemplateType.IMAGE]: {
    label: "图片",
    value: TemplateType.IMAGE,
    icon: "🖼️",
    description: "处理图像数据的清洗模板",
  },
  [TemplateType.VIDEO]: {
    value: TemplateType.VIDEO,
    label: "视频",
    icon: "🎥",
    description: "处理视频数据的清洗模板",
  },
  [TemplateType.AUDIO]: {
    value: TemplateType.AUDIO,
    label: "音频",
    icon: "🎵",
    description: "处理音频数据的清洗模板",
  },
  [TemplateType.IMAGE2TEXT]: {
    value: TemplateType.IMAGE2TEXT,
    label: "图片转文本",
    icon: "🔄",
    description: "图像识别转文本的处理模板",
  },
};

export const TaskStatusMap = {
  [JobStatus.PENDING]: {
    label: "待处理",
    value: JobStatus.PENDING,
    color: "gray",
    icon: <ClockCircleOutlined />,
  },
  [JobStatus.RUNNING]: {
    label: "进行中",
    value: JobStatus.RUNNING,
    color: "blue",
    icon: <PlayCircleOutlined />,
  },
  [JobStatus.COMPLETED]: {
    label: "已完成",
    value: JobStatus.COMPLETED,
    color: "green",
    icon: <CheckCircleOutlined />,
  },
  [JobStatus.FAILED]: {
    label: "失败",
    value: JobStatus.FAILED,
    color: "red",
    icon: <AlertOutlined />,
  },
  [JobStatus.CANCELLED]: {
    label: "已取消",
    value: JobStatus.CANCELLED,
    color: "orange",
    icon: <StopOutlined />,
  },
};
