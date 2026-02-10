import { useEffect, useState } from "react";
import { Modal, Form, Select, Input, message } from "antd";
import type { AutoAnnotationTask } from "../../annotation.model";
import { importAutoAnnotationFromLabelStudioUsingPost } from "../../annotation.api";
import { useTranslation } from "react-i18next";

interface ImportFromLabelStudioDialogProps {
  visible: boolean;
  task: AutoAnnotationTask | null;
  onCancel: () => void;
  onSuccess: () => void;
}

const EXPORT_FORMAT_OPTIONS = [
  "JSON",
  "JSON_MIN",
  "CSV",
  "TSV",
  "COCO",
  "YOLO",
  "YOLOv8",
];

export default function ImportFromLabelStudioDialog({
  visible,
  task,
  onCancel,
  onSuccess,
}: ImportFromLabelStudioDialogProps) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible && task) {
      // 默认选中任务原始数据集和 JSON 导出格式
      form.setFieldsValue({
        exportFormat: "JSON",
      });
    }
  }, [visible, task, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const exportFormat: string = values.exportFormat;
      const fileName: string | undefined = values.fileName;

      if (!task?.id) {
        message.error(t("dataAnnotation.home.messages.autoTaskNotFound"));
        return;
      }

      setLoading(true);
      await importAutoAnnotationFromLabelStudioUsingPost(task.id, {
        exportFormat,
        // 后端会自动附加正确的扩展名
        fileName: fileName?.trim() || undefined,
      });

      message.success(t("dataAnnotation.dialogs.importFromLS.success"));
      onSuccess();
    } catch (e: any) {
      if (e?.errorFields) {
        return;
      }
      console.error("Failed to import from Label Studio:", e);
      message.error(e?.message || t("dataAnnotation.dialogs.importFromLS.failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={t("dataAnnotation.dialogs.importFromLS.title")}
      open={visible}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical">
        <Form.Item label={t("dataAnnotation.dialogs.importFromLS.taskLabelAuto")}>
          <span>{task?.name || "-"}</span>
        </Form.Item>

        <Form.Item
          label={t("dataAnnotation.dialogs.importFromLS.exportFormat")}
          name="exportFormat"
          rules={[{ required: true, message: t("dataAnnotation.dialogs.importFromLS.exportFormatRequired") }]}
        >
          <Select
            options={EXPORT_FORMAT_OPTIONS.map((fmt) => ({
              label: fmt,
              value: fmt,
            }))}
          />
        </Form.Item>

        <Form.Item
          label={t("dataAnnotation.dialogs.importFromLS.fileNameLabel")}
          name="fileName"
        >
          <Input
            placeholder={t("dataAnnotation.dialogs.importFromLS.fileNamePlaceholder")}
          />
        </Form.Item>

        <div className="text-xs text-gray-500 mt-2">
          {t("dataAnnotation.dialogs.importFromLS.description")}
        </div>
      </Form>
    </Modal>
  );
}
