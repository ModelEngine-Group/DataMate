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
import { AnyObject } from "antd/es/_util/type";

export function getKBFileStatusMap(t: (key: string) => string) {
  return {
    [KBFileStatus.PROCESSED]: {
      value: KBFileStatus.PROCESSED,
      label: t("knowledgeBase.const.status.processed"),
      icon: CheckCircle,
      color: "#389e0d",
    },
    [KBFileStatus.PROCESSING]: {
      value: KBFileStatus.PROCESSING,
      label: t("knowledgeBase.const.status.processing"),
      icon: Clock,
      color: "#faad14",
    },
    [KBFileStatus.PROCESS_FAILED]: {
      value: KBFileStatus.PROCESS_FAILED,
      label: t("knowledgeBase.const.status.processFailed"),
      icon: XCircle,
      color: "#ff4d4f",
    },
    [KBFileStatus.UNPROCESSED]: {
      value: KBFileStatus.UNPROCESSED,
      label: t("knowledgeBase.const.status.unprocessed"),
      icon: CircleEllipsis,
      color: "#d9d9d9",
    },
  };
}

export function getKBTypeMap(t: (key: string) => string) {
  return {
    [KBType.DOCUMENT]: {
      value: KBType.DOCUMENT,
      label: t("knowledgeBase.const.type.vector"),
      icon: BookOpen,
      iconColor: "#1d4ed8",
      description: t("knowledgeBase.const.type.vectorDesc"),
      tag: {
        label: t("knowledgeBase.const.type.vector"),
        color: "#1d4ed8",
        background: "#e0edff",
      },
    },
    [KBType.GRAPH]: {
      value: KBType.GRAPH,
      label: t("knowledgeBase.const.type.graph"),
      icon: Share2,
      iconColor: "#9333ea",
      description: t("knowledgeBase.const.type.graphDesc"),
      tag: {
        label: t("knowledgeBase.const.type.graph"),
        color: "#9333ea",
        background: "#f3e8ff",
      },
    },
  };
}

export function mapKnowledgeBase(
  kb: KnowledgeBaseItem,
  showModelFields: boolean = true,
  t: (key: string) => string
): KnowledgeBaseItem {
  const typeMeta = getKBTypeMap(t)[kb.type as keyof ReturnType<typeof getKBTypeMap>];

  return {
    ...kb,
    icon: <BookOpenText className="w-full h-full" />,
    description: kb.description,
    tags: typeMeta?.tag ? [typeMeta.tag] : undefined,
    statistics: [
      ...(showModelFields
        ? [
            {
              label: t("knowledgeBase.const.statistics.embeddingModel"),
              key: "embeddingModel",
              icon: <VectorSquare className="w-4 h-4 text-blue-500" />,
              value:
                kb.embedding?.modelName +
                  (kb.embedding?.provider
                    ? ` (${kb.embedding.provider})`
                    : "") || t("knowledgeBase.const.statistics.none"),
            },
            {
              label: t("knowledgeBase.const.statistics.chatModel"),
              key: "chatModel",
              icon: <BookType className="w-4 h-4 text-blue-500" />,
              value:
                kb.chat?.modelName +
                  (kb.chat?.provider ? ` (${kb.chat.provider})` : "") || t("knowledgeBase.const.statistics.none"),
            },
          ]
        : []),
      {
        label: t("knowledgeBase.const.statistics.fileCount"),
        key: "fileCount",
        icon: <File className="w-4 h-4 text-blue-500" />,
        value: formatNumber(kb?.fileCount) || 0,
      },
      {
        label: t("knowledgeBase.const.statistics.chunkCount"),
        key: "chunkCount",
        icon: <ChartNoAxesColumn className="w-4 h-4 text-blue-500" />,
        value: formatNumber(kb?.chunkCount) || 0,
      },
    ],
    updatedAt: formatDateTime(kb.updatedAt),
    createdAt: formatDateTime(kb.createdAt),
  };
}

export function mapFileData(file: Partial<KBFile>, t: (key: string) => string): KBFile {
  const statusMap = getKBFileStatusMap(t);
  return {
    ...file,
    name: file.fileName,
    createdAt: formatDateTime(file.createdAt),
    updatedAt: formatDateTime(file.updatedAt),
    status: statusMap[file.status] || {
      value: file.status,
      label: t("knowledgeBase.const.status.unknown"),
      icon: CircleEllipsis,
      color: "#d9d9d9",
    },
  };
}

export function getDatasetFileCols(t: (key: string) => string) {
  return [
    {
      title: t("knowledgeBase.const.fileColumns.dataset"),
      dataIndex: "datasetName",
      key: "datasetName",
      ellipsis: true,
    },
    {
      title: t("knowledgeBase.const.fileColumns.fileName"),
      dataIndex: "fileName",
      key: "fileName",
      ellipsis: true,
    },
    {
      title: t("knowledgeBase.const.fileColumns.fileSize"),
      dataIndex: "fileSize",
      key: "fileSize",
      ellipsis: true,
      render: formatBytes,
    },
  ];
}
