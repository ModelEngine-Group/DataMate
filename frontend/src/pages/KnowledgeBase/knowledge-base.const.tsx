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
  Share2,
  Network,
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
  [KBType.DOCUMENT]: {
    value: KBType.DOCUMENT,
    label: "向量知识库",
    icon: BookOpen,
    iconColor: "#1d4ed8",
    description: "面向非结构化文档的检索问答",
    tag: {
      label: "向量知识库",
      color: "#1d4ed8",
      background: "#e0edff",
    },
  },
  [KBType.GRAPH]: {
    value: KBType.GRAPH,
    label: "知识图谱",
    icon: Share2,
    iconColor: "#9333ea",
    description: "管理实体与关系的图谱知识",
    tag: {
      label: "知识图谱",
      color: "#9333ea",
      background: "#f3e8ff",
    },
  },
};

export function mapKnowledgeBase(
  kb: KnowledgeBaseItem,
  showModelFields: boolean = true
): KnowledgeBaseItem {
  const typeMeta = KBTypeMap[kb.type as keyof typeof KBTypeMap];

  return {
    ...kb,
    icon: <BookOpenText className="w-full h-full" />,
    description: kb.description,
    tags: typeMeta?.tag ? [typeMeta.tag] : undefined,
    statistics: [
      ...(showModelFields
        ? [
            {
              label: "索引模型",
              key: "embeddingModel",
              icon: <VectorSquare className="w-4 h-4 text-blue-500" />,
              value:
                kb.embedding?.modelName +
                  (kb.embedding?.provider
                    ? ` (${kb.embedding.provider})`
                    : "") || "无",
            },
            {
              label: "文本理解模型",
              key: "chatModel",
              icon: <BookType className="w-4 h-4 text-blue-500" />,
              value:
                kb.chat?.modelName +
                  (kb.chat?.provider ? ` (${kb.chat.provider})` : "") || "无",
            },
          ]
        : []),
      {
        label: "文件数",
        key: "fileCount",
        icon: <File className="w-4 h-4 text-blue-500" />,
        value: formatNumber(kb?.fileCount) || 0,
      },
      {
        label: "分块数",
        key: "chunkCount",
        icon: <ChartNoAxesColumn className="w-4 h-4 text-blue-500" />,
        value: formatNumber(kb?.chunkCount) || 0,
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

export const DatasetFileCols = [
  {
    title: "所属数据集",
    dataIndex: "datasetName",
    key: "datasetName",
    ellipsis: true,
  },
  {
    title: "文件名",
    dataIndex: "fileName",
    key: "fileName",
    ellipsis: true,
  },
  {
    title: "大小",
    dataIndex: "fileSize",
    key: "fileSize",
    ellipsis: true,
    render: formatBytes,
  },
];
