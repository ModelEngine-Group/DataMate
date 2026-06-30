import React from "react";
import { Card, Tabs, List, Tag, Typography, Space, Empty, Spin } from "antd";
import {
    AppstoreOutlined,
    ControlOutlined,
    InfoCircleOutlined,
} from "@ant-design/icons";
import { useTagConfig } from "../../../../hooks/useTagConfig";
import {
    getControlDisplayName,
    getObjectDisplayName,
    getControlGroups,
} from "../../annotation.tagconfig";
import type { TagOption } from "../../annotation.tagconfig";

const { Title, Paragraph, Text } = Typography;

interface TagBrowserProps {
    onTagSelect?: (tagName: string, category: "object" | "control") => void;
}

/**
 * Tag Browser Component
 * Displays all available Label Studio tags in a browsable interface
 */
const TagBrowser: React.FC<TagBrowserProps> = ({ onTagSelect }) => {
    const { config, objectOptions, controlOptions, loading, error } =
        useTagConfig();

    if (loading) {
        return (
            <Card>
                <div style={{ textAlign: "center", padding: "40px" }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>加载标签配置...</div>
                </div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card>
                <Empty
                    description={
                        <div>
                            <div>{error}</div>
                            <Text type="secondary">无法加载标签配置</Text>
                        </div>
                    }
                />
            </Card>
        );
    }

    const renderObjectList = () => (
        <List
            grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 3, xxl: 4 }}
            dataSource={objectOptions}
            renderItem={(item: TagOption) => {
                const objConfig = config?.objects[item.value];
                return (
                    <List.Item>
                        <Card
                            hoverable
                            size="small"
                            onClick={() => onTagSelect?.(item.value, "object")}
                            style={{ height: "100%" }}
                        >
                            <Space direction="vertical" size="small" style={{ width: "100%" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <Text strong>{getObjectDisplayName(item.value)}</Text>
                                    <Tag color="blue">&lt;{item.value}&gt;</Tag>
                                </div>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    {item.description}
                                </Text>
                                {objConfig && (
                                    <div style={{ marginTop: 8 }}>
                                        <Text style={{ fontSize: 11, color: "#8c8c8c" }}>
                                            必需属性:{" "}
                                            {objConfig.required_attrs.join(", ") || "无"}
                                        </Text>
                                    </div>
                                )}
                            </Space>
                        </Card>
                    </List.Item>
                );
            }}
        />
    );

    const renderControlsByGroup = () => {
        const groups = getControlGroups();

        return (
            <Tabs
                defaultActiveKey="classification"
                items={Object.entries(groups).map(([groupKey, groupConfig]) => {
                    const groupControls = controlOptions.filter((opt: TagOption) =>
                        groupConfig.controls.includes(opt.value)
                    );

                    return {
                        key: groupKey,
                        label: groupConfig.label,
                        children: (
                            <List
                                grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 3, xxl: 4 }}
                                dataSource={groupControls}
                                locale={{ emptyText: "此分组暂无控件" }}
                                renderItem={(item: TagOption) => {
                                    const ctrlConfig = config?.controls[item.value];
                                    return (
                                        <List.Item>
                                            <Card
                                                hoverable
                                                size="small"
                                                onClick={() => onTagSelect?.(item.value, "control")}
                                                style={{ height: "100%" }}
                                            >
                                                <Space direction="vertical" size="small" style={{ width: "100%" }}>
                                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                                        <Text strong>
                                                            {getControlDisplayName(item.value)}
                                                        </Text>
                                                        <Tag color="green">&lt;{item.value}&gt;</Tag>
                                                    </div>
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        {item.description}
                                                    </Text>
                                                    {ctrlConfig && (
                                                        <Space
                                                            size={4}
                                                            wrap
                                                            style={{ marginTop: 8 }}
                                                        >
                                                            {ctrlConfig.requires_children && (
                                                                <Tag
                                                                    color="orange"
                                                                    style={{ fontSize: 10, margin: 0 }}
                                                                >
                                                                    需要 &lt;{ctrlConfig.child_tag}&gt;
                                                                </Tag>
                                                            )}
                                                            {ctrlConfig.required_attrs.includes("toName") && (
                                                                <Tag
                                                                    color="purple"
                                                                    style={{ fontSize: 10, margin: 0 }}
                                                                >
                                                                    绑定对象
                                                                </Tag>
                                                            )}
                                                        </Space>
                                                    )}
                                                </Space>
                                            </Card>
                                        </List.Item>
                                    );
                                }}
                            />
                        ),
                    };
                })}
            />
        );
    };

    return (
        <Card>
            <Tabs
                defaultActiveKey="controls"
                items={[
                    {
                        key: "controls",
                        label: (
                            <span>
                                <ControlOutlined />
                                控件标签 ({controlOptions.length})
                            </span>
                        ),
                        children: renderControlsByGroup(),
                    },
                    {
                        key: "objects",
                        label: (
                            <span>
                                <AppstoreOutlined />
                                数据对象 ({objectOptions.length})
                            </span>
                        ),
                        children: renderObjectList(),
                    },
                    {
                        key: "help",
                        label: (
                            <span>
                                <InfoCircleOutlined />
                                使用说明
                            </span>
                        ),
                        children: (
                            <div style={{ padding: "16px" }}>
                                <Title level={4}>Label Studio 标签配置说明</Title>
                                <Paragraph>
                                    标注模板由两类标签组成：
                                </Paragraph>
                                <ul>
                                    <li>
                                        <Text strong>数据对象标签</Text>：定义要标注的数据类型（如图像、文本、音频等）
                                    </li>
                                    <li>
                                        <Text strong>控件标签</Text>：定义标注工具和交互方式（如矩形框、分类选项、文本输入等）
                                    </li>
                                </ul>
                                <Title level={5} style={{ marginTop: 24 }}>
                                    基本结构
                                </Title>
                                <Paragraph>
                                    <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 4 }}>
                                        {`<View>
  <!-- 数据对象 -->
  <Image name="image" value="$image" />
  
  <!-- 控件 -->
  <RectangleLabels name="label" toName="image">
    <Label value="人物" />
    <Label value="车辆" />
  </RectangleLabels>
</View>`}
                                    </pre>
                                </Paragraph>
                                <Title level={5} style={{ marginTop: 24 }}>
                                    属性说明
                                </Title>
                                <ul>
                                    <li>
                                        <Text code>name</Text>：控件的唯一标识符
                                    </li>
                                    <li>
                                        <Text code>toName</Text>：指向要标注的数据对象的 name
                                    </li>
                                    <li>
                                        <Text code>value</Text>：数据源字段，以 $ 开头（如 $image, $text）
                                    </li>
                                    <li>
                                        <Text code>required</Text>：是否必填（可选）
                                    </li>
                                </ul>
                            </div>
                        ),
                    },
                ]}
            />
        </Card>
    );
};

export default TagBrowser;
