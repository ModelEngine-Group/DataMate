import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { mapDataset } from "@/pages/DataManagement/dataset.const";
import { Button, Form, Input, Modal, Select, message } from "antd";
import TextArea from "antd/es/input/TextArea";
import { useEffect, useState } from "react";
import { createAnnotationTaskUsingPost } from "../../annotation.api";
import { Dataset } from "@/pages/DataManagement/dataset.model";
import LabelingConfigEditor from "./LabelingConfigEditor";
import { useRef } from "react";

export default function CreateAnnotationTask({
  open,
  onClose,
  onRefresh,
}: {
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const [form] = Form.useForm();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [nameManuallyEdited, setNameManuallyEdited] = useState(false);
  const editorRef = useRef<any>(null);
  const EDITOR_LIST_HEIGHT = 420;

  useEffect(() => {
    if (!open) return;
    const fetchDatasets = async () => {
      const { data } = await queryDatasetsUsingGet({
        page: 0,
        size: 1000,
      });
      setDatasets(data.content.map(mapDataset) || []);
    };
    fetchDatasets();
  }, [open]);

  // Reset form and manual-edit flag when modal opens
  useEffect(() => {
    if (open) {
      form.resetFields();
      setNameManuallyEdited(false);
    }
  }, [open, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      await createAnnotationTaskUsingPost(values);
      message?.success?.("创建标注任务成功");
      onClose();
      onRefresh();
    } catch (err: any) {
      console.error("Create annotation task failed", err);
      const msg = err?.message || err?.data?.message || "创建失败，请稍后重试";
      // show a user friendly message
      (message as any)?.error?.(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Placeholder function: generates labeling interface from config
  // For now it simply returns the parsed config (per requirement)
  const generateLabelingInterface = (config: any) => {
    return config;
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="创建标注任务"
      footer={
        <>
          <Button onClick={onClose} disabled={submitting}>
            取消
          </Button>
          <Button type="primary" onClick={handleSubmit} loading={submitting}>
            确定
          </Button>
        </>
      }
      width={1200}
    >
      <Form form={form} layout="vertical">
        {/* 数据集 与 标注工程名称 并排显示（数据集在左） */}
        <div className="grid grid-cols-2 gap-4">
          <Form.Item
            label="数据集"
            name="datasetId"
            rules={[{ required: true, message: "请选择数据集" }]}
          >
            <Select
              placeholder="请选择数据集"
              options={datasets.map((dataset) => {
                return {
                  label: (
                    <div className="flex items-center justify-between gap-3 py-2">
                      <div className="flex items-center font-sm text-gray-900">
                        <span className="mr-2">{(dataset as any).icon}</span>
                        <span>{dataset.name}</span>
                      </div>
                      <div className="text-xs text-gray-500">{dataset.size}</div>
                    </div>
                  ),
                  value: dataset.id,
                };
              })}
              onChange={(value) => {
                // 如果用户未手动修改名称，则用数据集名称作为默认任务名
                if (!nameManuallyEdited) {
                  const ds = datasets.find((d) => d.id === value);
                  if (ds) {
                    form.setFieldsValue({ name: ds.name });
                  }
                }
              }}
            />
          </Form.Item>

          <Form.Item
            label="标注工程名称"
            name="name"
            rules={[{ required: true, message: "请输入任务名称" }]}
          >
            <Input
              placeholder="输入标注工程名称"
              onChange={() => setNameManuallyEdited(true)}
            />
          </Form.Item>
        </div>
        {/* 描述变为可选 */}
        <Form.Item label="描述" name="description">
          <TextArea placeholder="（可选）详细描述标注任务的要求和目标" rows={3} />
        </Form.Item>

        {/* 标注页面设计 模块：左侧为配置编辑，右侧为预览（作为表单的一部分，与其他字段同级） */}
        <div style={{ marginTop: 8 }}>
          <label className="block font-medium mb-2">标注页面设计</label>
          <div style={{ display: "grid", gridTemplateColumns: "minmax(360px, 1fr) 1fr", gridTemplateRows: "auto 1fr", gap: 16 }}>
            {/* Row 1: buttons on the left, spacer on the right so preview aligns with editor below */}
            <div style={{ gridColumn: 1, gridRow: 1, display: 'flex', gap: 8 }}>
              <Button onClick={() => editorRef.current?.addLabel?.()}>添加标签</Button>
              <Button type="primary" onClick={() => editorRef.current?.generate?.()}>生成标注页面配置</Button>
            </div>

            {/* empty spacer to occupy top-right cell so preview starts on the second row */}
            <div style={{ gridColumn: 2, gridRow: 1 }} />

            {/* Row 2, Col 1: 编辑列表（固定高度） */}
            <div style={{ gridColumn: 1, gridRow: 2, height: EDITOR_LIST_HEIGHT, overflowY: 'auto', paddingRight: 8, border: '1px solid #e6e6e6', borderRadius: 6, padding: 12 }}>
              <LabelingConfigEditor
                ref={editorRef}
                hideFooter={true}
                initial={undefined}
                onGenerate={(config: any) => {
                  form.setFieldsValue({ labelingConfig: JSON.stringify(config, null, 2), labelingInterface: JSON.stringify(generateLabelingInterface(config), null, 2) });
                }}
              />
              <Form.Item
                name="labelingConfig"
                rules={[
                  {
                    validator: async (_, value) => {
                      if (!value || value === "") return Promise.resolve();
                      try {
                        JSON.parse(value);
                        return Promise.resolve();
                      } catch (e) {
                        return Promise.reject(new Error("请输入有效的 JSON"));
                      }
                    },
                  },
                ]}
                style={{ display: "none" }}
              >
                <Input />
              </Form.Item>
            </div>

            {/* Row 2, Col 2: 预览，与编辑列表在同一行，保持一致高度 */}
            <div style={{ gridColumn: 2, gridRow: 2, display: 'flex', flexDirection: 'column' }}>
              <Form.Item name="labelingInterface" style={{ flex: 1 }}>
                <TextArea
                  placeholder="标注页面设计（只读，由标注配置生成）"
                  disabled
                  style={{ height: EDITOR_LIST_HEIGHT, resize: 'none' }}
                />
              </Form.Item>
            </div>
          </div>
        </div>
      </Form>
    </Modal>
  );
}
