import { Button, Form, Input, message, Modal, Select } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import { queryModelListUsingGet } from "@/pages/SettingsPage/settings.apis";
import { ModelI } from "@/pages/SettingsPage/ModelAccess";
import {
  createKnowledgeBaseUsingPost,
  updateKnowledgeBaseByIdUsingPut,
} from "../knowledge-base.api";
import { KnowledgeBaseItem } from "../knowledge-base.model";

export default function CreateKnowledgeBase({
  isEdit,
  data,
  onUpdate,
}: {
  isEdit?: boolean;
  data?: Partial<KnowledgeBaseItem> | null;
  onUpdate: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const [models, setModels] = useState<ModelI[]>([]);

  const embeddingModelOptions = models
    .filter((model) => model.type === "EMBEDDING")
    .map((model) => ({
      label: model.modelName + " (" + model.provider + ")",
      value: model.id,
    }));

  const chatModelOptions = models
    .filter((model) => model.type === "CHAT")
    .map((model) => ({
      label: model.modelName + " (" + model.provider + ")",
      value: model.id,
    }));

  const fetchModels = async () => {
    const { data } = await queryModelListUsingGet({ page: 0, size: 1000 });
    setModels(data.content || []);
  };

  useEffect(() => {
    if (open) fetchModels();
  }, [open]);

  useEffect(() => {
    if (isEdit && data) {
      setOpen(true);
      form.setFieldsValue({
        name: data.name,
        description: data.description,
        embeddingModel: data.embeddingModel,
        chatModel: data.chatModel,
      });
    }
  }, [isEdit, data, form]);

  const handleCreateKnowledgeBase = async () => {
    try {
      const values = await form.validateFields();
      if (isEdit && data) {
        await updateKnowledgeBaseByIdUsingPut(data.id!, values);
        message.success("知识库更新成功");
      } else {
        await createKnowledgeBaseUsingPost(values);
        message.success("知识库创建成功");
      }
      setOpen(false);
      onUpdate();
    } catch (error) {
      message.error("操作失败:", error.data.message);
    }
  };

  return (
    <>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={() => {
          form.resetFields();
          setOpen(true);
        }}
      >
        创建知识库
      </Button>
      <Modal
        title={isEdit ? "编辑知识库" : "创建知识库"}
        open={open}
        okText="确定"
        cancelText="取消"
        onCancel={() => setOpen(false)}
        onOk={handleCreateKnowledgeBase}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="知识库名称"
            name="name"
            rules={[{ required: true, message: "请输入知识库名称" }]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>
          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: false }]}
          >
            <Input.TextArea placeholder="请输入知识库描述（可选）" rows={4} />
          </Form.Item>
          <Form.Item
            label="索引模型"
            name="embeddingModel"
            rules={[{ required: true, message: "请选择索引模型" }]}
          >
            <Select
              placeholder="请选择索引模型"
              options={embeddingModelOptions}
            />
          </Form.Item>
          <Form.Item
            label="文本理解模型"
            name="chatModel"
            rules={[{ required: true, message: "请选择文本理解模型" }]}
          >
            <Select
              placeholder="请选择文本理解模型"
              options={chatModelOptions}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
