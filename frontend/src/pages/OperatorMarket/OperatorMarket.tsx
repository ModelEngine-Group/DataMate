"use client";

import { useState } from "react";
import { Button, Input, Badge, Drawer, Checkbox } from "antd";
import {
  Plus,
  Eye,
  Edit,
  Star,
  TagIcon,
  Save,
  Trash2,
  X,
  Code,
  Cpu,
  ImageIcon,
  FileText,
  Music,
  Video,
  Brain,
  Zap,
  Settings,
  Package,
  Filter,
} from "lucide-react";
import React from "react";
import { SearchControls } from "@/components/SearchControls";
import CardView from "@/components/CardView";
import { useNavigate } from "react-router";

interface Operator {
  id: number;
  name: string;
  version: string;
  description: string;
  author: string;
  category: string;
  modality: string[];
  type: "preprocessing" | "training" | "inference" | "postprocessing";
  tags: string[];
  createdAt: string;
  lastModified: string;
  status: "active" | "deprecated" | "beta";
  isFavorited?: boolean;
  downloads: number;
  usage: number;
  framework: string;
  language: string;
  size: string;
  dependencies: string[];
  inputFormat: string[];
  outputFormat: string[];
  performance: {
    accuracy?: number;
    speed: string;
    memory: string;
  };
}

