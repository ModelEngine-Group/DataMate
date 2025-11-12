import React from "react";
import { Modal, Descriptions, Tag, Space, Divider, Card, Typography } from "antd";
import type { AnnotationTemplate } from "../annotation.model";

const { Text, Paragraph } = Typography;

interface TemplateDetailProps {
    visible: boolean;
    template?: AnnotationTemplate;
    onClose: () => void;
}

const TemplateDetail: React.FC<TemplateDetailProps> = ({
    visible,
    template,
    onClose,
}) => {
    if (!template) return null;

    return (
        <Modal
            title="Template Details"
            open={visible}
            onCancel={onClose}
            footer={null}
            width={800}
        >
            <Descriptions bordered column={2}>
                <Descriptions.Item label="Name" span={2}>
                    {template.name}
                </Descriptions.Item>
                <Descriptions.Item label="Description" span={2}>
                    {template.description || "-"}
                </Descriptions.Item>
                <Descriptions.Item label="Data Type">
                    <Tag color="cyan">{template.dataType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Labeling Type">
                    <Tag color="geekblue">{template.labelingType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Category">
                    <Tag color="blue">{template.category}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Style">
                    {template.style}
                </Descriptions.Item>
                <Descriptions.Item label="Type">
                    <Tag color={template.builtIn ? "gold" : "default"}>
                        {template.builtIn ? "Built-in" : "Custom"}
                    </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Version">
                    {template.version}
                </Descriptions.Item>
                <Descriptions.Item label="Created At" span={2}>
                    {new Date(template.createdAt).toLocaleString()}
                </Descriptions.Item>
                {template.updatedAt && (
                    <Descriptions.Item label="Updated At" span={2}>
                        {new Date(template.updatedAt).toLocaleString()}
                    </Descriptions.Item>
                )}
            </Descriptions>

            <Divider>Configuration</Divider>

            <Card title="Data Objects" size="small" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: "100%" }}>
                    {template.configuration.objects.map((obj, index) => (
                        <Card key={index} size="small" type="inner">
                            <Space>
                                <Text strong>Name:</Text>
                                <Tag>{obj.name}</Tag>
                                <Text strong>Type:</Text>
                                <Tag color="blue">{obj.type}</Tag>
                                <Text strong>Value:</Text>
                                <Tag color="green">{obj.value}</Tag>
                            </Space>
                        </Card>
                    ))}
                </Space>
            </Card>

            <Card title="Label Controls" size="small" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                    {template.configuration.labels.map((label, index) => (
                        <Card key={index} size="small" type="inner" title={`Control ${index + 1}`}>
                            <Space direction="vertical" style={{ width: "100%" }}>
                                <div>
                                    <Text strong>From Name: </Text>
                                    <Tag>{label.fromName}</Tag>
                                    <Text strong style={{ marginLeft: 16 }}>To Name: </Text>
                                    <Tag>{label.toName}</Tag>
                                    <Text strong style={{ marginLeft: 16 }}>Type: </Text>
                                    <Tag color="purple">{label.type}</Tag>
                                    {label.required && <Tag color="red">Required</Tag>}
                                </div>

                                {label.description && (
                                    <div>
                                        <Text strong>Description: </Text>
                                        <Text type="secondary">{label.description}</Text>
                                    </div>
                                )}

                                {label.options && label.options.length > 0 && (
                                    <div>
                                        <Text strong>Options: </Text>
                                        <div style={{ marginTop: 4 }}>
                                            {label.options.map((opt, i) => (
                                                <Tag key={i} color="cyan">{opt}</Tag>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {label.labels && label.labels.length > 0 && (
                                    <div>
                                        <Text strong>Labels: </Text>
                                        <div style={{ marginTop: 4 }}>
                                            {label.labels.map((lbl, i) => (
                                                <Tag key={i} color="geekblue">{lbl}</Tag>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </Space>
                        </Card>
                    ))}
                </Space>
            </Card>

            {template.labelConfig && (
                <Card title="Label Studio XML Configuration" size="small">
                    <Paragraph>
                        <pre style={{
                            background: "#f5f5f5",
                            padding: 12,
                            borderRadius: 4,
                            overflow: "auto",
                            maxHeight: 300
                        }}>
                            {template.labelConfig}
                        </pre>
                    </Paragraph>
                </Card>
            )}
        </Modal>
    );
};

export default TemplateDetail;
