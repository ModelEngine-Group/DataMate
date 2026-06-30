import { BarChart, Circle, Grid, ImageIcon, Layers, Maximize, MousePointer, Move, Square, Target, Crop, RotateCcw, FileText, Tag, Heart, HelpCircle, BookOpen, MessageSquare, Users, Zap, Globe, Scissors } from "lucide-react";

// Define the AnnotationTask type if not imported from elsewhere
interface AnnotationTask {
    id: string
    name: string
    completed: string
    completedCount: number
    skippedCount: number
    totalCount: number
    annotators: Array<{
        id: string
        name: string
        avatar?: string
    }>
    text: string
    status: "completed" | "in_progress" | "pending" | "skipped"
    project: string
    type: "图像分类" | "文本分类" | "目标检测" | "NER" | "语音识别" | "视频分析"
    datasetType: "text" | "image" | "video" | "audio"
    progress: number
}


export const mockTasks: AnnotationTask[] = [
    {
        id: "12345678",
        name: "图像分类标注任务",
        completed: "2024年1月20日 20:40",
        completedCount: 1,
        skippedCount: 0,
        totalCount: 2,
        annotators: [
            { id: "1", name: "张三", avatar: "/placeholder-user.jpg" },
            { id: "2", name: "李四", avatar: "/placeholder-user.jpg" },
        ],
        text: "对产品图像进行分类标注，包含10个类别",
        status: "completed",
        project: "图像分类",
        type: "图像分类",
        datasetType: "image",
        progress: 100,
    },
    {
        id: "12345679",
        name: "文本情感分析标注",
        completed: "2024年1月20日 20:40",
        completedCount: 2,
        skippedCount: 0,
        totalCount: 2,
        annotators: [
            { id: "1", name: "王五", avatar: "/placeholder-user.jpg" },
            { id: "2", name: "赵六", avatar: "/placeholder-user.jpg" },
        ],
        text: "对用户评论进行情感倾向标注",
        status: "completed",
        project: "文本分类",
        type: "文本分类",
        datasetType: "text",
        progress: 100,
    },
    {
        id: "12345680",
        name: "目标检测标注任务",
        completed: "2024年1月20日 20:40",
        completedCount: 1,
        skippedCount: 0,
        totalCount: 2,
        annotators: [{ id: "1", name: "孙七", avatar: "/placeholder-user.jpg" }],
        text: "对交通场景图像进行目标检测标注",
        status: "in_progress",
        project: "目标检测",
        type: "目标检测",
        datasetType: "image",
        progress: 50,
    },
    {
        id: "12345681",
        name: "命名实体识别标注",
        completed: "2024年1月20日 20:40",
        completedCount: 1,
        skippedCount: 0,
        totalCount: 2,
        annotators: [{ id: "1", name: "周八", avatar: "/placeholder-user.jpg" }],
        text: "对新闻文本进行命名实体识别标注",
        status: "in_progress",
        project: "NER",
        type: "NER",
        datasetType: "text",
        progress: 75,
    },
    {
        id: "12345682",
        name: "语音识别标注任务",
        completed: "2024年1月20日 20:40",
        completedCount: 1,
        skippedCount: 0,
        totalCount: 2,
        annotators: [{ id: "1", name: "吴九", avatar: "/placeholder-user.jpg" }],
        text: "对语音数据进行转录和标注",
        status: "in_progress",
        project: "语音识别",
        type: "语音识别",
        datasetType: "audio",
        progress: 25,
    },
    {
        id: "12345683",
        name: "视频动作识别标注",
        completed: "2024年1月20日 20:40",
        completedCount: 0,
        skippedCount: 2,
        totalCount: 2,
        annotators: [
            { id: "1", name: "陈十", avatar: "/placeholder-user.jpg" },
            { id: "2", name: "林十一", avatar: "/placeholder-user.jpg" },
        ],
        text: "对视频中的人体动作进行识别和标注",
        status: "skipped",
        project: "视频分析",
        type: "视频分析",
        datasetType: "video",
        progress: 0,
    },
]

// Define the Template type
type Template = {
    id: string;
    name: string;
    category: string;
    description: string;
    type: string;
    preview?: string;
    icon: React.ReactNode;
};

