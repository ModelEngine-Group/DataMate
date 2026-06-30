import React, { useState } from "react";
import {
    Card,
    Button,
    Space,
    Row,
    Col,
    Drawer,
    Typography,
    message,
} from "antd";
import {
    PlusOutlined,
    EyeOutlined,
    CodeOutlined,
    AppstoreOutlined,
} from "@ant-design/icons";
import { TagBrowser } from "./components";

const { Paragraph } = Typography;

interface VisualTemplateBuilderProps {
    onSave?: (templateCode: string) => void;
}

/**
 * Visual Template Builder
 * Provides a drag-and-drop interface for building Label Studio templates
 */
const VisualTemplateBuilder: React.FC<VisualTemplateBuilderProps> = ({
    onSave,
}) => {
    const [drawerVisible, setDrawerVisible] = useState(false);
    const [previewVisible, setPreviewVisible] = useState(false);
    const [selectedTags, setSelectedTags] = useState<
        Array<{ name: string; category: "object" | "control" }>
    >([]);

    const handleTagSelect = (tagName: string, category: "object" | "control") => {
        message.info(`选择了 ${category === "object" ? "对象" : "控件"}: ${tagName}`);
        setSelectedTags([...selectedTags, { name: tagName, category }]);
        setDrawerVisible(false);
    };

    const handleSave = () => {
        // TODO: Generate template XML from selectedTags
        message.success("模板保存成功");
        onSave?.("<View><!-- Generated template --></View>");
    };

    return (
        <div style={{ padding: "24px" }}>
            <Row gutter={16}>
                <Col span={24}>
                    <Card
                        title="可视化模板构建器"
                        extra={
                            <Space>
                                <Button
                                    icon={<AppstoreOutlined />}
                                    onClick={() => setDrawerVisible(true)}
                                >
                                    浏览标签
                                </Button>
                                <Button
                                    icon={<CodeOutlined />}
                                    onClick={() => setPreviewVisible(true)}
                                >
                                    查看代码
                                </Button>
                                <Button
                                    type="primary"
                                    icon={<EyeOutlined />}
                                    onClick={handleSave}
                                >
                                    保存模板
                                </Button>
                            </Space>
                        }
                    >
                        <div
                            style={{
                                minHeight: "400px",
                                border: "2px dashed #d9d9d9",
                                borderRadius: "8px",
                                padding: "24px",
                                textAlign: "center",
                            }}
                        >
                            {selectedTags.length === 0 ? (
                                <div>
                                    <Paragraph type="secondary">
                                        点击"浏览标签"开始构建您的标注模板
                                    </Paragraph>
                                    <Button
                                        type="dashed"
                                        icon={<PlusOutlined />}
                                        onClick={() => setDrawerVisible(true)}
                                    >
                                        添加标签
                                    </Button>
                                </div>
                            ) : (
                                <Space direction="vertical" size="large">
                                    {selectedTags.map((tag, index) => (
                                        <Card key={index} size="small">
                                            <div>
                                                {tag.category === "object" ? "对象" : "控件"}: {tag.name}
                                            </div>
                                        </Card>
                                    ))}
                                </Space>
                            )}
                        </div>
                    </Card>
                </Col>
            </Row>

            <Drawer
                title="标签浏览器"
                placement="right"
                width={800}
                open={drawerVisible}
                onClose={() => setDrawerVisible(false)}
            >
                <TagBrowser onTagSelect={handleTagSelect} />
            </Drawer>

            <Drawer
                title="模板代码预览"
                placement="right"
                width={600}
                open={previewVisible}
                onClose={() => setPreviewVisible(false)}
            >
                <pre
                    style={{
                        background: "#f5f5f5",
                        padding: "16px",
                        borderRadius: "4px",
                        overflow: "auto",
                    }}
                >
                    <code>
                        {`<View>
  <!-- 根据选择的标签生成的模板代码 -->
  ${selectedTags
                                .map(
                                    (tag) =>
                                        `<${tag.name}${tag.category === "object" ? ' name="obj" value="$data"' : ' name="ctrl" toName="obj"'} />`
                                )
                                .join("\n  ")}
</View>`}
                    </code>
                </pre>
            </Drawer>
        </div>
    );
};

export default VisualTemplateBuilder;
