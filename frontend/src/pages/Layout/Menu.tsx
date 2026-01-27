import {
  FolderOpen,
  MessageSquare,
  GitBranch,
  Zap,
  Shield,
  Store,
} from "lucide-react";

export const menuItems = [
  {
    id: "management",
    title: "数据管理",
    icon: FolderOpen,
    description: "创建、导入和管理数据集",
    color: "bg-blue-500",
  },
  {
    id: "cleansing",
    title: "数据处理",
    icon: GitBranch,
    description: "数据清洗和预处理",
    color: "bg-purple-500",
  },
  {
    id: "operator-market",
    title: "算子市场",
    icon: Store,
    description: "算子上传与管理",
    color: "bg-yellow-500",
  },
];

export const features = [
  {
    icon: GitBranch,
    title: "智能编排",
    description: "可视化数据清洗流程编排，拖拽式设计复杂的数据清洗管道",
  },
  {
    icon: MessageSquare,
    title: "对话助手",
    description: "通过自然语言对话完成复杂的数据集操作和业务流程",
  },
  {
    icon: Zap,
    title: "高效处理",
    description: "完整的数据清洗流水线，从原始数据到可用数据集",
  },
];
