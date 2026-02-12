import React, { useState, useEffect } from "react";
import { Select, Tooltip, Spin, Collapse, Tag, Space } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { getTagConfigUsingGet } from "../../annotation.api";
import type {
    LabelStudioTagConfig,
    TagOption,
} from "../../annotation.tagconfig";
import {
    parseTagConfig,
    getControlDisplayName,
    getObjectDisplayName,
    getControlGroups,
} from "../../annotation.tagconfig";

const { Option, OptGroup } = Select;

interface TagSelectorProps {
    value?: string;
    onChange?: (value: string) => void;
    type: "object" | "control";
    placeholder?: string;
    style?: React.CSSProperties;
    disabled?: boolean;
}

/**
 * Tag Selector Component
 * Dynamically fetches and displays available Label Studio tags from backend config
 */
const TagSelector: React.FC<TagSelectorProps> = ({
    value,
    onChange,
    type,
    placeholder,
    style,
    disabled,
}) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [tagOptions, setTagOptions] = useState<TagOption[]>([]);

    useEffect(() => {
        fetchTagConfig();
    }, []);

    const fetchTagConfig = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getTagConfigUsingGet();
            if (response.data) {
                const config: LabelStudioTagConfig = response.data;
                const { objectOptions, controlOptions } = parseTagConfig(config);

                if (type === "object") {
                    setTagOptions(objectOptions);
                } else {
                    setTagOptions(controlOptions);
                }
            } else {
                setError(response.message || "获取标签配置失败");
            }
        } catch (err: any) {
            console.error("Failed to fetch tag config:", err);
            setError("加载标签配置时出错");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Select
                placeholder="加载中..."
                style={style}
                disabled
                suffixIcon={<Spin size="small" />}
            />
        );
    }

    if (error) {
        return (
            <Tooltip title={error}>
                <Select
                    placeholder="加载失败，点击重试"
                    style={style}
                    disabled={disabled}
                    status="error"
                    onClick={() => fetchTagConfig()}
                />
            </Tooltip>
        );
    }

    // Group controls by usage pattern
    if (type === "control") {
        const groups = getControlGroups();
        const groupedOptions: Record<string, TagOption[]> = {};
        const ungroupedOptions: TagOption[] = [];

        // Group the controls
        Object.entries(groups).forEach(([groupKey, groupConfig]) => {
            groupedOptions[groupKey] = tagOptions.filter((opt) =>
                groupConfig.controls.includes(opt.value)
            );
        });

        // Find ungrouped controls
        const allGroupedControls = new Set(
            Object.values(groups).flatMap((g) => g.controls)
        );
        tagOptions.forEach((opt) => {
            if (!allGroupedControls.has(opt.value)) {
                ungroupedOptions.push(opt);
            }
        });

        return (
            <Select
                value={value}
                onChange={onChange}
                placeholder={placeholder || "选择控件类型"}
                style={style}
                disabled={disabled}
                showSearch
                optionFilterProp="label"
            >
                {Object.entries(groups).map(([groupKey, groupConfig]) => {
                    const options = groupedOptions[groupKey];
                    if (options.length === 0) return null;

                    return (
                        <OptGroup key={groupKey} label={groupConfig.label}>
                            {options.map((opt) => (
                                <Option key={opt.value} value={opt.value} label={opt.label}>
                                    <div className="flex items-center justify-between">
                                        <span>{getControlDisplayName(opt.value)}</span>
                                        <Tooltip title={opt.description}>
                                            <InfoCircleOutlined
                                                style={{ color: "#8c8c8c", fontSize: 12 }}
                                            />
                                        </Tooltip>
                                    </div>
                                </Option>
                            ))}
                        </OptGroup>
                    );
                })}
                {ungroupedOptions.length > 0 && (
                    <OptGroup label="其他">
                        {ungroupedOptions.map((opt) => (
                            <Option key={opt.value} value={opt.value} label={opt.label}>
                                <div className="flex items-center justify-between">
                                    <span>{getControlDisplayName(opt.value)}</span>
                                    <Tooltip title={opt.description}>
                                        <InfoCircleOutlined
                                            style={{ color: "#8c8c8c", fontSize: 12 }}
                                        />
                                    </Tooltip>
                                </div>
                            </Option>
                        ))}
                    </OptGroup>
                )}
            </Select>
        );
    }

    // Objects selector (no grouping)
    return (
        <Select
            value={value}
            onChange={onChange}
            placeholder={placeholder || "选择数据对象类型"}
            style={style}
            disabled={disabled}
            showSearch
            optionFilterProp="label"
        >
            {tagOptions.map((opt) => (
                <Option key={opt.value} value={opt.value} label={opt.label}>
                    <div className="flex items-center justify-between">
                        <span>{getObjectDisplayName(opt.value)}</span>
                        <Tooltip title={opt.description}>
                            <InfoCircleOutlined style={{ color: "#8c8c8c", fontSize: 12 }} />
                        </Tooltip>
                    </div>
                </Option>
            ))}
        </Select>
    );
};

export default TagSelector;

/**
 * Tag Info Panel Component
 * Displays detailed information about a selected tag
 */
interface TagInfoPanelProps {
    tagConfig: LabelStudioTagConfig | null;
    tagType: string;
    category: "object" | "control";
}

export const TagInfoPanel: React.FC<TagInfoPanelProps> = ({
    tagConfig,
    tagType,
    category,
}) => {
    if (!tagConfig || !tagType) {
        return null;
    }

    const config =
        category === "object"
            ? tagConfig.objects[tagType]
            : tagConfig.controls[tagType];

    if (!config) {
        return null;
    }

    return (
        <Collapse
            size="small"
            items={[
                {
                    key: "1",
                    label: "标签配置详情",
                    children: (
                        <Space direction="vertical" size="small" style={{ width: "100%" }}>
                            <div>
                                <strong>描述：</strong>
                                {config.description}
                            </div>

                            <div>
                                <strong>必需属性：</strong>
                                <div style={{ marginTop: 4 }}>
                                    {config.required_attrs.map((attr: string) => (
                                        <Tag key={attr} color="red">
                                            {attr}
                                        </Tag>
                                    ))}
                                </div>
                            </div>

                            {config.optional_attrs &&
                                Object.keys(config.optional_attrs).length > 0 && (
                                    <div>
                                        <strong>可选属性：</strong>
                                        <div style={{ marginTop: 4 }}>
                                            {Object.entries(config.optional_attrs).map(
                                                ([attrName, attrConfig]: [string, any]) => (
                                                    <Tooltip
                                                        key={attrName}
                                                        title={
                                                            <div>
                                                                {attrConfig.description && (
                                                                    <div>{attrConfig.description}</div>
                                                                )}
                                                                {attrConfig.type && (
                                                                    <div>类型: {attrConfig.type}</div>
                                                                )}
                                                                {attrConfig.default !== undefined && (
                                                                    <div>默认值: {String(attrConfig.default)}</div>
                                                                )}
                                                                {attrConfig.values && (
                                                                    <div>
                                                                        可选值: {attrConfig.values.join(", ")}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        }
                                                    >
                                                        <Tag color="blue" style={{ cursor: "help" }}>
                                                            {attrName}
                                                        </Tag>
                                                    </Tooltip>
                                                )
                                            )}
                                        </div>
                                    </div>
                                )}

                            {config.requires_children && (
                                <div>
                                    <strong>子元素：</strong>
                                    <Tag color="green">需要 &lt;{config.child_tag}&gt;</Tag>
                                </div>
                            )}
                        </Space>
                    ),
                },
            ]}
        />
    );
};
