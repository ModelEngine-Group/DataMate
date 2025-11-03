import {
  CleansingTask,
  CleansingTemplate,
  TaskStatus,
  TemplateType,
} from "@/pages/DataCleansing/cleansing.model";
import {
  formatBytes,
  formatDateTime,
  formatExecutionDuration,
} from "@/utils/unit";
import {
  ClockCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined,
  PauseCircleOutlined,
} from "@ant-design/icons";
import { BrushCleaning, Layout } from "lucide-react";

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
  [TaskStatus.STOPPED]: {
    label: "已停止",
    value: TaskStatus.STOPPED,
    color: "orange",
    icon: <PauseCircleOutlined />,
  },
};

export const mapTask = (task: CleansingTask) => {
  const duration = formatExecutionDuration(task.startedAt, task.finishedAt);
  const before = formatBytes(task.beforeSize);
  const after = formatBytes(task.afterSize);
  const status = TaskStatusMap[task.status];
  const finishedAt = formatDateTime(task.finishedAt);
  const startedAt = formatDateTime(task.startedAt);
  const createdAt = formatDateTime(task.createdAt);
  return {
    ...task,
    ...task.progress,
    createdAt,
    startedAt,
    finishedAt,
    icon: <BrushCleaning className="w-full h-full" />,
    status,
    duration,
    before,
    after,
    statistics: [
      { label: "进度", value: `${task?.progress?.process || 0}%` },
      {
        label: "执行耗时",
        value: duration,
      },
      {
        label: "已处理文件数",
        value: task?.progress?.finishedFileNum || 0,
      },
      {
        label: "总文件数",
        value: task?.progress?.totalFileNum || 0,
      },
    ],
    lastModified: formatDateTime(task.createdAt),
  };
};

export const mapTemplate = (template: CleansingTemplate) => ({
  ...template,
  createdAt: formatDateTime(template.createdAt),
  updatedAt: formatDateTime(template.updatedAt),
  icon: <Layout className="w-full h-full" />,
  statistics: [{ label: "算子数量", value: template.instance?.length ?? 0 }],
  lastModified: formatDateTime(template.updatedAt),
});
