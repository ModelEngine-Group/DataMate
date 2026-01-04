import React from "react";
import { Atom, Code, FileText, Film, Image, Music } from "lucide-react";
import { OperatorI } from "./operator.model";
import { formatDateTime } from "@/utils/unit.ts";

const getOperatorVisual = (
  op: OperatorI
): { icon: React.ReactNode; iconColor?: string } => {
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
      icon: <Atom className="w-full h-full" />,
      iconColor: "#F472B6",
    };
  }

  if (isVideoOp) {
    return {
      icon: <Film className="w-full h-full" />,
      iconColor: "#22D3EE",
    };
  }

  if (isAudioOp) {
    return {
      icon: <Music className="w-full h-full" />,
      iconColor: "#F59E0B",
    };
  }

  if (isImageOp) {
    return {
      icon: <Image className="w-full h-full" />,
      iconColor: "#38BDF8", // 图像算子背景色
    };
  }

  if (isTextOp) {
    return {
      icon: <FileText className="w-full h-full" />,
      iconColor: "#A78BFA", // 文本算子背景色
    };
  }

  return {
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
  };
};
