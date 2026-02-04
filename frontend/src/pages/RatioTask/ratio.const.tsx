import { formatDateTime } from "@/utils/unit";
import { RatioTaskItem, RatioStatus } from "./ratio.model";
import { BarChart3, Calendar, Database } from "lucide-react";
import { Link } from "react-router";

export type TFunction = (key: string) => string;

export function getRatioTaskStatusMap(
  t: TFunction
): Record<
  string,
  {
    value: RatioStatus;
    label: string;
    color: string;
    icon?: React.ReactNode;
  }
> {
  return {
    [RatioStatus.PENDING]: {
      value: RatioStatus.PENDING,
      label: t("common.status.task.pending"),
      color: "gray",
    },
    [RatioStatus.RUNNING]: {
      value: RatioStatus.RUNNING,
      label: t("common.status.task.running"),
      color: "blue",
    },
    [RatioStatus.COMPLETED]: {
      value: RatioStatus.COMPLETED,
      label: t("common.status.task.completed"),
      color: "green",
    },
    [RatioStatus.FAILED]: {
      value: RatioStatus.FAILED,
      label: t("common.status.task.failed"),
      color: "red",
    },
    [RatioStatus.PAUSED]: {
      value: RatioStatus.PAUSED,
      label: t("common.status.task.paused"),
      color: "orange",
    },
  };
}

export function mapRatioTask(
  task: Partial<RatioTaskItem>,
  t: TFunction
): RatioTaskItem {
  const statusMap = getRatioTaskStatusMap(t);
  return {
    ...task,
    status: statusMap[task.status || RatioStatus.PENDING],
    createdAt: formatDateTime(task.created_at),
    updatedAt: formatDateTime(task.updated_at),
    description: task.description,
    icon: <BarChart3 />,
    iconColor: task.ratio_method === "DATASET" ? "bg-blue-100" : "bg-green-100",
    statistics: [
      {
        label: t("ratioTask.detail.labels.targetCount"),
        icon: <BarChart3 className="w-4 h-4 text-gray-500" />,
        value: (task.totals ?? 0).toLocaleString(),
      },
      {
        label: t("ratioTask.detail.labels.targetDataset"),
        icon: <Database className="w-4 h-4 text-gray-500" />,
        value: task.target_dataset_name ? (
          <Link to={`/data/management/detail/${task.target_dataset_id}`}>
            {task.target_dataset_name}
          </Link>
        ) : (
          t("dataManagement.defaults.none")
        ),
      },
      {
        label: t("ratioTask.detail.labels.createdAt"),
        icon: <Calendar className="w-4 h-4 text-gray-500" />,
        value: task.created_at || t("common.placeholders.empty"),
      },
    ],
  };
}
