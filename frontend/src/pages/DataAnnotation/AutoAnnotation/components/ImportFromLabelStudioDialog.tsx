import { useEffect, useState } from "react";
import { Modal, Form, Select, Input, message } from "antd";
import type { AutoAnnotationTask } from "../../annotation.model";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import { importAutoAnnotationFromLabelStudioUsingPost } from "../../annotation.api";

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
  const [form] = Form.useForm();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) return;

    let cancelled = false;

    (async () => {
      try {
        const resp: any = await queryDatasetsUsingGet({ page: 0, size: 1000 });
        const list: Dataset[] = resp?.content || resp?.data?.content || resp?.data || resp || [];
        if (!cancelled && Array.isArray(list)) {
          setDatasets(list);
        }
      } catch (e) {
        console.error("Failed to fetch datasets for LS import:", e);
        if (!cancelled) {
          message.error("获取数据集列表失败");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [visible]);

  useEffect(() => {
    if (visible && task) {
      // 默认选中任务原始数据集和 JSON 导出格式
      form.setFieldsValue({
        targetDatasetId: task.datasetId,
        exportFormat: "JSON",
      });
    }
  }, [visible, task, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const targetDatasetId: string = values.targetDatasetId;
      const exportFormat: string = values.exportFormat;
      const fileName: string | undefined = values.fileName;

      if (!task?.id) {
        message.error("未找到自动标注任务");
        return;
      }

      setLoading(true);
      await importAutoAnnotationFromLabelStudioUsingPost(task.id, {
        targetDatasetId,
        exportFormat,
        // 后端会自动附加正确的扩展名
        fileName: fileName?.trim() || undefined,
      });

      message.success("已从 Label Studio 导出结果并保存到数据集");
      onSuccess();
    } catch (e: any) {
      if (e?.errorFields) {
        // 表单校验错误，忽略
        return;
      }
      console.error("Failed to import from Label Studio:", e);
      message.error(e?.message || "后向同步失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="从 Label Studio 导回结果"
      open={visible}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical">
        <Form.Item label="自动标注任务">
          <span>{task?.name || "-"}</span>
        </Form.Item>

        <Form.Item
          label="导入目标数据集"
          name="targetDatasetId"
          rules={[{ required: true, message: "请选择目标数据集" }]}
        >
          <Select
            placeholder="请选择要导入到的数据集"
            optionFilterProp="label"
            showSearch
            options={datasets.map((ds) => ({
              label: ds.name,
              value: ds.id,
            }))}
          />
        </Form.Item>

        <Form.Item
          label="导出/导入格式"
          name="exportFormat"
          rules={[{ required: true, message: "请选择导出格式" }]}
        >
          <Select
            options={EXPORT_FORMAT_OPTIONS.map((fmt) => ({
              label: fmt,
              value: fmt,
            }))}
          />
        </Form.Item>

        <Form.Item
          label="保存文件名（可选，不含扩展名）"
          name="fileName"
        >
          <Input
            placeholder="留空则使用默认文件名，如 ls_export_xxx_时间戳"
          />
        </Form.Item>

        <div className="text-xs text-gray-500 mt-2">
          将从与该自动标注任务关联的 Label Studio 项目中，
          按所选格式导出完整标注结果，并作为一个文件保存到所选数据集中。
          不会修改已有标签，仅追加一个导出工件文件。
        </div>
      </Form>
    </Modal>
  );
}
