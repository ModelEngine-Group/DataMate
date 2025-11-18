/**
 * Label Studio Tag Configuration Types
 * Corresponds to runtime/datamate-python/app/module/annotation/config/label_studio_tags.yaml
 */

export interface TagAttributeConfig {
    type?: "boolean" | "number" | "string";
    values?: string[];
    default?: any;
    description?: string;
}

export interface TagConfig {
    description: string;
    required_attrs: string[];
    optional_attrs?: Record<string, TagAttributeConfig>;
    requires_children?: boolean;
    child_tag?: string;
    child_required_attrs?: string[];
    category?: string; // e.g., "labeling" or "layout" for controls; "image", "text", etc. for objects
}

export interface LabelStudioTagConfig {
    objects: Record<string, TagConfig>;
    controls: Record<string, TagConfig>;
}

/**
 * UI-friendly representation of a tag for selection
 */
export interface TagOption {
    value: string;
    label: string;
    description: string;
    category: "object" | "control";
    requiresChildren: boolean;
    childTag?: string;
    requiredAttrs: string[];
    optionalAttrs?: Record<string, TagAttributeConfig>;
}

/**
 * Convert backend tag config to frontend tag options
 * @param config - The full tag configuration from backend
 * @param includeLabelingOnly - If true, only include controls with category="labeling" (default: true)
 */
export function parseTagConfig(
    config: LabelStudioTagConfig,
    includeLabelingOnly: boolean = true
): {
    objectOptions: TagOption[];
    controlOptions: TagOption[];
} {
    const objectOptions: TagOption[] = Object.entries(config.objects).map(
        ([key, value]) => ({
            value: key,
            label: key,
            description: value.description,
            category: "object" as const,
            requiresChildren: value.requires_children || false,
            childTag: value.child_tag,
            requiredAttrs: value.required_attrs,
            optionalAttrs: value.optional_attrs,
        })
    );

    const controlOptions: TagOption[] = Object.entries(config.controls)
        .filter(([_, value]) => {
            // If includeLabelingOnly is true, filter out layout controls
            if (includeLabelingOnly) {
                return value.category === "labeling";
            }
            return true;
        })
        .map(([key, value]) => ({
            value: key,
            label: key,
            description: value.description,
            category: "control" as const,
            requiresChildren: value.requires_children || false,
            childTag: value.child_tag,
            requiredAttrs: value.required_attrs,
            optionalAttrs: value.optional_attrs,
        }));

    return { objectOptions, controlOptions };
}

/**
 * Get user-friendly display name for control types
 */
export function getControlDisplayName(controlType: string): string {
    const displayNames: Record<string, string> = {
        Choices: "选项 (单选/多选)",
        RectangleLabels: "矩形框",
        PolygonLabels: "多边形",
        Labels: "标签",
        TextArea: "文本区域",
        Rating: "评分",
        Taxonomy: "分类树",
        Ranker: "排序",
        List: "列表",
        BrushLabels: "画笔分割",
        EllipseLabels: "椭圆",
        KeyPointLabels: "关键点",
        Rectangle: "矩形",
        Polygon: "多边形",
        Ellipse: "椭圆",
        KeyPoint: "关键点",
        Brush: "画笔",
        Number: "数字输入",
        DateTime: "日期时间",
        Relation: "关系",
        Relations: "关系组",
        Pairwise: "成对比较",
    };

    return displayNames[controlType] || controlType;
}

/**
 * Get user-friendly display name for object types
 */
export function getObjectDisplayName(objectType: string): string {
    const displayNames: Record<string, string> = {
        Image: "图像",
        Text: "文本",
        Audio: "音频",
        Video: "视频",
        HyperText: "HTML内容",
        PDF: "PDF文档",
        Markdown: "Markdown内容",
        Paragraphs: "段落",
        Table: "表格",
        AudioPlus: "高级音频",
        Timeseries: "时间序列",
        Vector: "向量数据",
        Chat: "对话数据",
    };

    return displayNames[objectType] || objectType;
}

/**
 * Group control types by common usage patterns
 */
export function getControlGroups(): Record<
    string,
    { label: string; controls: string[] }
> {
    return {
        classification: {
            label: "分类标注",
            controls: ["Choices", "Taxonomy", "Labels", "Rating"],
        },
        detection: {
            label: "目标检测",
            controls: [
                "RectangleLabels",
                "PolygonLabels",
                "EllipseLabels",
                "KeyPointLabels",
                "Rectangle",
                "Polygon",
                "Ellipse",
                "KeyPoint",
            ],
        },
        segmentation: {
            label: "分割标注",
            controls: ["BrushLabels", "Brush", "BitmaskLabels", "MagicWand"],
        },
        text: {
            label: "文本输入",
            controls: ["TextArea", "Number", "DateTime"],
        },
        other: {
            label: "其他",
            controls: [
                "TimeseriesLabels",
                "VectorLabels",
                "ParagraphLabels",
                "VideoRectangle",
            ],
        },
    };
}
