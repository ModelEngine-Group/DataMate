import {
  DatasetType,
  DatasetStatus,
  type Dataset,
  DatasetSubType,
  DataSource,
} from "@/pages/DataManagement/dataset.model";
import { formatBytes, formatDateTime } from "@/utils/unit";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  FileOutlined,
} from "@ant-design/icons";
import { AnyObject } from "antd/es/_util/type";
import {
  FileImage,
  FileText,
  Video,
  Film,
  FileCode,
  MessageCircleMore,
  ImagePlus,
  FileMusic,
  Music,
  Videotape,
  Database,
  Image,
  ScanText,
} from "lucide-react";

export function getDatasetTypeMap(t: (key: string) => string): Record<
  string,
  {
    value: DatasetType;
    label: string;
    order: number;
    description: string;
    icon?: any;
    iconColor?: string;
    children: DatasetSubType[];
  }
> {
  return {
    [DatasetType.TEXT]: {
      value: DatasetType.TEXT,
      label: t("dataManagement.datasetTypes.text"),
      order: 1,
      icon: ScanText,
      iconColor: "#A78BFA",
      children: [
        DatasetSubType.TEXT_DOCUMENT,
        DatasetSubType.TEXT_WEB,
        DatasetSubType.TEXT_DIALOG,
      ],
      description: t("dataManagement.datasetTypeDesc.text"),
    },
    [DatasetType.IMAGE]: {
      value: DatasetType.IMAGE,
      label: t("dataManagement.datasetTypes.image"),
      order: 2,
      icon: Image,
      iconColor: "#38BDF8",
      children: [DatasetSubType.IMAGE_IMAGE, DatasetSubType.IMAGE_CAPTION],
      description: t("dataManagement.datasetTypeDesc.image"),
    },
    [DatasetType.AUDIO]: {
      value: DatasetType.AUDIO,
      label: t("dataManagement.datasetTypes.audio"),
      order: 3,
      icon: Music,
      iconColor: "#F59E0B",
      children: [DatasetSubType.AUDIO_AUDIO, DatasetSubType.AUDIO_JSONL],
      description: t("dataManagement.datasetTypeDesc.audio"),
    },
    [DatasetType.VIDEO]: {
      value: DatasetType.VIDEO,
      label: t("dataManagement.datasetTypes.video"),
      order: 3,
      icon: Film,
      iconColor: "#22D3EE",
      children: [DatasetSubType.VIDEO_VIDEO, DatasetSubType.VIDEO_JSONL],
      description: t("dataManagement.datasetTypeDesc.video"),
    },
  };
}

export function getDatasetSubTypeMap(t: (key: string) => string): Record<
  string,
  {
    value: DatasetSubType;
    label: string;
    order?: number;
    description?: string;
    icon?: any;
    color?: string;
  }
> {
  return {
    [DatasetSubType.TEXT_DOCUMENT]: {
      value: DatasetSubType.TEXT_DOCUMENT,
      label: t("dataManagement.datasetSubTypes.textDocument"),
      color: "blue",
      icon: FileText,
      description: t("dataManagement.datasetSubTypeDesc.textDocument"),
    },
    [DatasetSubType.TEXT_WEB]: {
      value: DatasetSubType.TEXT_WEB,
      label: t("dataManagement.datasetSubTypes.textWeb"),
      color: "cyan",
      icon: FileCode,
      description: t("dataManagement.datasetSubTypeDesc.textWeb"),
    },
    [DatasetSubType.TEXT_DIALOG]: {
      value: DatasetSubType.TEXT_DIALOG,
      label: t("dataManagement.datasetSubTypes.textDialog"),
      color: "teal",
      icon: MessageCircleMore,
      description: t("dataManagement.datasetSubTypeDesc.textDialog"),
    },
    [DatasetSubType.IMAGE_IMAGE]: {
      value: DatasetSubType.IMAGE_IMAGE,
      label: t("dataManagement.datasetSubTypes.imageImage"),
      color: "green",
      icon: FileImage,
      description: t("dataManagement.datasetSubTypeDesc.imageImage"),
    },
    [DatasetSubType.IMAGE_CAPTION]: {
      value: DatasetSubType.IMAGE_CAPTION,
      label: t("dataManagement.datasetSubTypes.imageCaption"),
      color: "lightgreen",
      icon: ImagePlus,
      description: t("dataManagement.datasetSubTypeDesc.imageCaption"),
    },
    [DatasetSubType.AUDIO_AUDIO]: {
      value: DatasetSubType.AUDIO_AUDIO,
      label: t("dataManagement.datasetSubTypes.audioAudio"),
      color: "purple",
      icon: Music,
      description: t("dataManagement.datasetSubTypeDesc.audioAudio"),
    },
    [DatasetSubType.AUDIO_JSONL]: {
      value: DatasetSubType.AUDIO_JSONL,
      label: t("dataManagement.datasetSubTypes.audioJsonl"),
      color: "purple",
      icon: FileMusic,
      description: t("dataManagement.datasetSubTypeDesc.audioJsonl"),
    },
    [DatasetSubType.VIDEO_VIDEO]: {
      value: DatasetSubType.VIDEO_VIDEO,
      label: t("dataManagement.datasetSubTypes.videoVideo"),
      color: "orange",
      icon: Video,
      description: t("dataManagement.datasetSubTypeDesc.videoVideo"),
    },
    [DatasetSubType.VIDEO_JSONL]: {
      value: DatasetSubType.VIDEO_JSONL,
      label: t("dataManagement.datasetSubTypes.videoJsonl"),
      color: "orange",
      icon: Videotape,
      description: t("dataManagement.datasetSubTypeDesc.videoJsonl"),
    },
  };
}

