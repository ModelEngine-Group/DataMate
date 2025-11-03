import {
  BookOpen,
  BookOpenText,
  BookType,
  ChartNoAxesColumn,
  CheckCircle,
  CircleEllipsis,
  Clock,
  Database,
  File,
  VectorSquare,
  XCircle,
} from "lucide-react";
import {
  KBFile,
  KBFileStatus,
  KBType,
  KnowledgeBaseItem,
} from "./knowledge-base.model";
import { formatBytes, formatDateTime, formatNumber } from "@/utils/unit";

export const KBFileStatusMap = {
  [KBFileStatus.PROCESSED]: {
    value: KBFileStatus.PROCESSED,
    label: "已处理",
    icon: CheckCircle,
    color: "#389e0d",
  },
  [KBFileStatus.PROCESSING]: {
    value: KBFileStatus.PROCESSING,
    label: "处理中",
    icon: Clock,
    color: "#faad14",
  },
  [KBFileStatus.PROCESS_FAILED]: {
    value: KBFileStatus.PROCESS_FAILED,
    label: "处理失败",
    icon: XCircle,
    color: "#ff4d4f",
  },
  [KBFileStatus.UNPROCESSED]: {
    value: KBFileStatus.UNPROCESSED,
    label: "未处理",
    icon: CircleEllipsis,
    color: "#d9d9d9",
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
    icon: <BookOpenText className="w-full h-full" />,
    description: kb.description,
    statistics: [
      {
        label: "索引模型",
        key: "embeddingModel",
        icon: <VectorSquare className="w-4 h-4 text-blue-500" />,
        value: kb.embeddingModel,
      },
      {
        label: "文本理解模型",
        key: "chatModel",
        icon: <BookType className="w-4 h-4 text-blue-500" />,
        value: kb.chatModel,
      },
      {
        label: "文件数",
        key: "fileCount",
        icon: <File className="w-4 h-4 text-blue-500" />,
        value: formatNumber(kb?.fileCount) || 0,
      },
      {
        label: "大小",
        key: "size",
        icon: <ChartNoAxesColumn className="w-4 h-4 text-blue-500" />,
        value: formatBytes(kb?.size) || "0 MB",
      },
    ],
    updatedAt: formatDateTime(kb.updatedAt),
    createdAt: formatDateTime(kb.createdAt),
  };
}

export function mapFileData(file: Partial<KBFile>): KBFile {
  return {
    ...file,
    name: file.fileName,
    createdAt: formatDateTime(file.createdAt),
    updatedAt: formatDateTime(file.updatedAt),
    status: KBFileStatusMap[file.status] || {
      value: file.status,
      label: "未知状态",
      icon: CircleEllipsis,
      color: "#d9d9d9",
    },
  };
}
