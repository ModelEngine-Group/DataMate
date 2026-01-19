import React from "react";
import { Atom, Code, FileText, Film, Image, Music } from "lucide-react";
import { OperatorI } from "./operator.model";
import { formatDateTime } from "@/utils/unit.ts";

const getOperatorVisual = (
  op: OperatorI
): { modal: String; icon: React.ReactNode; iconColor?: string } => {
  const type = (op?.type || "").toLowerCase();
  const categories = (op?.categories || []).map((c) => (c || "").toLowerCase());
  const inputs = (op?.inputs || "").toLowerCase();
  const outputs = (op?.outputs || "").toLowerCase();

  // 后端固定的分类 ID，兼容 categories 传 UUID 的情况
  const CATEGORY_IDS = {
    text: "d8a5df7a-52a9-42c2-83c4-01062e60f597",
    image: "de36b61c-9e8a-4422-8c31-d30585c7100f",
    audio: "42dd9392-73e4-458c-81ff-41751ada47b5",
    video: "a233d584-73c8-4188-ad5d-8f7c8dda9c27",
  } as const;

  const hasCategoryId = (key: keyof typeof CATEGORY_IDS) =>
    (op?.categories || []).some((c) => c === CATEGORY_IDS[key]);

  const isMultimodal =
    ["multimodal", "multi", "多模态"].some((k) =>
      type.includes(k)
    ) ||
    categories.some((c) => c.includes("multimodal") || c.includes("多模态")) ||
    inputs.includes("multimodal") ||
    outputs.includes("multimodal");

  const isVideoOp =
    ["video", "视频"].includes(type) ||
    categories.some((c) => c.includes("video") || c.includes("视频")) ||
    inputs.includes("video") ||
    outputs.includes("video") ||
    hasCategoryId("video");

  const isAudioOp =
    ["audio", "音频"].includes(type) ||
    categories.some((c) => c.includes("audio") || c.includes("音频")) ||
    inputs.includes("audio") ||
    outputs.includes("audio") ||
    hasCategoryId("audio");

  const isImageOp =
    ["image", "图像", "图像类"].includes(type) ||
    categories.some((c) => c.includes("image") || c.includes("图像")) ||
    inputs.includes("image") ||
    outputs.includes("image") ||
    hasCategoryId("image");

  const isTextOp =
    ["text", "文本", "文本类"].includes(type) ||
    categories.some((c) => c.includes("text") || c.includes("文本")) ||
    inputs.includes("text") ||
    outputs.includes("text") ||
    hasCategoryId("text");

  if (isMultimodal) {
    return {
      modal: "多模态",
      icon: <Atom className="w-full h-full" />,
      iconColor: "#F472B6",
    };
  }

  if (isVideoOp) {
    return {
      modal: "视频",
      icon: <Film className="w-full h-full" />,
      iconColor: "#22D3EE",
    };
  }

  if (isAudioOp) {
    return {
      modal: "音频",
      icon: <Music className="w-full h-full" />,
      iconColor: "#F59E0B",
    };
  }

  if (isImageOp) {
    return {
      modal: "图片",
      icon: <Image className="w-full h-full" />,
      iconColor: "#38BDF8", // 图像算子背景色
    };
  }

  if (isTextOp) {
    return {
      modal: "文本",
      icon: <FileText className="w-full h-full" />,
      iconColor: "#A78BFA", // 文本算子背景色
    };
  }

  return {
    modal: "多模态",
    icon: <Code className="w-full h-full" />,
    iconColor: undefined,
  };
};

export const mapOperator = (op: OperatorI) => {
  const visual = getOperatorVisual(op);

  return {
    ...op,
    icon: visual.icon,
    iconColor: visual.iconColor,
    createdAt: formatDateTime(op?.createdAt) || "--",
    updatedAt:
      formatDateTime(op?.updatedAt) ||
      formatDateTime(op?.createdAt) ||
      "--",
    statistics: [
      {
        label: "使用次数",
        value: Math.floor(Math.random() * 1000) + 1
      },
      {
        label: "类型",
        value: visual.modal || "text",
      },
      {
        label: "大小",
        value: `${(Math.floor(Math.random() * 91) + 10) / 10} MB`,
      },
      {
        label: "语言",
        value: "Python",
      },
    ],
  };
};

export type MediaType = 'text' | 'image' | 'video' | 'audio' | 'multimodal';

const TEXT_EXTENSIONS = ['.txt', '.md', '.json', '.csv', '.doc', '.docx', '.pdf'];
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'];
const VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];
const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.aac', '.flac'];

// 3. 定义 Map 对象
export const FileExtensionMap: Record<MediaType, string[]> = {
  text: TEXT_EXTENSIONS,
  image: IMAGE_EXTENSIONS,
  video: VIDEO_EXTENSIONS,
  audio: AUDIO_EXTENSIONS,

  // 使用扩展运算符合并所有数组，生成全集
  multimodal: [
    ...TEXT_EXTENSIONS,
    ...IMAGE_EXTENSIONS,
    ...VIDEO_EXTENSIONS,
    ...AUDIO_EXTENSIONS,
  ],
};