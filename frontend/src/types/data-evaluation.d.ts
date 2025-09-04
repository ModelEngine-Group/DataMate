interface EvaluationDimension {
    id: string
    name: string
    description: string
    category: "quality" | "accuracy" | "completeness" | "consistency" | "bias" | "custom"
    isCustom?: boolean
    isEnabled?: boolean
}

interface EvaluationTask {
    id: string
    name: string
    datasetId: string
    datasetName: string
    evaluationType: "model" | "manual"
    status: "running" | "completed" | "failed" | "pending"
    score?: number
    progress?: number
    createdAt: string
    completedAt?: string
    description: string
    dimensions: string[]
    customDimensions: EvaluationDimension[]
    sliceConfig?: {
        threshold: number
        sampleCount: number
        method: string
    }
    modelConfig?: {
        url: string
        apiKey: string
        prompt: string
        temperature: number
        maxTokens: number
    }
    metrics: {
        accuracy: number
        completeness: number
        consistency: number
        relevance: number
    }
    issues: {
        type: string
        count: number
        severity: "high" | "medium" | "low"
    }[]
}

interface EvaluationSlice {
    id: string
    content: string
    sourceFile: string
    sliceIndex: number
    sliceType: string
    metadata: {
        startPosition?: number
        endPosition?: number
        pageNumber?: number
        section?: string
        processingMethod: string
    }
    scores?: { [dimensionId: string]: number }
    comment?: string
}

interface QAPair {
    id: string
    question: string
    answer: string
    sliceId: string
    score: number
    feedback?: string
}