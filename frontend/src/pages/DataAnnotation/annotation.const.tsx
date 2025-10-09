import { AnnotationTaskStatus } from "./annotation.interface";
import React from "react";
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
