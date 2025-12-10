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
            title="模板详情"
            open={visible}
            onCancel={onClose}
            footer={null}
            width={800}
        >
            <Descriptions bordered column={2}>
                <Descriptions.Item label="名称" span={2}>
                    {template.name}
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                    {template.description || "-"}
                </Descriptions.Item>
                <Descriptions.Item label="数据类型">
                    <Tag color="cyan">{template.dataType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="标注类型">
                    <Tag color="geekblue">{template.labelingType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="分类">
                    <Tag color="blue">{template.category}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="样式">
                    {template.style}
                </Descriptions.Item>
                <Descriptions.Item label="类型">
                    <Tag color={template.builtIn ? "gold" : "default"}>
                        {template.builtIn ? "系统内置" : "自定义"}
                    </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="版本">
                    {template.version}
                </Descriptions.Item>
                <Descriptions.Item label="创建时间" span={2}>
                    {new Date(template.createdAt).toLocaleString()}
                </Descriptions.Item>
                {template.updatedAt && (
                    <Descriptions.Item label="更新时间" span={2}>
                        {new Date(template.updatedAt).toLocaleString()}
                    </Descriptions.Item>
                )}
            </Descriptions>

            <Divider>配置详情</Divider>

            <Card title="数据对象" size="small" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: "100%" }}>
                    {template.configuration.objects.map((obj, index) => (
                        <Card key={index} size="small" type="inner">
                            <Space>
                                <Text strong>名称：</Text>
                                <Tag>{obj.name}</Tag>
                                <Text strong>类型：</Text>
                                <Tag color="blue">{obj.type}</Tag>
                                <Text strong>值：</Text>
                                <Tag color="green">{obj.value}</Tag>
                            </Space>
                        </Card>
                    ))}
                </Space>
            </Card>

            <Card title="标注控件" size="small" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: "100%" }} size="middle">
                    {template.configuration.labels.map((label, index) => (
                        <Card key={index} size="small" type="inner" title={`控件 ${index + 1}`}>
                            <Space direction="vertical" style={{ width: "100%" }}>
                                <div>
                                    <Text strong>来源名称：</Text>
                                    <Tag>{label.fromName}</Tag>

                                    <Text strong style={{ marginLeft: 16 }}>目标名称：</Text>
                                    <Tag>{label.toName}</Tag>

                                    <Text strong style={{ marginLeft: 16 }}>类型：</Text>
                                    <Tag color="purple">{label.type}</Tag>

                                    {label.required && <Tag color="red">必填</Tag>}
                                </div>

                                {label.description && (
                                    <div>
                                        <Text strong>描述：</Text>
                                        <Text type="secondary">{label.description}</Text>
                                    </div>
                                )}

                                {label.options && label.options.length > 0 && (
                                    <div>
                                        <Text strong>选项：</Text>
                                        <div style={{ marginTop: 4 }}>
                                            {label.options.map((opt, i) => (
                                                <Tag key={i} color="cyan">{opt}</Tag>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {label.labels && label.labels.length > 0 && (
                                    <div>
                                        <Text strong>标签：</Text>
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
                <Card title="Label Studio XML 配置" size="small">
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
