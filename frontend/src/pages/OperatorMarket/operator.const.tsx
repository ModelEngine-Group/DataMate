import React from "react";
import { Code, FileSliders, Image } from "lucide-react";
import { OperatorI } from "./operator.model";
import { formatDateTime } from "@/utils/unit.ts";

const getOperatorVisual = (
  op: OperatorI
): { icon: React.ReactNode; iconColor?: string } => {
  const type = (op?.type || "").toLowerCase();
  const categories = (op?.categories || []).map((c) => (c || "").toLowerCase());
  const inputs = (op?.inputs || "").toLowerCase();
  const outputs = (op?.outputs || "").toLowerCase();

  const isImageOp =
    ["image", "图像", "图像类"].includes(type) ||
    categories.some((c) => c.includes("image") || c.includes("图像")) ||
    inputs.includes("image") ||
    outputs.includes("image");

  const isTextOp =
    ["text", "文本", "文本类"].includes(type) ||
    categories.some((c) => c.includes("text") || c.includes("文本")) ||
    inputs.includes("text") ||
    outputs.includes("text");

  if (isImageOp) {
    return {
      icon: <Image className="w-full h-full" />,
      iconColor: "#38BDF8", // 图像算子背景色
    };
  }

  if (isTextOp) {
    return {
      icon: <FileSliders className="w-full h-full" />,
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
