import { formatDate } from "@/utils/unit";
import { RatioTaskItem, RatioStatus } from "./ratio.model";

export const ratioTaskStatusMap: Record<
  string,
  {
    value: RatioStatus;
    label: string;
    color: string;
  }
> = {
  [RatioStatus.PENDING]: {
    value: RatioStatus.PENDING,
    label: "等待中",
    color: "blue",
  },
  [RatioStatus.RUNNING]: {
    value: RatioStatus.RUNNING,
    label: "运行中",
    color: "green",
  },
  [RatioStatus.COMPLETED]: {
    value: RatioStatus.COMPLETED,
    label: "已完成",
    color: "gray",
  },
  [RatioStatus.FAILED]: {
    value: RatioStatus.FAILED,
    label: "失败",
    color: "red",
  },
  [RatioStatus.PAUSED]: {
    value: RatioStatus.PAUSED,
    label: "已暂停",
    color: "orange",
  },
};

export function mapRatioTask(task: Partial<RatioTaskItem>): RatioTaskItem {
  return {
    ...task,
    status: ratioTaskStatusMap[task.status || RatioStatus.PENDING]?.value,
    createdAt: formatDate(task.created_at),
    updatedAt: formatDate(task.updated_at),
  };
}
