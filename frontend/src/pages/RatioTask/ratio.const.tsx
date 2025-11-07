import { formatDate } from "@/utils/unit";
import { RatioTaskItem, RatioStatus } from "./ratio.model";
import { BarChart3 } from "lucide-react";
import { Link } from "react-router";

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
    description:
      task.ratio_method === "DATASET" ? "按数据集配比" : "按标签配比",
    icon: <BarChart3 className="w-6 h-6" />,
    iconColor: task.ratio_method === "DATASET" ? "bg-blue-100" : "bg-green-100",
    statistics: [
      {
        label: "目标数量",
        value: (task.totals ?? 0).toLocaleString(),
      },
      {
        label: "目标数据集",
        value: task.target_dataset_name ? (
          <Link to={`/data/management/detail/${task.target_dataset_id}`}>
            {task.target_dataset_name}
          </Link>
        ) : (
          "无"
        ),
      },
      {
        label: "创建时间",
        value: task.created_at || "-",
      },
    ],
  };
}
