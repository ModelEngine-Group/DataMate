import React, { useState, useEffect } from "react";
import {
    Modal,
    Form,
    Input,
    Select,
    Button,
    Space,
    message,
    Divider,
    Card,
    Checkbox,
} from "antd";
import { PlusOutlined, MinusCircleOutlined } from "@ant-design/icons";
import {
    createAnnotationTemplateUsingPost,
    updateAnnotationTemplateByIdUsingPut,
} from "../annotation.api";
import type { AnnotationTemplate } from "../annotation.model";
import TagSelector from "./components/TagSelector";

const { TextArea } = Input;
const { Option } = Select;

interface TemplateFormProps {
    visible: boolean;
    mode: "create" | "edit";
    template?: AnnotationTemplate;
    onSuccess: () => void;
    onCancel: () => void;
}

const TemplateForm: React.FC<TemplateFormProps> = ({
    visible,
    mode,
    template,
    onSuccess,
    onCancel,
}) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (visible && template && mode === "edit") {
            form.setFieldsValue({
                name: template.name,
                description: template.description,
                dataType: template.dataType,
                labelingType: template.labelingType,
                style: template.style,
                category: template.category,
                labels: template.configuration.labels,
                objects: template.configuration.objects,
            });
        } else if (visible && mode === "create") {
            form.resetFields();
            // Set default values
            form.setFieldsValue({
                style: "horizontal",
                category: "custom",
                labels: [],
                objects: [{ name: "image", type: "Image", value: "$image" }],
            });
        }
    }, [visible, template, mode, form]);

    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            setLoading(true);

            console.log("Form values:", values);

            const requestData = {
                name: values.name,
                description: values.description,
                dataType: values.dataType,
                labelingType: values.labelingType,
                style: values.style,
                category: values.category,
                configuration: {
                    labels: values.labels,
                    objects: values.objects,
                },
            };

            console.log("Request data:", requestData);

            let response;
            if (mode === "create") {
                response = await createAnnotationTemplateUsingPost(requestData);
            } else {
                response = await updateAnnotationTemplateByIdUsingPut(template!.id, requestData);
            }

            if (response.data) {
                message.success(`模板${mode === "create" ? "创建" : "更新"}成功`);
                form.resetFields();
                onSuccess();
            } else {
                message.error(response.message || `模板${mode === "create" ? "创建" : "更新"}失败`);
            }
        } catch (error: any) {
            if (error.errorFields) {
                message.error("请填写所有必填字段");
            } else {
                message.error(`模板${mode === "create" ? "创建" : "更新"}失败`);
                console.error(error);
            }
        } finally {
            setLoading(false);
        }
    };

    const needsOptions = (type: string) => {
        return ["Choices", "RectangleLabels", "PolygonLabels", "Labels"].includes(type);
    };

    return (
        <Modal
            title={mode === "create" ? "创建模板" : "编辑模板"}
            open={visible}
            onCancel={onCancel}
            onOk={handleSubmit}
            confirmLoading={loading}
            width={900}
            destroyOnClose
        >
            <Form
                form={form}
                layout="vertical"
                style={{ maxHeight: "70vh", overflowY: "auto", paddingRight: 8 }}
            >
                <Form.Item
                    label="模板名称"
                    name="name"
                    rules={[{ required: true, message: "请输入模板名称" }]}
                >
                    <Input placeholder="例如：产品质量分类" maxLength={100} />
                </Form.Item>

                <Form.Item label="描述" name="description">
                    <TextArea
                        placeholder="描述此模板的用途"
                        rows={2}
                        maxLength={500}
                    />
                </Form.Item>

                <Space style={{ width: "100%" }} size="large">
                    <Form.Item
                        label="数据类型"
                        name="dataType"
                        rules={[{ required: true, message: "请选择数据类型" }]}
                        style={{ width: 200 }}
                    >
                        <Select placeholder="选择数据类型">
                            <Option value="image">图像</Option>
                            <Option value="text">文本</Option>
                            <Option value="audio">音频</Option>
                            <Option value="video">视频</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        label="标注类型"
                        name="labelingType"
                        rules={[{ required: true, message: "请选择标注类型" }]}
                        style={{ width: 220 }}
                    >
                        <Select placeholder="选择标注类型">
                            <Option value="classification">分类</Option>
                            <Option value="object-detection">目标检测</Option>
                            <Option value="segmentation">分割</Option>
                            <Option value="ner">命名实体识别</Option>
                            <Option value="multi-stage">多阶段</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        label="样式"
                        name="style"
                        style={{ width: 150 }}
                    >
                        <Select>
                            <Option value="horizontal">水平</Option>
                            <Option value="vertical">垂直</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        label="分类"
                        name="category"
                        style={{ width: 180 }}
                    >
                        <Select>
                            <Option value="computer-vision">计算机视觉</Option>
                            <Option value="nlp">自然语言处理</Option>
                            <Option value="audio">音频</Option>
                            <Option value="quality-control">质量控制</Option>
                            <Option value="custom">自定义</Option>
                        </Select>
                    </Form.Item>
                </Space>

                <Divider>数据对象</Divider>

                <Form.List name="objects">
                    {(fields, { add, remove }) => (
                        <>
                            {fields.map((field) => (
                                <Card key={field.key} size="small" style={{ marginBottom: 8 }}>
                                    <Space align="start" style={{ width: "100%" }}>
                                        <Form.Item
                                            {...field}
                                            label="名称"
                                            name={[field.name, "name"]}
                                            rules={[{ required: true, message: "必填" }]}
                                            style={{ marginBottom: 0, width: 150 }}
                                        >
                                            <Input placeholder="例如：image" />
                                        </Form.Item>

                                        <Form.Item
                                            {...field}
                                            label="类型"
                                            name={[field.name, "type"]}
                                            rules={[{ required: true, message: "必填" }]}
                                            style={{ marginBottom: 0, width: 150 }}
                                        >
                                            <TagSelector type="object" />
                                        </Form.Item>

                                        <Form.Item
                                            {...field}
                                            label="值"
                                            name={[field.name, "value"]}
                                            rules={[
                                                { required: true, message: "必填" },
                                                { pattern: /^\$/, message: "必须以 $ 开头" },
                                            ]}
                                            style={{ marginBottom: 0, width: 150 }}
                                        >
                                            <Input placeholder="$image" />
                                        </Form.Item>

                                        {fields.length > 1 && (
                                            <MinusCircleOutlined
                                                style={{ marginTop: 30, color: "red" }}
                                                onClick={() => remove(field.name)}
                                            />
                                        )}
                                    </Space>
                                </Card>
                            ))}
                            <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                                添加对象
                            </Button>
                        </>
                    )}
                </Form.List>

                <Divider>标签控件</Divider>

                <Form.List name="labels">
                    {(fields, { add, remove }) => (
                        <>
                            {fields.map((field) => (
                                <Card
                                    key={field.key}
                                    size="small"
                                    style={{ marginBottom: 12 }}
                                    title={
                                        <Space>
                                            <span>控件 {fields.indexOf(field) + 1}</span>
                                            <Form.Item noStyle shouldUpdate>
                                                {() => {
                                                    const controlType = form.getFieldValue(["labels", field.name, "type"]);
                                                    const fromName = form.getFieldValue(["labels", field.name, "fromName"]);
                                                    if (controlType || fromName) {
                                                        return (
                                                            <span style={{ fontSize: 12, fontWeight: 'normal', color: '#999' }}>
                                                                ({fromName || '未命名'} - {controlType || '未设置类型'})
                                                            </span>
                                                        );
                                                    }
                                                    return null;
                                                }}
                                            </Form.Item>
                                        </Space>
                                    }
                                    extra={
                                        <MinusCircleOutlined
                                            style={{ color: "red" }}
                                            onClick={() => remove(field.name)}
                                        />
                                    }
                                >
                                    <Space direction="vertical" style={{ width: "100%" }} size="middle">
                                        {/* Row 1: 控件名称, 标注目标对象, 控件类型 */}
                                        <div style={{ display: 'grid', gridTemplateColumns: '180px 220px 1fr auto', gap: 12, alignItems: 'flex-end' }}>
                                            <Form.Item
                                                {...field}
                                                label="来源名称"
                                                name={[field.name, "fromName"]}
                                                rules={[{ required: true, message: "必填" }]}
                                                style={{ marginBottom: 0 }}
                                                tooltip="此控件的唯一标识符"
                                            >
                                                <Input placeholder="例如：choice" />
                                            </Form.Item>

                                            <Form.Item
                                                {...field}
                                                label="标注目标对象"
                                                name={[field.name, "toName"]}
                                                rules={[{ required: true, message: "必填" }]}
                                                style={{ marginBottom: 0 }}
                                                tooltip="选择此控件将标注哪个数据对象"
                                                dependencies={['objects']}
                                            >
                                                <Select placeholder="选择数据对象">
                                                    {(form.getFieldValue("objects") || []).map((obj: any, idx: number) => (
                                                        <Option key={idx} value={obj?.name || ''}>
                                                            {obj?.name || `对象 ${idx + 1}`} ({obj?.type || '未知类型'})
                                                        </Option>
                                                    ))}
                                                </Select>
                                            </Form.Item>

                                            <Form.Item
                                                {...field}
                                                label="控件类型"
                                                name={[field.name, "type"]}
                                                rules={[{ required: true, message: "必填" }]}
                                                style={{ marginBottom: 0 }}
                                            >
                                                <TagSelector type="control" />
                                            </Form.Item>

                                            <Form.Item
                                                {...field}
                                                label=" "
                                                name={[field.name, "required"]}
                                                valuePropName="checked"
                                                style={{ marginBottom: 0 }}
                                            >
                                                <Checkbox>必填</Checkbox>
                                            </Form.Item>
                                        </div>

                                        {/* Row 2: 取值范围定义（添加选项） - Conditionally rendered based on type */}
                                        <Form.Item
                                            noStyle
                                            shouldUpdate={(prevValues, currentValues) => {
                                                const prevType = prevValues.labels?.[field.name]?.type;
                                                const currType = currentValues.labels?.[field.name]?.type;
                                                return prevType !== currType;
                                            }}
                                        >
                                            {({ getFieldValue }) => {
                                                const controlType = getFieldValue(["labels", field.name, "type"]);
                                                const fieldName = controlType === "Choices" ? "options" : "labels";

                                                if (needsOptions(controlType)) {
                                                    return (
                                                        <Form.Item
                                                            {...field}
                                                            label={controlType === "Choices" ? "选项" : "标签"}
                                                            name={[field.name, fieldName]}
                                                            rules={[{ required: true, message: "至少需要一个选项" }]}
                                                            style={{ marginBottom: 0 }}
                                                        >
                                                            <Select
                                                                mode="tags"
                                                                open={false}
                                                                placeholder={
                                                                    controlType === "Choices"
                                                                        ? "输入选项内容，按回车添加。例如：是、否、不确定"
                                                                        : "输入标签名称，按回车添加。例如：人物、车辆、建筑物"
                                                                }
                                                                style={{ width: "100%" }}
                                                            />
                                                        </Form.Item>
                                                    );
                                                }
                                                return null;
                                            }}
                                        </Form.Item>

                                        {/* Row 3: 描述 */}
                                        <Form.Item
                                            {...field}
                                            label="描述"
                                            name={[field.name, "description"]}
                                            style={{ marginBottom: 0 }}
                                            tooltip="向标注人员显示的帮助信息"
                                        >
                                            <Input placeholder="为标注人员提供此控件的使用说明" maxLength={200} />
                                        </Form.Item>
                                    </Space>
                                </Card>
                            ))}
                            <Button
                                type="dashed"
                                onClick={() =>
                                    add({
                                        fromName: "",
                                        toName: "",
                                        type: "Choices",
                                        required: false,
                                    })
                                }
                                block
                                icon={<PlusOutlined />}
                            >
                                添加标签控件
                            </Button>
                        </>
                    )}
                </Form.List>
            </Form>
        </Modal>
    );
};

export default TemplateForm;
