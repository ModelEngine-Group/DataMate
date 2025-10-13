import React from "react";

import { useState } from "react";
import { Card, Breadcrumb } from "antd";
import {
  FireOutlined,
  ShareAltOutlined,
  StarOutlined,
} from "@ant-design/icons";
import { Download, Settings, Clock, User, Package, Zap } from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import { Link } from "react-router";
import Overview from "./components/Overview";
import Install from "./components/Install";
import Documentation from "./components/Documentation";
import Examples from "./components/Examples";
import ChangeLog from "./components/ChangeLog";
import Reviews from "./components/Reviews";

export default function OperatorPluginDetail() {
  const [activeTab, setActiveTab] = useState("overview");
  const [isFavorited, setIsFavorited] = useState(false);

  // 模拟算子数据
  const operator = {
    id: 1,
    name: "图像预处理算子",
    version: "1.2.0",
    description:
      "支持图像缩放、裁剪、旋转、颜色空间转换等常用预处理操作，优化了内存使用和处理速度。这是一个高效、易用的图像预处理工具，适用于各种机器学习和计算机视觉项目。",
    author: "张三",
    authorAvatar: "/placeholder-user.jpg",
    category: "图像处理",
    modality: ["image"],
    type: "preprocessing",
    tags: [
      "图像处理",
      "预处理",
      "缩放",
      "裁剪",
      "旋转",
      "计算机视觉",
      "深度学习",
    ],
    createdAt: "2024-01-15",
    lastModified: "2024-01-23",
    status: "active",
    downloads: 1247,
    usage: 856,
    stars: 89,
    framework: "PyTorch",
    language: "Python",
    size: "2.3MB",
    license: "MIT",
    dependencies: [
      "opencv-python>=4.5.0",
      "pillow>=8.0.0",
      "numpy>=1.20.0",
      "torch>=1.9.0",
      "torchvision>=0.10.0",
    ],
    inputFormat: ["jpg", "png", "bmp", "tiff", "webp"],
    outputFormat: ["jpg", "png", "tensor", "numpy"],
    performance: {
      accuracy: 99.5,
      speed: "50ms/image",
      memory: "128MB",
      throughput: "20 images/sec",
    },
    systemRequirements: {
      python: ">=3.7",
      memory: ">=2GB RAM",
      storage: ">=100MB",
      gpu: "Optional (CUDA support)",
    },
    installCommand: "pip install image-preprocessor==1.2.0",
    documentation: `# 图像预处理算子

## 概述
这是一个高效的图像预处理算子，支持多种常用的图像处理操作。

## 主要功能
- 图像缩放和裁剪
- 旋转和翻转
- 颜色空间转换
- 噪声添加和去除
- 批量处理支持

## 性能特点
- 内存优化，支持大图像处理
- GPU加速支持
- 多线程并行处理
- 自动批处理优化`,
    examples: [
      {
        title: "基本使用",
        code: `from image_preprocessor import ImagePreprocessor

# 初始化预处理器
processor = ImagePreprocessor()

# 加载图像
image = processor.load_image("input.jpg")

# 执行预处理
result = processor.process(
    image,
    resize=(224, 224),
    normalize=True,
    augment=True
)

# 保存结果
processor.save_image(result, "output.jpg")`,
      },
      {
        title: "批量处理",
        code: `from image_preprocessor import ImagePreprocessor
import glob

processor = ImagePreprocessor()

# 批量处理图像
image_paths = glob.glob("images/*.jpg")
results = processor.batch_process(
    image_paths,
    resize=(256, 256),
    crop_center=(224, 224),
    normalize=True
)

# 保存批量结果
for i, result in enumerate(results):
    processor.save_image(result, f"output_{i}.jpg")`,
      },
      {
        title: "高级配置",
        code: `from image_preprocessor import ImagePreprocessor, Config

# 自定义配置
config = Config(
    resize_method="bilinear",
    color_space="RGB",
    normalize_mean=[0.485, 0.456, 0.406],
    normalize_std=[0.229, 0.224, 0.225],
    augmentation={
        "rotation": (-15, 15),
        "brightness": (0.8, 1.2),
        "contrast": (0.8, 1.2)
    }
)

processor = ImagePreprocessor(config)
result = processor.process(image)`,
      },
    ],
    changelog: [
      {
        version: "1.2.0",
        date: "2024-01-23",
        changes: [
          "新增批量处理功能",
          "优化内存使用，减少50%内存占用",
          "添加GPU加速支持",
          "修复旋转操作的边界问题",
        ],
      },
      {
        version: "1.1.0",
        date: "2024-01-10",
        changes: [
          "添加颜色空间转换功能",
          "支持WebP格式",
          "改进错误处理机制",
          "更新文档和示例",
        ],
      },
      {
        version: "1.0.0",
        date: "2024-01-01",
        changes: [
          "首次发布",
          "支持基本图像预处理操作",
          "包含缩放、裁剪、旋转功能",
        ],
      },
    ],
    reviews: [
      {
        id: 1,
        user: "李四",
        avatar: "/placeholder-user.jpg",
        rating: 5,
        date: "2024-01-20",
        comment:
          "非常好用的图像预处理工具，性能优秀，文档清晰。在我们的项目中大大提高了数据预处理的效率。",
      },
      {
        id: 2,
        user: "王五",
        avatar: "/placeholder-user.jpg",
        rating: 4,
        date: "2024-01-18",
        comment:
          "功能很全面，但是希望能添加更多的数据增强选项。整体来说是个不错的工具。",
      },
      {
        id: 3,
        user: "赵六",
        avatar: "/placeholder-user.jpg",
        rating: 5,
        date: "2024-01-15",
        comment:
          "安装简单，使用方便，性能表现超出预期。推荐给所有做图像处理的同学。",
      },
    ],
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: {
        label: "活跃",
        color:
          "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200",
        icon: Zap,
      },
      beta: {
        label: "测试版",
        color:
          "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200",
        icon: Settings,
      },
      deprecated: {
        label: "已弃用",
        color:
          "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200",
        icon: Settings,
      },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.active
    );
  };

  // 构造 DetailHeader 所需数据
  const headerData = {
    id: operator.id,
    icon: (
      <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
        <Package className="w-8 h-8 text-blue-600" />
      </div>
    ),
    name: operator.name,
    description: operator.description,
    status: {
      label: getStatusBadge(operator.status).label,
      icon: React.createElement(getStatusBadge(operator.status).icon, {
        className: "w-3 h-3",
      }),
      color:
        operator.status === "active"
          ? "green"
          : operator.status === "beta"
          ? "blue"
          : "gray",
    },
    createdAt: operator.createdAt,
    lastUpdated: operator.lastModified,
  };

  const statistics = [
    {
      icon: <Download className="w-4 h-4" />,
      label: "",
      value: operator.downloads.toLocaleString(),
    },
    {
      icon: <User className="w-4 h-4" />,
      label: "",
      value: operator.author,
    },
    {
      icon: <Clock className="w-4 h-4" />,
      label: "",
      value: operator.lastModified,
    },
  ];

  const operations = [
    {
      key: "favorite",
      label: "收藏",
      icon: (
        <StarOutlined
          className={`w-4 h-4 ${
            isFavorited ? "fill-yellow-400 text-yellow-400" : ""
          }`}
        />
      ),
      onClick: () => setIsFavorited(!isFavorited),
    },
    {
      key: "share",
      label: "分享",
      icon: <ShareAltOutlined />,
      onClick: () => {
        /* 分享逻辑 */
      },
    },
    {
      key: "report",
      label: "发布",
      icon: <FireOutlined />,
      onClick: () => {
        /* 发布逻辑 */
      },
    },
  ];

  return (
    <div className="min-h-screen flex flex-col gap-4">
      {/* Header */}
      <Breadcrumb
        items={[
          {
            title: <Link to="/data/operator-market">算子市场</Link>,
            href: "/data/operator-market",
          },
          {
            title: operator.name,
          },
        ]}
      />
      <DetailHeader
        data={headerData}
        statistics={statistics}
        operations={operations}
      />
      <Card
        tabList={[
          {
            key: "overview",
            label: "概览",
          },
          {
            key: "install",
            label: "安装",
          },
          {
            key: "documentation",
            label: "文档",
          },
          {
            key: "examples",
            label: "示例",
          },
          {
            key: "changelog",
            label: "更新日志",
          },
          {
            key: "reviews",
            label: "评价",
          },
        ]}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        {activeTab === "overview" && <Overview operator={operator} />}
        {activeTab === "install" && <Install operator={operator} />}
        {activeTab === "documentation" && <Documentation operator={operator} />}
        {activeTab === "examples" && <Examples operator={operator} />}
        {activeTab === "changelog" && <ChangeLog operator={operator} />}
        {activeTab === "reviews" && <Reviews operator={operator} />}
      </Card>
    </div>
  );
}
