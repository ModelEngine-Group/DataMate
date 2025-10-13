import {
  DatabaseOutlined,
  BarChartOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  PictureOutlined,
  CalculatorOutlined,
  SwapOutlined,
} from "@ant-design/icons";
import { FileImage, FileText, Music, Repeat, Video } from "lucide-react";

// 模板类型选项
export const templateTypes = [
  {
    value: "text",
    label: "文本",
    icon: FileText,
    description: "处理文本数据的清洗模板",
  },
  {
    value: "image",
    label: "图片",
    icon: FileImage,
    description: "处理图像数据的清洗模板",
  },
  {
    value: "video",
    label: "视频",
    icon: Video,
    description: "处理视频数据的清洗模板",
  },
  {
    value: "audio",
    label: "音频",
    icon: Music,
    description: "处理音频数据的清洗模板",
  },
  {
    value: "image-to-text",
    label: "图片转文本",
    icon: Repeat,
    description: "图像识别转文本的处理模板",
  },
];

// 算子分类
export const OPERATOR_CATEGORIES = {
  data: { name: "数据清洗", icon: <DatabaseOutlined />, color: "#1677ff" },
  ml: { name: "机器学习", icon: <ThunderboltOutlined />, color: "#722ed1" },
  vision: { name: "计算机视觉", icon: <PictureOutlined />, color: "#52c41a" },
  nlp: { name: "自然语言处理", icon: <FileTextOutlined />, color: "#faad14" },
  analysis: { name: "数据分析", icon: <BarChartOutlined />, color: "#f5222d" },
  transform: { name: "数据转换", icon: <SwapOutlined />, color: "#13c2c2" },
  io: { name: "输入输出", icon: <FileTextOutlined />, color: "#595959" },
  math: { name: "数学计算", icon: <CalculatorOutlined />, color: "#fadb14" },
};