export function getDatasetStatusMap(t: (key: string) => string) {
  return {
    [DatasetStatus.ACTIVE]: {
      label: t("dataManagement.datasetStatus.active"),
      value: DatasetStatus.ACTIVE,
      color: "#409f17ff",
      icon: <CheckCircleOutlined />,
    },
    [DatasetStatus.PROCESSING]: {
      label: t("dataManagement.datasetStatus.processing"),
      value: DatasetStatus.PROCESSING,
      color: "#2673e5",
      icon: <ClockCircleOutlined />,
    },
    [DatasetStatus.INACTIVE]: {
      label: t("dataManagement.datasetStatus.inactive"),
      value: DatasetStatus.INACTIVE,
      color: "#4f4444ff",
      icon: <CloseCircleOutlined />,
    },
    [DatasetStatus.DRAFT]: {
      label: t("dataManagement.datasetStatus.draft"),
      value: DatasetStatus.DRAFT,
      color: "#a1a1a1ff",
      icon: <FileOutlined />,
    },
  };
}

export function getDataSourceMap(t: (key: string) => string): Record<
  string,
  { label: string; value: string }
> {
  return {
    [DataSource.UPLOAD]: {
      label: t("dataManagement.dataSources.upload"),
      value: DataSource.UPLOAD,
    },
    [DataSource.COLLECTION]: {
      label: t("dataManagement.dataSources.collection"),
      value: DataSource.COLLECTION,
    },
  };
}

export function mapDataset(dataset: AnyObject, t: (key: string) => string): Dataset {
  const datasetTypeMap = getDatasetTypeMap(t);
  const datasetStatusMap = getDatasetStatusMap(t);
  const { icon: IconComponent, iconColor } =
    datasetTypeMap[dataset?.datasetType] || {};
  return {
    ...dataset,
    key: dataset.id,
    type: datasetTypeMap[dataset.datasetType]?.label || t("dataManagement.defaults.unknown"),
    size: formatBytes(dataset.totalSize || 0),
    createdAt: formatDateTime(dataset.createdAt) || t("dataManagement.defaults.empty"),
    updatedAt: formatDateTime(dataset?.updatedAt) || t("dataManagement.defaults.empty"),
    icon: IconComponent ? <IconComponent className="w-full h-full" /> : <Database />,
    iconColor: iconColor,
    status: datasetStatusMap[dataset.status],
    statistics: [
      { label: t("dataManagement.labels.fileCount"), value: dataset.fileCount || 0 },
      { label: t("dataManagement.labels.dataSize"), value: formatBytes(dataset.totalSize || 0) },
    ],
    lastModified: dataset.updatedAt,
  };
}

export function getDatasetTypes(t: (key: string) => string) {
  const datasetTypeMap = getDatasetTypeMap(t);
  const datasetSubTypeMap = getDatasetSubTypeMap(t);
  return Object.values(datasetTypeMap).map((type) => ({
    ...type,
    options: type.children?.map(
      (subType) => datasetSubTypeMap[subType as keyof typeof datasetSubTypeMap]
    ),
  }));
}