// 扩展的预制模板数据
export const mockTemplates: Template[] = [
    // 计算机视觉模板
    {
        id: "cv-1",
        name: "目标检测",
        category: "Computer Vision",
        description: "使用边界框标注图像中的目标对象",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Object+Detection",
        icon: <Square className="w-4 h-4" />,
    },
    {
        id: "cv-2",
        name: "语义分割（多边形）",
        category: "Computer Vision",
        description: "使用多边形精确标注图像中的区域",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Polygon+Segmentation",
        icon: <Layers className="w-4 h-4" />,
    },
    {
        id: "cv-3",
        name: "语义分割（掩码）",
        category: "Computer Vision",
        description: "使用像素级掩码标注图像区域",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Mask+Segmentation",
        icon: <Circle className="w-4 h-4" />,
    },
    {
        id: "cv-4",
        name: "关键点标注",
        category: "Computer Vision",
        description: "标注图像中的关键点位置",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Keypoint+Labeling",
        icon: <MousePointer className="w-4 h-4" />,
    },
    {
        id: "cv-5",
        name: "图像分类",
        category: "Computer Vision",
        description: "为整个图像分配类别标签",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Image+Classification",
        icon: <ImageIcon className="w-4 h-4" />,
    },
    {
        id: "cv-6",
        name: "实例分割",
        category: "Computer Vision",
        description: "区分同类别的不同实例对象",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Instance+Segmentation",
        icon: <Target className="w-4 h-4" />,
    },
    {
        id: "cv-7",
        name: "全景分割",
        category: "Computer Vision",
        description: "结合语义分割和实例分割的全景标注",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Panoptic+Segmentation",
        icon: <Grid className="w-4 h-4" />,
    },
    {
        id: "cv-8",
        name: "3D目标检测",
        category: "Computer Vision",
        description: "在3D空间中标注目标对象的位置和方向",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=3D+Object+Detection",
        icon: <Maximize className="w-4 h-4" />,
    },
    {
        id: "cv-9",
        name: "图像配对",
        category: "Computer Vision",
        description: "标注图像之间的对应关系",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Image+Matching",
        icon: <Move className="w-4 h-4" />,
    },
    {
        id: "cv-10",
        name: "图像质量评估",
        category: "Computer Vision",
        description: "评估和标注图像质量等级",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Quality+Assessment",
        icon: <BarChart className="w-4 h-4" />,
    },
    {
        id: "cv-11",
        name: "图像裁剪标注",
        category: "Computer Vision",
        description: "标注图像中需要裁剪的区域",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Image+Cropping",
        icon: <Crop className="w-4 h-4" />,
    },
    {
        id: "cv-12",
        name: "图像旋转标注",
        category: "Computer Vision",
        description: "标注图像的正确方向角度",
        type: "image",
        preview: "/placeholder.svg?height=120&width=180&text=Image+Rotation",
        icon: <RotateCcw className="w-4 h-4" />,
    },
    // 自然语言处理模板
    {
        id: "nlp-1",
        name: "文本分类",
        category: "Natural Language Processing",
        description: "为文本分配类别标签",
        type: "text",
        icon: <FileText className="w-4 h-4" />,
    },
    {
        id: "nlp-2",
        name: "命名实体识别",
        category: "Natural Language Processing",
        description: "识别和标注文本中的实体",
        type: "text",
        icon: <Tag className="w-4 h-4" />,
    },
    {
        id: "nlp-3",
        name: "情感分析",
        category: "Natural Language Processing",
        description: "标注文本的情感倾向",
        type: "text",
        icon: <Heart className="w-4 h-4" />,
    },
    {
        id: "nlp-4",
        name: "问答标注",
        category: "Natural Language Processing",
        description: "标注问题和答案对",
        type: "text",
        icon: <HelpCircle className="w-4 h-4" />,
    },
    {
        id: "nlp-5",
        name: "文本摘要",
        category: "Natural Language Processing",
        description: "为长文本创建摘要标注",
        type: "text",
        icon: <BookOpen className="w-4 h-4" />,
    },
    {
        id: "nlp-6",
        name: "对话标注",
        category: "Natural Language Processing",
        description: "标注对话中的意图和实体",
        type: "text",
        icon: <MessageSquare className="w-4 h-4" />,
    },
    {
        id: "nlp-7",
        name: "关系抽取",
        category: "Natural Language Processing",
        description: "标注实体之间的关系",
        type: "text",
        icon: <Users className="w-4 h-4" />,
    },
    {
        id: "nlp-8",
        name: "文本相似度",
        category: "Natural Language Processing",
        description: "标注文本之间的相似度",
        type: "text",
        icon: <Zap className="w-4 h-4" />,
    },
    {
        id: "nlp-9",
        name: "语言检测",
        category: "Natural Language Processing",
        description: "识别和标注文本的语言类型",
        type: "text",
        icon: <Globe className="w-4 h-4" />,
    },
    {
        id: "nlp-10",
        name: "文本纠错",
        category: "Natural Language Processing",
        description: "标注文本中的错误并提供修正",
        type: "text",
        icon: <Scissors className="w-4 h-4" />,
    },
]