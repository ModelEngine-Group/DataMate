import {
  CleansingTask,
  CleansingTemplate,
  TaskStatus,
  TemplateType,
} from "@/pages/DataCleansing/cleansing.model";
import { formatDateTime } from "@/utils/unit";
import {
  ClockCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  DatabaseOutlined,
  AppstoreOutlined,
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
  [TaskStatus.PENDING]: {
    label: "待处理",
    value: TaskStatus.PENDING,
    color: "gray",
    icon: <ClockCircleOutlined />,
  },
  [TaskStatus.RUNNING]: {
    label: "进行中",
    value: TaskStatus.RUNNING,
    color: "blue",
    icon: <PlayCircleOutlined />,
  },
  [TaskStatus.COMPLETED]: {
    label: "已完成",
    value: TaskStatus.COMPLETED,
    color: "green",
    icon: <CheckCircleOutlined />,
  },
  [TaskStatus.FAILED]: {
    label: "失败",
    value: TaskStatus.FAILED,
    color: "red",
    icon: <AlertOutlined />,
  },
};

export const mapTask = (task: CleansingTask) => {
  return {
    ...task,
    createdAt: formatDateTime(task.createdAt),
    startedAt: formatDateTime(task.startedAt),
    endedAt: formatDateTime(task.endedAt),
    icon: <DatabaseOutlined style={{ color: "#1677ff" }} />,
    iconColor: "bg-blue-100",
    status: TaskStatusMap[task.status],
    statistics: [{ label: "进度", value: `${task.progress}%` }],
    lastModified: formatDateTime(task.createdAt),
  };
};

export const mapTemplate = (template: CleansingTemplate) => ({
  ...template,
  createdAt: formatDateTime(template.createdAt),
  updatedAt: formatDateTime(template.updatedAt),
  icon: <AppstoreOutlined style={{ color: "#1677ff" }} />,
  iconColor: "bg-blue-100",
  statistics: [{ label: "算子数量", value: template.instance?.length ?? 0 }],
  lastModified: formatDateTime(template.updatedAt),
});
