import {
  FolderOpen,
  Tag,
  Target,
  BookOpen,
  Shuffle,
  BarChart3,
  MessageSquare,
  GitBranch,
  Zap,
  Shield,
  Database,
  Store,
  Merge,
} from "lucide-react";

export const menuItems = [
  {
    id: "collection",
    title: "数据归集",
    icon: Database,
    description: "创建、导入和管理数据集",
    color: "bg-orange-500",
  },
  {
    id: "management",
    title: "数据管理",
    icon: FolderOpen,
    description: "创建、导入和管理数据集",
    color: "bg-blue-500",
  },
  {
    id: "cleansing",
    title: "数据清洗",
    icon: GitBranch,
    description: "数据清洗和预处理",
    color: "bg-purple-500",
  },
  {
    id: "annotation",
    title: "数据标注",
    icon: Tag,
    description: "对数据进行标注和标记",
    color: "bg-green-500",
  },
  {
    id: "synthesis",
    title: "数据合成",
    icon: Shuffle,
    description: "智能数据合成和配比",
    color: "bg-pink-500",
    children: [
      {
        id: "synthesis/task",
        title: "合成任务",
        icon: Merge,
      },
      {
        id: "synthesis/ratio-task",
        title: "配比任务",
        icon: BarChart3,
      },
    ],
  },
  {
    id: "evaluation",
    title: "数据评估",
    icon: Target,
    badge: 4,
    description: "质量分析、性能评估和偏见检测",
    color: "bg-indigo-500",
  },
  {
    id: "knowledge-base",
    title: "知识生成",
    icon: BookOpen,
    description: "面向RAG的知识库构建",
    color: "bg-teal-500",
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
    icon: Target,
    title: "全面评估",
    description: "多维度数据质量评估，包含统计分析、性能测试和偏见检测",
  },
  {
    icon: Zap,
    title: "高效处理",
    description: "完整的数据清洗流水线，从原始数据到可用数据集",
  },
  {
    icon: Shield,
    title: "知识管理",
    description: "构建面向RAG的知识库，支持智能问答和检索",
  },
];
