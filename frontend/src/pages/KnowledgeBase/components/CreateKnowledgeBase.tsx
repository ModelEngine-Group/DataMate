import { Button, Form, Input, message, Modal, Select, Tooltip } from "antd";
import RadioCard from "@/components/RadioCard";
import { InfoCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { Share2, BookOpen } from "lucide-react";
import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { queryModelListUsingGet } from "@/pages/SettingsPage/settings.apis";
import { ModelI } from "@/pages/SettingsPage/ModelAccess";
import {
  createKnowledgeBaseUsingPost,
  updateKnowledgeBaseByIdUsingPut,
} from "../knowledge-base.api";
import { KnowledgeBaseItem, KBType } from "../knowledge-base.model";
import { showSettings } from "@/store/slices/settingsSlice";
import { getKBTypeMap } from "../knowledge-base.const";
import { useTranslation } from "react-i18next";

export default function CreateKnowledgeBase({
  isEdit,
  data,
  showBtn = true,
  onUpdate,
  onClose,
}: {
  isEdit?: boolean;
  showBtn?: boolean;
  data?: Partial<KnowledgeBaseItem> | null;
  onUpdate: () => void;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const [models, setModels] = useState<ModelI[]>([]);
  const dispatch = useDispatch();

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
        type: data.type ?? KBType.DOCUMENT,
        customEntities: data.customEntities ?? [],
      });
    } else {
      form.setFieldsValue({ type: KBType.DOCUMENT, customEntities: [] });
    }
  }, [isEdit, data, form]);

  const typeValue = Form.useWatch("type", form);
  const isGraphKB = typeValue === KBType.GRAPH;

  const kbTypes = getKBTypeMap(t);
  const typeOptions = [
    {
      value: KBType.DOCUMENT,
      label: kbTypes[KBType.DOCUMENT]?.label || t("knowledgeBase.const.type.vector"),
      description: kbTypes[KBType.DOCUMENT]?.description || t("knowledgeBase.create.type.documentDesc"),
      icon: BookOpen,
    },
    {
      value: KBType.GRAPH,
      label: kbTypes[KBType.GRAPH]?.label || t("knowledgeBase.const.type.graph"),
      description: kbTypes[KBType.GRAPH]?.description || t("knowledgeBase.create.type.graphDesc"),
      icon: Share2,
    },
  ];

  const handleCreateKnowledgeBase = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        customEntities: values.type === KBType.GRAPH ? values.customEntities : undefined,
      };
      if (isEdit && data) {
        await updateKnowledgeBaseByIdUsingPut(data.id!, payload);
        message.success(t("knowledgeBase.create.messages.updateSuccess"));
      } else {
        await createKnowledgeBaseUsingPost(payload);
        message.success(t("knowledgeBase.create.messages.createSuccess"));
      }
      setOpen(false);
      onUpdate();
    } catch (error) {
      message.error(t("knowledgeBase.create.messages.operationFailed") + error.data.message);
    }
  };

  const handleCloseModal = () => {
    setOpen(false);
    onClose?.();
  };

  return (
    <>
      {showBtn && (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields();
            setOpen(true);
          }}
        >
          {t("knowledgeBase.create.title")}
        </Button>
      )}
      <Modal
        title={isEdit ? t("knowledgeBase.create.editTitle") : t("knowledgeBase.create.title")}
        open={open}
        okText={t("knowledgeBase.create.okText")}
        cancelText={t("knowledgeBase.create.cancelText")}
        maskClosable={false}
        onCancel={handleCloseModal}
        onOk={handleCreateKnowledgeBase}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label={t("knowledgeBase.create.form.typeLabel")}
            name="type"
            rules={[{ required: true, message: t("knowledgeBase.create.form.typeRequired") }]}
          >
            <RadioCard
              value={typeValue}
              onChange={(val) => form.setFieldValue("type", val)}
              options={typeOptions}
            />
          </Form.Item>
          {isGraphKB && (
            <Form.Item
              label={
                <div className="flex items-center gap-2">
                  <span>{t("knowledgeBase.create.form.entityLabel")}</span>
                  <Tooltip title={t("knowledgeBase.create.form.entityTooltip")}>
                    <InfoCircleOutlined className="text-gray-400" />
                  </Tooltip>
                </div>
              }
              name="customEntities"
              rules={[{ type: "array" }]}
            >
              <Select
                mode="tags"
                placeholder={t("knowledgeBase.create.form.entityPlaceholder")}
                tokenSeparators={[",", " "]}
              />
            </Form.Item>
          )}
          <Form.Item
            label={t("knowledgeBase.create.form.nameLabel")}
            name="name"
            rules={[{ required: true, message: t("knowledgeBase.create.form.nameRequired") }]}
          >
            <Input placeholder={t("knowledgeBase.create.form.namePlaceholder")} />
          </Form.Item>
          <Form.Item
            label={t("knowledgeBase.create.form.descriptionLabel")}
            name="description"
            rules={[{ required: false }]}
          >
            <Input.TextArea placeholder={t("knowledgeBase.create.form.descriptionPlaceholder")} rows={4} />
          </Form.Item>
          <Form.Item
            label={t("knowledgeBase.create.form.embeddingModelLabel")}
            name="embeddingModel"
            rules={[{ required: true, message: t("knowledgeBase.create.form.embeddingModelRequired") }]}
          >
            <Select
              placeholder={t("knowledgeBase.create.form.embeddingModelPlaceholder")}
              options={embeddingModelOptions}
              disabled={isEdit} // 编辑模式下禁用索引模型修改
              popupRender={(menu) => (
                <>
                  {menu}
                  <Button
                    block
                    type="link"
                    icon={<PlusOutlined />}
                    onClick={() => dispatch(showSettings())}
                  >
                    {t("knowledgeBase.create.form.addModel")}
                  </Button>
                </>
              )}
            />
          </Form.Item>
          <Form.Item
            label={t("knowledgeBase.create.form.chatModelLabel")}
            name="chatModel"
            rules={[{ required: true, message: t("knowledgeBase.create.form.chatModelRequired") }]}
          >
            <Select
              placeholder={t("knowledgeBase.create.form.chatModelPlaceholder")}
              options={chatModelOptions}
              popupRender={(menu) => (
                <>
                  {menu}
                  <Button
                    block
                    type="link"
                    icon={<PlusOutlined />}
                    onClick={() => dispatch(showSettings())}
                  >
                    {t("knowledgeBase.create.form.addModel")}
                  </Button>
                </>
              )}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
