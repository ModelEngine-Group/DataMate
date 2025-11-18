import { formatDate } from "@/utils/unit";
import { RatioTaskItem, RatioStatus } from "./ratio.model";
import { BarChart3, Calendar, Database } from "lucide-react";
import { Link } from "react-router";

export const ratioTaskStatusMap: Record<
  string,
  {
    value: RatioStatus;
    label: string;
    color: string;
    icon?: React.ReactNode;
  }
> = {
  [RatioStatus.PENDING]: {
    value: RatioStatus.PENDING,
    label: "等待中",
    color: "gray",
  },
  [RatioStatus.RUNNING]: {
    value: RatioStatus.RUNNING,
    label: "运行中",
    color: "blue",
  },
  [RatioStatus.COMPLETED]: {
    value: RatioStatus.COMPLETED,
    label: "已完成",
    color: "green",
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
    status: ratioTaskStatusMap[task.status || RatioStatus.PENDING],
    createdAt: formatDate(task.created_at),
    updatedAt: formatDate(task.updated_at),
    description:
      task.description ||
      (task.ratio_method === "DATASET" ? "按数据集配比" : "按标签配比"),
    icon: <BarChart3 />,
    iconColor: task.ratio_method === "DATASET" ? "bg-blue-100" : "bg-green-100",
    statistics: [
      {
        label: "目标数量",
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: (task.totals ?? 0).toLocaleString(),
      },
      {
        label: "目标数据集",
        icon: <Database className="w-4 h-4 text-gray-500" />,
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
        icon: <Calendar className="w-4 h-4 text-gray-500" />,
        value: task.created_at || "-",
      },
    ],
    type: task.ratio_method === "DATASET" ? "数据集配比" : "标签配比",
    // progress: 100,
    // sourceDatasets: ["sentiment_dataset", "news_classification"],
    // targetRatio: { 正面: 33, 负面: 33, 中性: 34 },
    // currentRatio: { 正面: 33, 负面: 33, 中性: 34 },
    // totalRecords: 15000,
    // processedRecords: 15000,
    // estimatedTime: "已完成",
    // quality: 95,
    // strategy: "随机下采样",
    // outputPath: "/data/balanced/sentiment_balanced_20250120",
  };
}