const mockOperators: Operator[] = [
  {
    id: 1,
    name: "图像预处理算子",
    version: "1.2.0",
    description:
      "支持图像缩放、裁剪、旋转、颜色空间转换等常用预处理操作，优化了内存使用和处理速度",
    author: "张三",
    category: "图像处理",
    modality: ["image"],
    type: "preprocessing",
    tags: ["图像处理", "预处理", "缩放", "裁剪", "旋转"],
    createdAt: "2024-01-15",
    lastModified: "2024-01-23",
    status: "active",
    isFavorited: true,
    downloads: 1247,
    usage: 856,
    framework: "PyTorch",
    language: "Python",
    size: "2.3MB",
    dependencies: ["opencv-python", "pillow", "numpy"],
    inputFormat: ["jpg", "png", "bmp", "tiff"],
    outputFormat: ["jpg", "png", "tensor"],
    performance: {
      accuracy: 99.5,
      speed: "50ms/image",
      memory: "128MB",
    },
  },
  {
    id: 2,
    name: "文本分词算子",
    version: "2.1.3",
    description:
      "基于深度学习的中文分词算子，支持自定义词典，在医学文本上表现优异",
    author: "李四",
    category: "自然语言处理",
    modality: ["text"],
    type: "preprocessing",
    tags: ["文本处理", "分词", "中文", "NLP", "医学"],
    createdAt: "2024-01-10",
    lastModified: "2024-01-20",
    status: "active",
    isFavorited: false,
    downloads: 892,
    usage: 634,
    framework: "TensorFlow",
    language: "Python",
    size: "15.6MB",
    dependencies: ["tensorflow", "jieba", "transformers"],
    inputFormat: ["txt", "json", "csv"],
    outputFormat: ["json", "txt"],
    performance: {
      accuracy: 96.8,
      speed: "10ms/sentence",
      memory: "256MB",
    },
  },
  {
    id: 3,
    name: "音频特征提取",
    version: "1.0.5",
    description: "提取音频的MFCC、梅尔频谱、色度等特征，支持多种音频格式",
    author: "王五",
    category: "音频处理",
    modality: ["audio"],
    type: "preprocessing",
    tags: ["音频处理", "特征提取", "MFCC", "频谱分析"],
    createdAt: "2024-01-08",
    lastModified: "2024-01-18",
    status: "active",
    isFavorited: true,
    downloads: 456,
    usage: 312,
    framework: "PyTorch",
    language: "Python",
    size: "8.9MB",
    dependencies: ["librosa", "scipy", "numpy"],
    inputFormat: ["wav", "mp3", "flac", "m4a"],
    outputFormat: ["npy", "json", "csv"],
    performance: {
      speed: "2x实时",
      memory: "64MB",
    },
  },
  {
    id: 4,
    name: "视频帧提取算子",
    version: "1.3.2",
    description: "高效的视频帧提取算子，支持关键帧检测和均匀采样",
    author: "赵六",
    category: "视频处理",
    modality: ["video"],
    type: "preprocessing",
    tags: ["视频处理", "帧提取", "关键帧", "采样"],
    createdAt: "2024-01-05",
    lastModified: "2024-01-22",
    status: "active",
    isFavorited: false,
    downloads: 723,
    usage: 445,
    framework: "OpenCV",
    language: "Python",
    size: "12.4MB",
    dependencies: ["opencv-python", "ffmpeg-python"],
    inputFormat: ["mp4", "avi", "mov", "mkv"],
    outputFormat: ["jpg", "png", "npy"],
    performance: {
      speed: "30fps处理",
      memory: "512MB",
    },
  },
  {
    id: 5,
    name: "多模态融合算子",
    version: "2.0.1",
    description: "支持文本、图像、音频多模态数据融合的深度学习算子",
    author: "孙七",
    category: "多模态处理",
    modality: ["text", "image", "audio"],
    type: "training",
    tags: ["多模态", "融合", "深度学习", "注意力机制"],
    createdAt: "2024-01-12",
    lastModified: "2024-01-21",
    status: "beta",
    isFavorited: false,
    downloads: 234,
    usage: 156,
    framework: "PyTorch",
    language: "Python",
    size: "45.2MB",
    dependencies: ["torch", "transformers", "torchvision", "torchaudio"],
    inputFormat: ["json", "jpg", "wav"],
    outputFormat: ["tensor", "json"],
    performance: {
      accuracy: 94.2,
      speed: "100ms/sample",
      memory: "2GB",
    },
  },
  {
    id: 6,
    name: "模型推理加速",
    version: "1.1.0",
    description: "基于TensorRT的模型推理加速算子，支持多种深度学习框架",
    author: "周八",
    category: "模型优化",
    modality: ["image", "text"],
    type: "inference",
    tags: ["推理加速", "TensorRT", "优化", "GPU"],
    createdAt: "2024-01-03",
    lastModified: "2024-01-19",
    status: "active",
    isFavorited: true,
    downloads: 567,
    usage: 389,
    framework: "TensorRT",
    language: "Python",
    size: "23.7MB",
    dependencies: ["tensorrt", "pycuda", "numpy"],
    inputFormat: ["onnx", "pb", "pth"],
    outputFormat: ["tensor", "json"],
    performance: {
      speed: "5x加速",
      memory: "减少40%",
    },
  },
  {
    id: 7,
    name: "数据增强算子",
    version: "1.4.1",
    description: "丰富的数据增强策略，包括几何变换、颜色变换、噪声添加等",
    author: "吴九",
    category: "数据增强",
    modality: ["image"],
    type: "preprocessing",
    tags: ["数据增强", "几何变换", "颜色变换", "噪声"],
    createdAt: "2024-01-01",
    lastModified: "2024-01-17",
    status: "active",
    isFavorited: false,
    downloads: 934,
    usage: 678,
    framework: "Albumentations",
    language: "Python",
    size: "6.8MB",
    dependencies: ["albumentations", "opencv-python", "numpy"],
    inputFormat: ["jpg", "png", "bmp"],
    outputFormat: ["jpg", "png", "npy"],
    performance: {
      speed: "20ms/image",
      memory: "32MB",
    },
  },
];

