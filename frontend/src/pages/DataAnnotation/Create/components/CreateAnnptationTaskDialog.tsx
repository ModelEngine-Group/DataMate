import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { mapDataset } from "@/pages/DataManagement/dataset.const";
import { Button, Form, Input, Modal, Select, message } from "antd";
import TextArea from "antd/es/input/TextArea";
import { useEffect, useState } from "react";
import { createAnnotationTaskUsingPost, queryAnnotationTemplatesUsingGet } from "../../annotation.api";
import { Dataset } from "@/pages/DataManagement/dataset.model";
import type { AnnotationTemplate } from "../../annotation.model";
import { useTranslation } from "react-i18next";

export default function CreateAnnotationTask({
  open,
  onClose,
  onRefresh,
}: {
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [templates, setTemplates] = useState<AnnotationTemplate[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [nameManuallyEdited, setNameManuallyEdited] = useState(false);

  useEffect(() => {
    if (!open) return;
    const fetchData = async () => {
      try {
        // Fetch datasets
        const { data: datasetData } = await queryDatasetsUsingGet({
          page: 0,
          pageSize: 1000,  // Use camelCase for HTTP params
        });
        setDatasets(datasetData.content.map(dataset => mapDataset(dataset, t)) || []);

        // Fetch templates
        const templateResponse = await queryAnnotationTemplatesUsingGet({
          page: 1,
          size: 100,  // Backend max is 100 (template API uses 'size' not 'pageSize')
        });

        // The API returns: {code, message, data: {content, total, page, ...}}
        if (templateResponse.code === 200 && templateResponse.data) {
          const fetchedTemplates = templateResponse.data.content || [];
          console.log("Fetched templates:", fetchedTemplates);
          setTemplates(fetchedTemplates);
        } else {
          console.error("Failed to fetch templates:", templateResponse);
          setTemplates([]);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        setTemplates([]);
      }
    };
    fetchData();
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

      // Send templateId instead of labelingConfig
      const requestData = {
        name: values.name,
        description: values.description,
        datasetId: values.datasetId,
        templateId: values.templateId,
      };

      await createAnnotationTaskUsingPost(requestData);
      message?.success?.("创建标注任务成功");
      onClose();
      onRefresh();
    } catch (err: any) {
      console.error("Create annotation task failed", err);
      const msg = err?.message || err?.data?.message || "创建失败，请稍后重试";
      (message as any)?.error?.(msg);
    } finally {
      setSubmitting(false);
    }
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
      width={800}
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

        {/* 标注模板选择 */}
        <Form.Item
          label="标注模板"
          name="templateId"
          rules={[{ required: true, message: "请选择标注模板" }]}
        >
          <Select
            placeholder={templates.length === 0 ? "暂无可用模板，请先创建模板" : "请选择标注模板"}
            showSearch
            optionFilterProp="label"
            notFoundContent={templates.length === 0 ? "暂无模板，请前往「标注模板」页面创建" : "未找到匹配的模板"}
            options={templates.map((template) => ({
              label: template.name,
              value: template.id,
              // Add description as subtitle
              title: template.description,
            }))}
            optionRender={(option) => (
              <div>
                <div style={{ fontWeight: 500 }}>{option.label}</div>
                {option.data.title && (
                  <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
                    {option.data.title}
                  </div>
                )}
              </div>
            )}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
