export interface RatioTask {
    id: number
    name: string
    status: "pending" | "running" | "completed" | "failed" | "paused"
    progress: number
    sourceDatasets: string[]
    targetCount: number
    generatedCount: number
    createdAt: string
    ratioType: "dataset" | "label"
    estimatedTime?: string
    quality?: number
    errorMessage?: string
    ratioConfigs: RatioConfig[]
}

export interface RatioConfig {
    id: string
    name: string
    type: "dataset" | "label"
    quantity: number
    percentage: number
    source: string
}