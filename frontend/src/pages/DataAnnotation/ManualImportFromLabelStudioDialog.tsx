import { useEffect, useState } from "react";
import { Modal, Form, Select, Input, message } from "antd";
import type { AnnotationTask } from "./annotation.model";
import { importManualAnnotationFromLabelStudioUsingPost } from "./annotation.api";
import { useTranslation } from "react-i18next";

interface ManualImportFromLabelStudioDialogProps {
  visible: boolean;
  task: AnnotationTask | null;
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

export default function ManualImportFromLabelStudioDialog({
  visible,
  task,
  onCancel,
  onSuccess,
}: ManualImportFromLabelStudioDialogProps) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible && task) {
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
        message.error(t("dataAnnotation.home.messages.taskNotFound"));
        return;
      }

      setLoading(true);
      await importManualAnnotationFromLabelStudioUsingPost(task.id, {
        exportFormat,
        fileName: fileName?.trim() || undefined,
      });

      message.success(t("dataAnnotation.dialogs.importFromLS.success"));
      onSuccess();
    } catch (e: any) {
      if (e?.errorFields) {
        return;
      }
      console.error("Failed to import manual annotations from Label Studio:", e);
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
        <Form.Item label={t("dataAnnotation.dialogs.importFromLS.taskLabel")}>
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
