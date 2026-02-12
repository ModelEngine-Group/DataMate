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
    i18Key: "dataCollection.title",
    icon: Database,
    description: "创建、导入和管理数据集",
    descriptionKey: "dataCollection.description",
    color: "bg-orange-500",
  },
  {
    id: "management",
    title: "数据管理",
    i18Key: "dataManagement.title",
    icon: FolderOpen,
    description: "创建、导入和管理数据集",
    descriptionKey: "dataManagement.description",
    color: "bg-blue-500",
  },
  {
    id: "cleansing",
    title: "数据处理",
    i18Key: "dataCleansing.title",
    icon: GitBranch,
    description: "数据清洗、处理和转换",
    descriptionKey: "dataCleansing.description",
    color: "bg-purple-500",
  },
  {
    id: "annotation",
    title: "数据标注",
    i18Key: "dataAnnotation.home.title",
    icon: Tag,
    description: "对数据进行标注和标记",
    descriptionKey: "dataAnnotation.home.description",
    color: "bg-green-500",
  },
  {
    id: "synthesis",
    title: "数据合成",
    i18Key: "synthesisTask.title",
    icon: Shuffle,
    description: "智能数据合成和配比",
    descriptionKey: "synthesisTask.description",
    color: "bg-pink-500",
    children: [
      {
        id: "synthesis/task",
        title: "合成任务",
        i18Key: "synthesisTask.tabs.tasks",
        icon: Merge,
      },
      {
        id: "synthesis/ratio-task",
        title: "配比任务",
        i18Key: "ratioTask.home.title",
        icon: BarChart3,
      },
    ],
  },
  {
    id: "evaluation",
    title: "数据评估",
    i18Key: "dataEvaluation.home.title",
    icon: Target,
    badge: 4,
    description: "质量分析、性能评估和偏见检测",
    descriptionKey: "dataEvaluation.home.description",
    color: "bg-indigo-500",
  },
  {
    id: "knowledge-base",
    title: "知识生成",
    i18Key: "knowledgeBase.title",
    icon: BookOpen,
    description: "面向RAG的知识库构建",
    descriptionKey: "knowledgeBase.description",
    color: "bg-teal-500",
  },
  {
    id: "operator-market",
    title: "算子市场",
    i18Key: "operatorMarket.title",
    icon: Store,
    description: "算子上传与管理",
    descriptionKey: "operatorMarket.description",
    color: "bg-yellow-500",
  },
];

export const features = [
  {
    icon: GitBranch,
    title: "智能编排",
    description: "可视化数据处理流程编排，拖拽式设计复杂的数据处理管道",
    titleKey: "home.features.orchestration.title",
    descriptionKey: "home.features.orchestration.description"
  },
  {
    icon: MessageSquare,
    title: "对话助手",
    description: "通过自然语言对话完成复杂的数据集操作和业务流程",
    titleKey: "home.features.chatAssistant.title",
    descriptionKey: "home.features.chatAssistant.description"
  },
  {
    icon: Target,
    title: "全面评估",
    description: "多维度数据质量评估，包含统计分析、性能测试和偏见检测",
    titleKey: "home.features.evaluation.title",
    descriptionKey: "home.features.evaluation.description"
  },
  {
    icon: Zap,
    title: "高效处理",
    description: "完整的数据处理流水线，从原始数据到可用数据集",
    titleKey: "home.features.processing.title",
    descriptionKey: "home.features.processing.description"
  },
  {
    icon: Shield,
    title: "知识管理",
    description: "构建面向RAG的知识库，支持智能问答和检索",
    titleKey: "home.features.knowledge.title",
    descriptionKey: "home.features.knowledge.description"
  },
];
