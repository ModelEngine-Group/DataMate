"use client"

import React, { useEffect } from "react"

import { useState } from "react"
import { Card, Button, Badge, Tag, Tabs, Tooltip, Descriptions, DescriptionsProps } from "antd"
import {
    Star,
    Download,
    Eye,
    FileText,
    Settings,
    Clock,
    User,
    Package,
    Zap,
    Copy,
    Share2,
    Flag,
    ChevronRight,
    ImageIcon,
    Music,
    Video,
    ArrowLeft,
} from "lucide-react"
import { useRouter } from "next/navigation"
import DetailHeader from "@/components/ui/detail-header"

export default function OperatorDetailPage() {
    const router = useRouter()
    let id;
    const [activeTab, setActiveTab] = useState("overview")
    const [isFavorited, setIsFavorited] = useState(false)

    useEffect(() => {
        if (router.isReady) {
            id = router.query.id as string;
        }
    }, [router.isReady])

    // 模拟算子数据
    const operator = {
        id: Number.parseInt(id),
        name: "图像预处理算子",
        version: "1.2.0",
        description:
            "支持图像缩放、裁剪、旋转、颜色空间转换等常用预处理操作，优化了内存使用和处理速度。这是一个高效、易用的图像预处理工具，适用于各种机器学习和计算机视觉项目。",
        author: "张三",
        authorAvatar: "/placeholder-user.jpg",
        category: "图像处理",
        modality: ["image"],
        type: "preprocessing",
        tags: ["图像处理", "预处理", "缩放", "裁剪", "旋转", "计算机视觉", "深度学习"],
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
        dependencies: ["opencv-python>=4.5.0", "pillow>=8.0.0", "numpy>=1.20.0", "torch>=1.9.0", "torchvision>=0.10.0"],
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
                changes: ["新增批量处理功能", "优化内存使用，减少50%内存占用", "添加GPU加速支持", "修复旋转操作的边界问题"],
            },
            {
                version: "1.1.0",
                date: "2024-01-10",
                changes: ["添加颜色空间转换功能", "支持WebP格式", "改进错误处理机制", "更新文档和示例"],
            },
            {
                version: "1.0.0",
                date: "2024-01-01",
                changes: ["首次发布", "支持基本图像预处理操作", "包含缩放、裁剪、旋转功能"],
            },
        ],
        reviews: [
            {
                id: 1,
                user: "李四",
                avatar: "/placeholder-user.jpg",
                rating: 5,
                date: "2024-01-20",
                comment: "非常好用的图像预处理工具，性能优秀，文档清晰。在我们的项目中大大提高了数据预处理的效率。",
            },
            {
                id: 2,
                user: "王五",
                avatar: "/placeholder-user.jpg",
                rating: 4,
                date: "2024-01-18",
                comment: "功能很全面，但是希望能添加更多的数据增强选项。整体来说是个不错的工具。",
            },
            {
                id: 3,
                user: "赵六",
                avatar: "/placeholder-user.jpg",
                rating: 5,
                date: "2024-01-15",
                comment: "安装简单，使用方便，性能表现超出预期。推荐给所有做图像处理的同学。",
            },
        ],
    }

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
        }
        return statusConfig[status as keyof typeof statusConfig] || statusConfig.active
    }

    const getModalityIcon = (modality: string) => {
        const iconMap = {
            text: FileText,
            image: ImageIcon,
            audio: Music,
            video: Video,
        }
        const IconComponent = iconMap[modality as keyof typeof iconMap] || FileText
        return <IconComponent className="w-4 h-4" />
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
        // 这里可以添加提示消息
    }

    const descriptionItems: DescriptionsProps["items"] = [
        {
            key: "version",
            label: "版本",
            children: operator.version,
        },
        {
            key: "category",
            label: "分类",
            children: operator.category,
        },
        {
            key: "language",
            label: "语言",
            children: operator.language,
        },
        {
            key: "modality",
            label: "模态",
            children: (
                <div className="flex items-center gap-2">
                    {operator.modality.map((mod, index) => (
                        <span key={index} className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm">
                            {getModalityIcon(mod)}
                            {mod}
                        </span>
                    ))}
                </div>
            ),
        },
        {
            key: "framework",
            label: "框架",
            children: operator.framework,
        },
        {
            key: "type",
            label: "类型",
            children: operator.type,
        },
        {
            key: "size",
            label: "大小",
            children: operator.size,
        },
        {
            key: "license",
            label: "许可证",
            children: operator.license,
        },
        {
            key: "createdAt",
            label: "创建时间",
            children: operator.createdAt,
        },
        {
            key: "lastModified",
            label: "最后修改",
            children: operator.lastModified,
        },
    ]

    const renderOverviewTab = () => (
        <div className="space-y-6">
            {/* 基本信息 */}
            <Card>
                <Descriptions column={2} title="基本信息" items={descriptionItems} />
            </Card>

            {/* 标签 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">标签</h3>
                <div className="flex flex-wrap gap-2">
                    {operator.tags.map((tag, index) => (
                        <Tag key={index} className="px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
                            {tag}
                        </Tag>
                    ))}
                </div>
            </Card>

            {/* 性能指标 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">性能指标</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {operator.performance.accuracy && (
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                            <div className="text-2xl font-bold text-gray-900">{operator.performance.accuracy}%</div>
                            <div className="text-sm text-gray-600">准确率</div>
                        </div>
                    )}
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">{operator.performance.speed}</div>
                        <div className="text-sm text-gray-600">处理速度</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">{operator.performance.memory}</div>
                        <div className="text-sm text-gray-600">内存使用</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">{operator.performance.throughput}</div>
                        <div className="text-sm text-gray-600">吞吐量</div>
                    </div>
                </div>
            </Card>

            {/* 输入输出格式 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">支持格式</h3>
                <Descriptions column={2} bordered size="middle">
                    <Descriptions.Item label="输入格式">
                        <div className="flex flex-wrap gap-2">
                            {operator.inputFormat.map((format, index) => (
                                <span
                                    key={index}
                                    className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded text-sm"
                                >
                                    .{format}
                                </span>
                            ))}
                        </div>
                    </Descriptions.Item>
                    <Descriptions.Item label="输出格式">
                        <div className="flex flex-wrap gap-2">
                            {operator.outputFormat.map((format, index) => (
                                <span key={index} className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded text-sm">
                                    .{format}
                                </span>
                            ))}
                        </div>
                    </Descriptions.Item>
                </Descriptions>
            </Card>
        </div>
    )

    const renderInstallTab = () => (
        <div className="space-y-6">
            {/* 安装命令 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">安装命令</h3>
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm">
                    <div className="flex items-center justify-between">
                        <span>{operator.installCommand}</span>
                        <Button size="small" onClick={() => copyToClipboard(operator.installCommand)} className="ml-2">
                            <Copy className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </Card>

            {/* 系统要求 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">系统要求</h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="font-medium text-gray-700">Python 版本</span>
                        <span className="text-gray-900">{operator.systemRequirements.python}</span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="font-medium text-gray-700">内存要求</span>
                        <span className="text-gray-900">{operator.systemRequirements.memory}</span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <span className="font-medium text-gray-700">存储空间</span>
                        <span className="text-gray-900">{operator.systemRequirements.storage}</span>
                    </div>
                    <div className="flex items-center justify-between py-2">
                        <span className="font-medium text-gray-700">GPU 支持</span>
                        <span className="text-gray-900">{operator.systemRequirements.gpu}</span>
                    </div>
                </div>
            </Card>

            {/* 依赖项 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">依赖项</h3>
                <div className="space-y-2">
                    {operator.dependencies.map((dep, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <span className="font-mono text-sm text-gray-900">{dep}</span>
                            <Button size="small" onClick={() => copyToClipboard(dep)}>
                                <Copy className="w-3 h-3" />
                            </Button>
                        </div>
                    ))}
                </div>
            </Card>

            {/* 快速开始 */}
            <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">快速开始</h3>
                <div className="space-y-4">
                    <div>
                        <h4 className="font-medium text-gray-900 mb-2">1. 安装算子</h4>
                        <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm">{operator.installCommand}</div>
                    </div>
                    <div>
                        <h4 className="font-medium text-gray-900 mb-2">2. 导入并使用</h4>
                        <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm">
                            {`from image_preprocessor import ImagePreprocessor
processor = ImagePreprocessor()
result = processor.process(image)`}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium text-gray-900 mb-2">3. 查看结果</h4>
                        <p className="text-gray-600">处理后的图像将保存在指定路径，可以直接用于后续的机器学习任务。</p>
                    </div>
                </div>
            </Card>
        </div>
    )

    const renderDocumentationTab = () => (
        <div className="space-y-6">
            <Card>
                <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">{operator.documentation}</div>
                </div>
            </Card>
        </div>
    )

    const renderExamplesTab = () => (
        <div className="space-y-6">
            {operator.examples.map((example, index) => (
                <Card key={index}>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">{example.title}</h3>
                        <Button size="small" onClick={() => copyToClipboard(example.code)}>
                            <Copy className="w-4 h-4 mr-2" />
                            复制代码
                        </Button>
                    </div>
                    <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                        <pre className="text-sm">
                            <code>{example.code}</code>
                        </pre>
                    </div>
                </Card>
            ))}
        </div>
    )

    const renderChangelogTab = () => (
        <div className="space-y-6">
            {operator.changelog.map((version, index) => (
                <Card key={index}>
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">版本 {version.version}</h3>
                            <p className="text-sm text-gray-600">{version.date}</p>
                        </div>
                        {index === 0 && <Badge className="bg-blue-100 text-blue-800 border border-blue-200">最新版本</Badge>}
                    </div>
                    <ul className="space-y-2">
                        {version.changes.map((change, changeIndex) => (
                            <li key={changeIndex} className="flex items-start gap-2">
                                <ChevronRight className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-700">{change}</span>
                            </li>
                        ))}
                    </ul>
                </Card>
            ))}
        </div>
    )

    const renderReviewsTab = () => (
        <div className="space-y-6">
            {/* 评分统计 */}
            <Card>
                <div className="flex items-center gap-6">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-gray-900">4.7</div>
                        <div className="flex items-center justify-center gap-1 mt-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <Star key={star} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                            ))}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">基于 {operator.reviews.length} 个评价</div>
                    </div>
                    <div className="flex-1">
                        <div className="space-y-2">
                            {[5, 4, 3, 2, 1].map((rating) => {
                                const count = operator.reviews.filter((r) => r.rating === rating).length
                                const percentage = (count / operator.reviews.length) * 100
                                return (
                                    <div key={rating} className="flex items-center gap-2">
                                        <span className="text-sm text-gray-600 w-8">{rating}星</span>
                                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                                            <div className="bg-yellow-400 h-2 rounded-full" style={{ width: `${percentage}%` }} />
                                        </div>
                                        <span className="text-sm text-gray-600 w-8">{count}</span>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </Card>

            {/* 评价列表 */}
            {operator.reviews.map((review) => (
                <Card key={review.id}>
                    <div className="flex items-start gap-4">
                        <img src={review.avatar || "/placeholder.svg"} alt={review.user} className="w-10 h-10 rounded-full" />
                        <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                                <div>
                                    <h4 className="font-medium text-gray-900">{review.user}</h4>
                                    <div className="flex items-center gap-2 mt-1">
                                        <div className="flex items-center gap-1">
                                            {[1, 2, 3, 4, 5].map((star) => (
                                                <Star
                                                    key={star}
                                                    className={`w-4 h-4 ${star <= review.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                                                        }`}
                                                />
                                            ))}
                                        </div>
                                        <span className="text-sm text-gray-600">{review.date}</span>
                                    </div>
                                </div>
                            </div>
                            <p className="text-gray-700">{review.comment}</p>
                        </div>
                    </div>
                </Card>
            ))}
        </div>
    )

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
            icon: React.createElement(getStatusBadge(operator.status).icon, { className: "w-3 h-3" }),
            color: operator.status === "active" ? "green" : operator.status === "beta" ? "blue" : "gray",
        },
        createdAt: operator.createdAt,
        lastUpdated: operator.lastModified,
    }

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
    ]

    const operations = [
        {
            key: "favorite",
            label: "收藏",
            icon: <Star className={`w-4 h-4 ${isFavorited ? "fill-yellow-400 text-yellow-400" : ""}`} />,
            onClick: () => setIsFavorited(!isFavorited),
        },
        {
            key: "share",
            label: "分享",
            icon: <Share2 className="w-4 h-4" />,
            onClick: () => { /* 分享逻辑 */ },
        },
        {
            key: "report",
            label: "举报",
            icon: <Flag className="w-4 h-4" />,
            onClick: () => { /* 举报逻辑 */ },
        },
        {
            key: "install",
            label: "安装使用",
            icon: <Download className="w-4 h-4 mr-2" />,
            onClick: () => { /* 安装逻辑 */ },
        },
    ]

    return (
        <div className="h-screen bg-gray-50">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button onClick={() => router.push("/operator-market")} className="flex items-center gap-2 bg-transparent border-none">
                    <ArrowLeft className="w-4 h-4" />
                </Button>
                <h1 className="text-2xl font-bold text-gray-900">算子详情</h1>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="w-full mx-auto space-y-6">
                    {/* 使用 DetailHeader 组件替换原头部 Card */}
                    <DetailHeader
                        data={headerData}
                        statistics={statistics}
                        operations={operations}
                    />

                    {/* 标签页内容 */}
                    <Card>
                        <Tabs
                            activeKey={activeTab}
                            onChange={setActiveTab}
                            items={[
                                {
                                    key: "overview",
                                    label: "概览",
                                    children: renderOverviewTab(),
                                },
                                {
                                    key: "install",
                                    label: "安装",
                                    children: renderInstallTab(),
                                },
                                {
                                    key: "documentation",
                                    label: "文档",
                                    children: renderDocumentationTab(),
                                },
                                {
                                    key: "examples",
                                    label: "示例",
                                    children: renderExamplesTab(),
                                },
                                {
                                    key: "changelog",
                                    label: "更新日志",
                                    children: renderChangelogTab(),
                                },
                                {
                                    key: "reviews",
                                    label: "评价",
                                    children: renderReviewsTab(),
                                },
                            ]}
                        />
                    </Card>
                </div>
            </div>
        </div>
    )
}


