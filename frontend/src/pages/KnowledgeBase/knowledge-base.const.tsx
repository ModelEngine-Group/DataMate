import {
  BookOpen,
  BookOpenText,
  CheckCircle,
  Clock,
  Database,
  XCircle,
} from "lucide-react";
import { KBStatus, KBType, KnowledgeBaseItem } from "./knowledge-base.model";
import { formatBytes, formatDateTime, formatNumber } from "@/utils/unit";

export const KBStatusMap = {
  [KBStatus.READY]: {
    label: KBStatus.READY,
    icon: CheckCircle,
    color: "#389e0d",
  },
  [KBStatus.VECTORIZING]: {
    label: KBStatus.PROCESSING,
    icon: Clock,
    color: "#3b82f6",
  },
  [KBStatus.ERROR]: {
    label: KBStatus.ERROR,
    icon: XCircle,
    color: "#ef4444",
  },
};

export const KBTypeMap = {
  [KBType.STRUCTURED]: {
    value: KBType.STRUCTURED,
    label: "结构化",
    icon: Database,
    iconColor: "blue",
    description: "用于处理和分析文本数据的数据集",
  },
  [KBType.UNSTRUCTURED]: {
    value: KBType.UNSTRUCTURED,
    label: "非结构化",
    icon: BookOpen,
    iconColor: "green",
    description: "适用于存储和管理各种格式的文件",
  },
};

export function mapKnowledgeBase(kb: KnowledgeBaseItem): KnowledgeBaseItem {
  return {
    ...kb,
    icon: <BookOpenText className="text-gray-400" />,
    description: kb.description,
    statistics: [
      { label: "索引模型", value: kb.embeddingModel },
      { label: "文本理解模型", value: kb.chatModel },
      { label: "文件数", value: formatNumber(kb?.fileCount) || 0 },
      { label: "大小", value: formatBytes(kb?.size) || "0 MB" },
    ],
    updatedAt: formatDateTime(kb.updatedAt),
    createdAt: formatDateTime(kb.createdAt),
  };
}
