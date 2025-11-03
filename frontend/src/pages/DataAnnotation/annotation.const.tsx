import { StickyNote } from "lucide-react";
import { AnnotationTaskStatus } from "./annotation.model";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  CustomerServiceOutlined,
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
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
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
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
