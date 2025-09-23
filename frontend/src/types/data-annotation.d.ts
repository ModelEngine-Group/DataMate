export interface AnnotationTask {
    id: string
    name: string
    type: "图像分类" | "文本分类" | "目标检测" | "NER" | "语音识别" | "视频分析"
    datasetType: "text" | "image" | "video" | "audio"
    totalCount: number
    completedCount: number
    skippedCount: number
    progress: number
}