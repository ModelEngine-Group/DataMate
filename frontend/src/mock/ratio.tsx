type RatioTask = {
    id: number;
    name: string;
    type: string;
    status: string;
    progress: number;
    sourceDatasets: string[];
    targetRatio: Record<string, number>;
    currentRatio: Record<string, number>;
    totalRecords: number;
    processedRecords: number;
    createdAt: string;
    estimatedTime?: string;
    errorMessage?: string;
    quality?: number;
    strategy: string;
    outputPath: string;
};

export const mockRatioTasks: RatioTask[] = [
    {
        id: 1,
        name: "多类别数据平衡任务",
        type: "balance",
        status: "completed",
        progress: 100,
        sourceDatasets: ["sentiment_dataset", "news_classification"],
        targetRatio: { 正面: 33, 负面: 33, 中性: 34 },
        currentRatio: { 正面: 33, 负面: 33, 中性: 34 },
        totalRecords: 15000,
        processedRecords: 15000,
        createdAt: "2025-01-20",
        estimatedTime: "已完成",
        quality: 95,
        strategy: "随机下采样",
        outputPath: "/data/balanced/sentiment_balanced_20250120",
    },
    {
        id: 2,
        name: "图像分类数据增强",
        type: "augment",
        status: "running",
        progress: 65,
        sourceDatasets: ["image_classification_v1"],
        targetRatio: { 猫: 25, 狗: 25, 鸟: 25, 鱼: 25 },
        currentRatio: { 猫: 35, 狗: 30, 鸟: 20, 鱼: 15 },
        totalRecords: 8000,
        processedRecords: 5200,
        createdAt: "2025-01-22",
        estimatedTime: "剩余 12 分钟",
        quality: 88,
        strategy: "SMOTE增强",
        outputPath: "/data/augmented/image_augmented_20250122",
    },
    {
        id: 3,
        name: "文本质量过滤任务",
        type: "filter",
        status: "failed",
        progress: 25,
        sourceDatasets: ["raw_text_corpus"],
        targetRatio: { 高质量: 60, 中等质量: 30, 低质量: 10 },
        currentRatio: { 高质量: 20, 中等质量: 35, 低质量: 45 },
        totalRecords: 50000,
        processedRecords: 12500,
        createdAt: "2025-01-23",
        errorMessage: "质量评估模型加载失败",
        strategy: "基于规则过滤",
        outputPath: "/data/filtered/text_filtered_20250123",
    },
    {
        id: 4,
        name: "多数据集合并配比",
        type: "merge",
        status: "pending",
        progress: 0,
        sourceDatasets: ["dataset_a", "dataset_b", "dataset_c"],
        targetRatio: { 数据集A: 40, 数据集B: 35, 数据集C: 25 },
        currentRatio: { 数据集A: 0, 数据集B: 0, 数据集C: 0 },
        totalRecords: 25000,
        processedRecords: 0,
        createdAt: "2025-01-24",
        estimatedTime: "等待开始",
        quality: 0,
        strategy: "按比例合并",
        outputPath: "/data/merged/combined_20250124",
    },
    {
        id: 5,
        name: "医疗数据类别平衡",
        type: "balance",
        status: "paused",
        progress: 45,
        sourceDatasets: ["medical_records"],
        targetRatio: { 正常: 50, 异常: 30, 疑似: 20 },
        currentRatio: { 正常: 65, 异常: 25, 疑似: 10 },
        totalRecords: 12000,
        processedRecords: 5400,
        createdAt: "2025-01-21",
        estimatedTime: "已暂停",
        quality: 92,
        strategy: "分层采样",
        outputPath: "/data/balanced/medical_balanced_20250121",
    },
]