export default function OperatorMarketPage() {
  const navigate = useNavigate();
  const [operators, setOperators] = useState<Operator[]>(mockOperators);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedModalities, setSelectedModalities] = useState<string[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showTagManager, setShowTagManager] = useState(false);

  const [showFilters, setShowFilters] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<
    Record<string, string[]>
  >({});
  const [sortBy, setSortBy] = useState<string>("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"card" | "list">("card");
  const filterOptions = [
    {
      key: "tag",
      label: "标签",
      options: [
        { label: "免费", value: "free" },
        { label: "付费", value: "paid" },
      ],
    },
  ];

  const sortOptions = [
    { label: "最近修改", value: "lastModified" },
    { label: "创建时间", value: "createdAt" },
    { label: "名称", value: "name" },
    { label: "使用量", value: "usage" },
    { label: "下载量", value: "downloads" },
    { label: "评分", value: "rating" },
  ];

  // Filter and sort logic
  const filteredData = mockOperators.filter((item) => {
    // Search filter
    if (
      searchTerm &&
      !item.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !item.description.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }

    // Category filter
    if (
      selectedFilters.category?.length &&
      !selectedFilters.category.includes(item.category)
    ) {
      return false;
    }

    // Type filter
    if (
      selectedFilters.type?.length &&
      !selectedFilters.type.includes(item.type)
    ) {
      return false;
    }

    // Modality filter
    if (
      selectedFilters.modality?.length &&
      !selectedFilters.modality.includes(item.modality)
    ) {
      return false;
    }

    // Status filter
    if (
      selectedFilters.status?.length &&
      !selectedFilters.status.includes(item.status)
    ) {
      return false;
    }

    // Price filter
    if (
      selectedFilters.price?.length &&
      !selectedFilters.price.includes(item.price)
    ) {
      return false;
    }

    return true;
  });

  // Sort data
  if (sortBy) {
    filteredData.sort((a, b) => {
      let aValue: any = a[sortBy as keyof Operator];
      let bValue: any = b[sortBy as keyof Operator];

      if (typeof aValue === "string") {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }

  // 视图状态管理
  const [selectedOperator, setSelectedOperator] = useState<Operator | null>(
    null
  );

  const [availableTags, setAvailableTags] = useState<string[]>([
    "图像处理",
    "预处理",
    "缩放",
    "裁剪",
    "旋转",
    "文本处理",
    "分词",
    "中文",
    "NLP",
    "医学",
    "音频处理",
    "特征提取",
    "MFCC",
    "频谱分析",
    "视频处理",
    "帧提取",
    "关键帧",
    "采样",
    "多模态",
    "融合",
    "深度学习",
    "注意力机制",
    "推理加速",
    "TensorRT",
    "优化",
    "GPU",
    "数据增强",
    "几何变换",
    "颜色变换",
    "噪声",
  ]);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");
  const [favoriteOperators, setFavoriteOperators] = useState<Set<number>>(
    new Set([1, 3, 6])
  );

  const categories = Array.from(new Set(operators.map((op) => op.category)));
  const modalities = Array.from(
    new Set(operators.flatMap((op) => op.modality))
  );
  const types = ["preprocessing", "training", "inference", "postprocessing"];
  const statuses = ["active", "beta", "deprecated"];

  const filteredOperators = operators
    .filter((operator) => {
      const matchesSearch =
        operator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        operator.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        operator.author.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCategory =
        selectedCategories.length === 0 ||
        selectedCategories.includes(operator.category);
      const matchesType =
        selectedTypes.length === 0 || selectedTypes.includes(operator.type);
      const matchesModality =
        selectedModalities.length === 0 ||
        operator.modality.some((mod) => selectedModalities.includes(mod));
      const matchesStatus =
        selectedStatuses.length === 0 ||
        selectedStatuses.includes(operator.status);
      const matchesTags =
        selectedTags.length === 0 ||
        operator.tags.some((tag) => selectedTags.includes(tag));

      return (
        matchesSearch &&
        matchesCategory &&
        matchesType &&
        matchesModality &&
        matchesStatus &&
        matchesTags
      );
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "createdAt":
          return (
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          );
        case "lastModified":
          return (
            new Date(b.lastModified).getTime() -
            new Date(a.lastModified).getTime()
          );
        case "downloads":
          return b.downloads - a.downloads;
        case "usage":
          return b.usage - a.usage;
        default:
          return 0;
      }
    });

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: {
        label: "活跃",
        color: "bg-green-100 text-green-800",
        icon: Zap,
      },
      beta: {
        label: "测试版",
        color: "bg-blue-100 text-blue-800",
        icon: Settings,
      },
      deprecated: {
        label: "已弃用",
        color: "bg-gray-100 text-gray-600",
        icon: X,
      },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.active
    );
  };

  const getTypeIcon = (type: string) => {
    const iconMap = {
      preprocessing: Code,
      training: Brain,
      inference: Cpu,
      postprocessing: Package,
    };
    const IconComponent = iconMap[type as keyof typeof iconMap] || Code;
    return <IconComponent className="w-4 h-4" />;
  };

  const getTypeColor = (type: string) => {
    const colorMap = {
      preprocessing: "bg-blue-100",
      training: "bg-green-100",
      inference: "bg-purple-100",
      postprocessing: "bg-orange-100",
    };
    return colorMap[type as keyof typeof colorMap] || "bg-blue-100";
  };

  const getModalityIcon = (modality: string) => {
    const iconMap = {
      text: FileText,
      image: ImageIcon,
      audio: Music,
      video: Video,
    };
    const IconComponent = iconMap[modality as keyof typeof iconMap] || FileText;
    return <IconComponent className="w-3 h-3" />;
  };

  const handleViewOperator = (operator: Operator) => {
    setSelectedOperator(operator);
    navigate(`/operator-market/${operator.id}/detail`);
  };

  const handleUploadOperator = () => {
    navigate(`/operator-market/create`);
  };

  const handleUpdateOperator = (operator: Operator) => {
    navigate(`/operator-market/${operator.id}/edit`);
    setSelectedOperator(operator);
  };

  const handleBackToMarket = () => {
    navigate("/operator-market");
    setSelectedOperator(null);
  };

  const handleToggleFavorite = (operatorId: number) => {
    setFavoriteOperators((prev) => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(operatorId)) {
        newFavorites.delete(operatorId);
      } else {
        newFavorites.add(operatorId);
      }
      return newFavorites;
    });

    setOperators((prev) =>
      prev.map((operator) =>
        operator.id === operatorId
          ? { ...operator, isFavorited: !operator.isFavorited }
          : operator
      )
    );
  };

  const handleCreateNewTag = () => {
    if (newTag.trim() && !availableTags.includes(newTag.trim())) {
      setAvailableTags([...availableTags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleEditTag = (oldTag: string, newTag: string) => {
    if (newTag.trim() && newTag !== oldTag) {
      setAvailableTags(
        availableTags.map((tag) => (tag === oldTag ? newTag.trim() : tag))
      );
      setOperators(
        operators.map((operator) => ({
          ...operator,
          tags: operator.tags.map((tag) =>
            tag === oldTag ? newTag.trim() : tag
          ),
        }))
      );
    }
    setEditingTag(null);
    setEditingTagValue("");
  };

  const handleDeleteTag = (tagToDelete: string) => {
    setAvailableTags(availableTags.filter((tag) => tag !== tagToDelete));
    setOperators(
      operators.map((operator) => ({
        ...operator,
        tags: operator.tags.filter((tag) => tag !== tagToDelete),
      }))
    );
  };

  const clearAllFilters = () => {
    setSearchTerm("");
    setSelectedCategories([]);
    setSelectedTypes([]);
    setSelectedModalities([]);
    setSelectedStatuses([]);
    setSelectedTags([]);
  };

  const hasActiveFilters =
    searchTerm ||
    selectedCategories.length > 0 ||
    selectedTypes.length > 0 ||
    selectedModalities.length > 0 ||
    selectedStatuses.length > 0 ||
    selectedTags.length > 0;

  const renderSidebar = () => (
    <div
      className={`w-72 bg-white border-r border-gray-200 transition-all duration-300 ${
        showFilters ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      <div className="p-4 space-y-4 h-full overflow-y-auto">
        {/* Filter Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900 flex items-center gap-2">
            <Filter className="w-4 h-4" />
            筛选器
          </h3>
          {hasActiveFilters && (
            <Button
              onClick={clearAllFilters}
              className=" text-gray-500 hover:text-gray-700 h-6 px-2"
            >
              清除
            </Button>
          )}
        </div>

        {/* Categories */}
        <div className="space-y-2">
          <h4 className=" font-medium text-gray-900">分类</h4>
          <div className="space-y-1">
            {categories.map((category) => (
              <label
                key={category}
                className="flex items-center space-x-2 cursor-pointer "
              >
                <Checkbox
                  checked={selectedCategories.includes(category)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedCategories([...selectedCategories, category]);
                    } else {
                      setSelectedCategories(
                        selectedCategories.filter((c) => c !== category)
                      );
                    }
                  }}
                />
                <span className="text-gray-700 flex-1">{category}</span>
                <span className="text-gray-400">
                  ({operators.filter((op) => op.category === category).length})
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Types */}
        <div className="space-y-2">
          <h4 className=" font-medium text-gray-900">类型</h4>
          <div className="space-y-1">
            {types.map((type) => {
              const typeLabels = {
                preprocessing: "预处理",
                training: "训练",
                inference: "推理",
                postprocessing: "后处理",
              };
              return (
                <label
                  key={type}
                  className="flex items-center space-x-2 cursor-pointer "
                >
                  <Checkbox
                    checked={selectedTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTypes([...selectedTypes, type]);
                      } else {
                        setSelectedTypes(
                          selectedTypes.filter((t) => t !== type)
                        );
                      }
                    }}
                  />
                  <div className="flex items-center gap-1 flex-1">
                    {getTypeIcon(type)}
                    <span className="text-gray-700">
                      {typeLabels[type as keyof typeof typeLabels]}
                    </span>
                  </div>
                  <span className="text-gray-400">
                    ({operators.filter((op) => op.type === type).length})
                  </span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Modalities */}
        <div className="space-y-2">
          <h4 className=" font-medium text-gray-900">模态</h4>
          <div className="space-y-1">
            {modalities.map((modality) => (
              <label
                key={modality}
                className="flex items-center space-x-2 cursor-pointer "
              >
                <Checkbox
                  checked={selectedModalities.includes(modality)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedModalities([...selectedModalities, modality]);
                    } else {
                      setSelectedModalities(
                        selectedModalities.filter((m) => m !== modality)
                      );
                    }
                  }}
                />
                <div className="flex items-center gap-1 flex-1">
                  {getModalityIcon(modality)}
                  <span className="text-gray-700">{modality}</span>
                </div>
                <span className="text-gray-400">
                  (
                  {
                    operators.filter((op) => op.modality.includes(modality))
                      .length
                  }
                  )
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Status */}
        <div className="space-y-2">
          <h4 className=" font-medium text-gray-900">状态</h4>
          <div className="space-y-1">
            {statuses.map((status) => {
              const statusLabels = {
                active: "活跃",
                beta: "测试版",
                deprecated: "已弃用",
              };
              return (
                <label
                  key={status}
                  className="flex items-center space-x-2 cursor-pointer "
                >
                  <Checkbox
                    checked={selectedStatuses.includes(status)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedStatuses([...selectedStatuses, status]);
                      } else {
                        setSelectedStatuses(
                          selectedStatuses.filter((s) => s !== status)
                        );
                      }
                    }}
                  />
                  <div className="flex-1">
                    <div className={`${getStatusBadge(status).color}`}>
                      <div className="flex items-center gap-1">
                        {React.createElement(getStatusBadge(status).icon, {
                          className: "w-3 h-3",
                        })}
                        <span>
                          {statusLabels[status as keyof typeof statusLabels]}
                        </span>
                      </div>
                    </div>
                  </div>
                  <span className="text-gray-400">
                    ({operators.filter((op) => op.status === status).length})
                  </span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="pt-3 border-t border-gray-200">
            <h4 className=" font-medium text-gray-900 mb-2">已选筛选</h4>
            <div className="space-y-1">
              {selectedCategories.map((category) => (
                <Badge
                  key={category}
                  className="bg-blue-100 text-blue-800  mr-1 mb-1"
                >
                  {category}
                  <X
                    className="w-3 h-3 ml-1 cursor-pointer"
                    onClick={() =>
                      setSelectedCategories(
                        selectedCategories.filter((c) => c !== category)
                      )
                    }
                  />
                </Badge>
              ))}
              {selectedTypes.map((type) => (
                <Badge
                  key={type}
                  className="bg-green-100 text-green-800  mr-1 mb-1"
                >
                  {type}
                  <X
                    className="w-3 h-3 ml-1 cursor-pointer"
                    onClick={() =>
                      setSelectedTypes(selectedTypes.filter((t) => t !== type))
                    }
                  />
                </Badge>
              ))}
              {selectedModalities.map((modality) => (
                <Badge
                  key={modality}
                  className="bg-purple-100 text-purple-800  mr-1 mb-1"
                >
                  {modality}
                  <X
                    className="w-3 h-3 ml-1 cursor-pointer"
                    onClick={() =>
                      setSelectedModalities(
                        selectedModalities.filter((m) => m !== modality)
                      )
                    }
                  />
                </Badge>
              ))}
              {selectedStatuses.map((status) => (
                <Badge
                  key={status}
                  className="bg-orange-100 text-orange-800  mr-1 mb-1"
                >
                  {status}
                  <X
                    className="w-3 h-3 ml-1 cursor-pointer"
                    onClick={() =>
                      setSelectedStatuses(
                        selectedStatuses.filter((s) => s !== status)
                      )
                    }
                  />
                </Badge>
              ))}
              {selectedTags.map((tag) => (
                <Badge
                  key={tag}
                  className="bg-pink-100 text-pink-800  mr-1 mb-1"
                >
                  {tag}
                  <X
                    className="w-3 h-3 ml-1 cursor-pointer"
                    onClick={() =>
                      setSelectedTags(selectedTags.filter((t) => t !== tag))
                    }
                  />
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderCardView = () => (
    <CardView
      data={filteredOperators.map((operator) => ({
        ...operator,
        icon: getTypeIcon(operator.type),
        iconColor: getTypeColor(operator.type),
        statusColor: getStatusBadge(operator.status).color,
        statusLabel: getStatusBadge(operator.status).label,
        statistics: [
          { label: "使用次数", value: operator.usage.toLocaleString() },
          { label: "框架", value: operator.framework },
          { label: "大小", value: operator.size },
          { label: "语言", value: operator.language },
        ],
      }))}
      pageSize={8}
      operations={[
        { key: "view", label: "查看详情", onClick: handleViewOperator },
        { key: "edit", label: "更新算子", onClick: handleUpdateOperator },
        { key: "delete", label: "删除算子", onClick: handleDeleteTag },
      ]}
      onView={handleViewOperator}
      onFavorite={(item) => handleToggleFavorite(item.id)}
      isFavorite={(item) => favoriteOperators.has(item.id)}
    />
  );

  const renderListView = () => (
    <div className="bg-white rounded-lg border">
      <div className="grid grid-cols-12 gap-4 p-4 border-b bg-gray-50 text-sm font-medium text-gray-700">
        <div className="col-span-3">名称</div>
        <div className="col-span-1">版本</div>
        <div className="col-span-1">类型</div>
        <div className="col-span-2">模态</div>
        <div className="col-span-1">状态</div>
        <div className="col-span-1">使用次数</div>
        <div className="col-span-1">框架</div>
        <div className="col-span-2">操作</div>
      </div>
      {filteredOperators.map((operator) => (
        <div
          key={operator.id}
          className="grid grid-cols-12 gap-4 p-4 border-b hover:bg-gray-50 transition-colors"
        >
          <div className="col-span-3 flex items-center gap-3">
            <div
              className={`w-8 h-8 ${getTypeColor(
                operator.type
              )} rounded flex items-center justify-center`}
            >
              {getTypeIcon(operator.type)}
            </div>
            <div>
              <h4
                className="font-medium text-gray-900 cursor-pointer hover:text-blue-600"
                onClick={() => handleViewOperator(operator)}
              >
                {operator.name}
              </h4>
              <p className=" text-gray-500">{operator.author}</p>
            </div>
          </div>
          <div className="col-span-1 flex items-center">
            <span className="text-sm">v{operator.version}</span>
          </div>
          <div className="col-span-1 flex items-center">
            <Badge variant="outline" className="">
              {operator.type}
            </Badge>
          </div>
          <div className="col-span-2 flex items-center gap-1">
            {operator.modality.map((mod, index) => (
              <div
                key={index}
                className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded "
              >
                {getModalityIcon(mod)}
                <span>{mod}</span>
              </div>
            ))}
          </div>
          <div className="col-span-1 flex items-center">
            <div className={getStatusBadge(operator.status).color}>
              <div className="flex items-center gap-1">
                {React.createElement(getStatusBadge(operator.status).icon, {
                  className: "w-3 h-3",
                })}
                <span>{getStatusBadge(operator.status).label}</span>
              </div>
            </div>
          </div>
          <div className="col-span-1 flex items-center">
            <span className="text-sm">{operator.usage.toLocaleString()}</span>
          </div>
          <div className="col-span-1 flex items-center">
            <span className="text-sm">{operator.framework}</span>
          </div>
          <div className="col-span-2 flex items-center gap-2">
            <Button
              onClick={() => handleViewOperator(operator)}
              className="h-8 w-8 p-0"
              title="查看详情"
            >
              <Eye className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => handleUpdateOperator(operator)}
              className="h-8 w-8 p-0 bg-transparent"
              title="更新算子"
            >
              <Edit className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => handleToggleFavorite(operator.id)}
              className={`h-8 w-8 p-0 border-none ${
                favoriteOperators.has(operator.id)
                  ? "text-yellow-500 hover:text-yellow-600"
                  : "text-gray-400 hover:text-yellow-500"
              }`}
            >
              <Star
                className={`w-4 h-4 ${
                  favoriteOperators.has(operator.id) ? "fill-current" : ""
                }`}
              />
            </Button>
            <Button
              className="h-8 w-8 p-0 text-red-500 hover:text-red-700 bg-transparent"
              title="删除算子"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );

  const renderMarketView = () => (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      {renderSidebar()}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => setShowFilters(!showFilters)}
                className="lg:hidden"
                icon={<Filter className="w-4 h-4" />}
              >
                筛选
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">算子市场</h1>
                <p className="text-gray-600 text-sm">发现和分享机器学习算子</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setShowTagManager(true)}
                icon={<TagIcon className="w-4 h-4 mr-2" />}
              >
                标签管理
              </Button>
              <Button
                onClick={handleUploadOperator}
                icon={<Plus className="w-4 h-4 mr-2" />}
              >
                上传算子
              </Button>
            </div>
          </div>
        </div>
        <SearchControls
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          searchPlaceholder="搜索算子..."
          filters={filterOptions}
          selectedFilters={selectedFilters}
          onFiltersChange={setSelectedFilters}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortChange={(field, order) => {
            setSortBy(field);
            setSortOrder(order);
          }}
          sortOptions={sortOptions}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          showViewToggle={true}
        />

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredOperators.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                没有找到匹配的算子
              </h3>
              <p className="text-gray-500">尝试调整筛选条件或搜索关键词</p>
            </div>
          ) : (
            <>{viewMode === "card" ? renderCardView() : renderListView()}</>
          )}
        </div>
      </div>

      {/* Tag Manager */}
      <Drawer
        visible={showTagManager}
        onClose={() => setShowTagManager(false)}
        title="标签管理"
      >
        <div className="space-y-6 mt-6">
          {/* Add New Tag */}
          <div className="space-y-2">
            <label>添加新标签</label>
            <div className="flex gap-2">
              <Input
                placeholder="输入标签名称..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    handleCreateNewTag();
                  }
                }}
              />
              <Button onClick={handleCreateNewTag} disabled={!newTag.trim()}>
                <Plus className="w-4 h-4 mr-2" />
                添加
              </Button>
            </div>
          </div>

          {/* Existing Tags */}
          <div className="grid grid-cols-2 gap-2">
            {availableTags.map((tag) => (
              <div
                key={tag}
                className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50"
              >
                {editingTag === tag ? (
                  <div className="flex gap-2 flex-1">
                    <Input
                      value={editingTagValue}
                      onChange={(e) => setEditingTagValue(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          handleEditTag(tag, editingTagValue);
                        }
                        if (e.key === "Escape") {
                          setEditingTag(null);
                          setEditingTagValue("");
                        }
                      }}
                      className="h-6 text-sm"
                      autoFocus
                    />
                    <Button
                      onClick={() => handleEditTag(tag, editingTagValue)}
                      className="h-6 w-6 p-0"
                    >
                      <Save className="w-3 h-3" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <span className="text-sm">{tag}</span>
                    <div className="flex gap-1">
                      <Button
                        onClick={() => {
                          setEditingTag(tag);
                          setEditingTagValue(tag);
                        }}
                        className="h-6 w-6 p-0"
                      >
                        <Edit className="w-3 h-3" />
                      </Button>
                      <Button
                        onClick={() => handleDeleteTag(tag)}
                        className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </Drawer>
    </div>
  );

  return renderMarketView();
}
