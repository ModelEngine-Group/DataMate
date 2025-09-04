 export enum DatasetType {
    PRETRAIN = 'PRETRAIN',
    FINE_TUNE = 'FINE_TUNE',
    EVAL = 'EVAL',

    PRETRAIN_TEXT = "PRETRAIN_TEXT",
    PRETRAIN_IMAGE = "PRETRAIN_IMAGE",
    PRETRAIN_AUDIO = "PRETRAIN_AUDIO",
    PRETRAIN_VIDEO = "PRETRAIN_VIDEO",

    FINE_TUNE_ALPACA = "FINE_TUNE_ALPACA",
    FINE_TUNE_CHATGLM = "FINE_TUNE_CHATGLM",
    FINE_TUNE_BLOOMZ = "FINE_TUNE_BLOOMZ",
    FINE_TUNE_LLAMA = "FINE_TUNE_LLAMA",

    EVAL_GSM8K = "EVAL_GSM8K",
    EVAL_SQUAD = "EVAL_SQUAD",
    EVAL_MNLI = "EVAL_MNLI",
    EVAL_IMDB = "EVAL_IMDB",
    EVAL_SINGLE_CHOICE_QA = "EVAL_SINGLE_CHOICE_QA",
}

export enum DatasetStatus {
    DRAFT = "DRAFT",
    PROCESSING = "PROCESSING",
    ARCHIVED = "ARCHIVED",
    PUBLISHED = "PUBLISHED",
}

export interface DatasetFile {
    id: number
    name: string
    size: string
    uploadDate: string
    path: string
}

export interface Dataset {
    id: number
    name: string
    description: string
    parentId?: number
    type: DatasetType
    status: DatasetStatus
    size?: string
    itemCount?: number
    createdBy: string
    createdTime: string
    updatedBy: string
    updatedTime: string
    lastModified: string
    tags: string[]
    quality: number
    isFavorited?: boolean
    files?: DatasetFile[]
    annotations?: {
        total: number
        completed: number
        accuracy: number
    }
    lineage?: {
        source: string
        processing: string[]
        training?: {
            model: string
            accuracy: number
            f1Score: number
        }
    }
}

export interface ScheduleConfig {
    type: "immediate" | "scheduled"
    scheduleType?: "daily" | "weekly" | "monthly" | "custom"
    time?: string
    dayOfWeek?: string
    dayOfMonth?: string
    cronExpression?: string
    maxExecutions?: number
    executionCount?: number
}

export interface DatasetTask {
    id: number
    name: string
    description: string
    type: string
    status: "importing" | "waiting" | "completed" | "failed"
    progress: number
    createdAt: string
    importConfig: any
    scheduleConfig: ScheduleConfig
    nextExecution?: string
    lastExecution?: string
    executionHistory?: { time: string; status: string }[]
}
