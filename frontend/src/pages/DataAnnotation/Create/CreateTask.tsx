import type React from "react";
import { useEffect, useState } from "react";
import { Card, Button, Input, Select, Divider, Form, message } from "antd";
import TextArea from "antd/es/input/TextArea";
import {
  DatabaseOutlined,
  CheckOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { mockTemplates } from "@/mock/annotation";
import CustomTemplateDialog from "./components/CustomTemplateDialog";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { queryDatasetsUsingGet } from "../../DataManagement/dataset.api";
import {
  DatasetType,
  type Dataset,
} from "@/pages/DataManagement/dataset.model";
import { useTranslation } from "react-i18next";

interface Template {
  id: string;
  name: string;
  category: string;
  description: string;
  type: "text" | "image";
  preview?: string;
  icon: React.ReactNode;
  isCustom?: boolean;
}

export default function AnnotationTaskCreate() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [showCustomTemplateDialog, setShowCustomTemplateDialog] =
    useState(false);
  const [selectedCategory, setSelectedCategory] = useState("Computer Vision");
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  // 用于Form的受控数据
  const [formValues, setFormValues] = useState({
    name: "",
    description: "",
    datasetId: "",
    templateId: "",
  });

  // Helper to get translated category label
  const getCategoryLabel = (category: string) => {
    if (category === "Computer Vision") return t('dataAnnotation.create.templateCategories.cv');
    if (category === "Natural Language Processing") return t('dataAnnotation.create.templateCategories.nlp');
    return category;
  };

  const templateCategories = ["Computer Vision", "Natural Language Processing"];

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet();
    setDatasets(data.results || []);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const filteredTemplates = mockTemplates.filter(
    (template) => template.category === selectedCategory
  );

  const handleDatasetSelect = (datasetId: string) => {
    const dataset = datasets.find((ds) => ds.id === datasetId) || null;
    setSelectedDataset(dataset);
    setFormValues((prev) => ({ ...prev, datasetId }));
    if (dataset?.type === DatasetType.PRETRAIN_IMAGE) {
      setSelectedCategory("Computer Vision");
    } else if (dataset?.type === DatasetType.PRETRAIN_TEXT) {
      setSelectedCategory("Natural Language Processing");
    }
    setSelectedTemplate(null);
    setFormValues((prev) => ({ ...prev, templateId: "" }));
  };

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
    setFormValues((prev) => ({ ...prev, templateId: template.id }));
  };

  const handleValuesChange = (_, allValues) => {
    setFormValues({ ...formValues, ...allValues });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const dataset = datasets.find((ds) => ds.id === values.datasetId);
      const template = mockTemplates.find(
        (tpl) => tpl.id === values.templateId
      );
      if (!dataset) {
        message.error(t('dataAnnotation.create.form.datasetRequired'));
        return;
      }
      if (!template) {
        message.error(t('dataAnnotation.create.form.templateRequired'));
        return;
      }
      const taskData = {
        name: values.name,
        description: values.description,
        dataset,
        template,
      };
      // onCreateTask(taskData); // 实际创建逻辑
      message.success(t('dataAnnotation.create.messages.createSuccess'));
      navigate("/data/annotation");
    } catch (e) {
      // 校验失败
    }
  };

  const handleSaveCustomTemplate = (templateData: any) => {
    setSelectedTemplate(templateData);
    setFormValues((prev) => ({ ...prev, templateId: templateData.id }));
    message.success(t('dataAnnotation.create.messages.createSuccess', { name: templateData.name }));
  };

  return (
    <div className="flex-overflow-auto">
      {/* Header */}
      <div className="flex items-center mb-2">
        <Link to="/data/annotation">
          <Button type="text">
            <ArrowLeft className="w-4 h-4 mr-1" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold bg-clip-text">{t('dataAnnotation.create.title')}</h1>
      </div>

      <div className="flex-overflow-auto bg-white rounded-lg shadow-sm">
        <div className="flex-1 overflow-y-auto p-6">
          <Form
            form={form}
            initialValues={formValues}
            onValuesChange={handleValuesChange}
            layout="vertical"
          >
            {/* 基本信息 */}
            <h2 className="font-medium text-gray-900 text-lg mb-2">{t('dataAnnotation.create.basicInfo')}</h2>
            <Form.Item
              label={t('dataAnnotation.create.form.name')}
              name="name"
              rules={[{ required: true, message: t('dataAnnotation.create.form.nameRequired') }]}
            >
              <Input placeholder={t('dataAnnotation.create.form.namePlaceholder')} />
            </Form.Item>
            <Form.Item
              label={t('dataAnnotation.create.form.description')}
              name="description"
              rules={[{ required: true, message: t('dataAnnotation.create.form.nameRequired') }]}
            >
              <TextArea placeholder={t('dataAnnotation.create.form.descriptionPlaceholder')} rows={3} />
            </Form.Item>
            <Form.Item
              label={t('dataAnnotation.create.form.dataset')}
              name="datasetId"
              rules={[{ required: true, message: t('dataAnnotation.create.form.datasetRequired') }]}
            >
              <Select
                optionFilterProp="children"
                value={formValues.datasetId}
                onChange={handleDatasetSelect}
                placeholder={t('dataAnnotation.create.form.datasetRequired')}
                size="large"
                options={datasets.map((dataset) => ({
                  label: (
                    <div className="flex items-center justify-between gap-3 py-2">
                      <div className="font-medium text-gray-900">
                        {dataset?.icon || <DatabaseOutlined className="mr-2" />}
                        {dataset.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {dataset?.fileCount} {t('common.table.file')} • {dataset.size}
                      </div>
                    </div>
                  ),
                  value: dataset.id,
                }))}
              />
            </Form.Item>

            {/* 模板选择 */}
            <h2 className="font-medium text-gray-900 text-lg mt-6 mb-2 flex items-center gap-2">
              {t('dataAnnotation.create.templateSelection')}
            </h2>
            <Form.Item
              name="templateId"
              rules={[{ required: true, message: t('dataAnnotation.create.form.templateRequired') }]}
            >
              <div className="flex">
                {/* Category Sidebar */}
                <div className="w-64 pr-6 border-r border-gray-200">
                  <div className="space-y-2">
                    {templateCategories.map((category) => {
                      const isAvailable =
                        selectedDataset?.type === "image"
                          ? category === "Computer Vision"
                          : category === "Natural Language Processing";
                      return (
                        <Button
                          key={category}
                          type={
                            selectedCategory === category && isAvailable
                              ? "primary"
                              : "default"
                          }
                          block
                          disabled={!isAvailable}
                          onClick={() =>
                            isAvailable && setSelectedCategory(category)
                          }
                          style={{ textAlign: "left", marginBottom: 8 }}
                        >
                          {getCategoryLabel(category)}
                        </Button>
                      );
                    })}
                    <Button
                      type="dashed"
                      block
                      icon={<PlusOutlined />}
                      onClick={() => setShowCustomTemplateDialog(true)}
                    >
                      {t('dataAnnotation.create.customTemplate')}
                    </Button>
                  </div>
                </div>
                {/* Template Grid */}
                <div className="flex-1 pl-6">
                  <div className="max-h-96 overflow-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredTemplates.map((template) => (
                        <div
                          key={template.id}
                          className={`border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                            formValues.templateId === template.id
                              ? "border-blue-500 bg-blue-50"
                              : "border-gray-200"
                          }`}
                          onClick={() => handleTemplateSelect(template)}
                        >
                          {template.preview && (
                            <div className="aspect-video bg-gray-100 rounded-t-lg overflow-hidden">
                              <img
                                src={template.preview || "/placeholder.svg"}
                                alt={template.name}
                                className="w-full h-full object-cover"
                              />
                            </div>
                          )}
                          <div className="p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                {template.icon}
                                <span className="font-medium text-sm">
                                  {template.name}
                                </span>
                              </div>
                            </div>
                            <p className="text-xs text-gray-600">
                              {template.description}
                            </p>
                          </div>
                        </div>
                      ))}
                      {/* Custom Template Option */}
                      <div
                        className={`border-2 border-dashed rounded-lg cursor-pointer transition-all hover:border-gray-400 ${
                          selectedTemplate?.isCustom
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-300"
                        }`}
                        onClick={() => setShowCustomTemplateDialog(true)}
                      >
                        <div className="aspect-video bg-gray-50 rounded-t-lg flex items-center justify-center">
                          <PlusOutlined
                            style={{ fontSize: 32, color: "#bbb" }}
                          />
                        </div>
                        <div className="p-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <PlusOutlined />
                              <span className="font-medium text-sm">
                                {t('dataAnnotation.create.customTemplate')}
                              </span>
                            </div>
                            {selectedTemplate?.isCustom && (
                              <CheckOutlined style={{ color: "#1677ff" }} />
                            )}
                          </div>
                          <p className="text-xs text-gray-600">
                            {t('dataAnnotation.create.customTemplateDesc')}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {selectedTemplate && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <span
                      className="text-sm font-medium"
                      style={{ color: "#1677ff" }}
                    >
                      {t('dataAnnotation.create.selectedTemplate')}
                    </span>
                  </div>
                  <p
                    className="text-sm"
                    style={{ color: "#1677ff", marginTop: 4 }}
                  >
                    {selectedTemplate.name} - {selectedTemplate.description}
                  </p>
                </div>
              )}
            </Form.Item>
          </Form>
        </div>
        <div className="flex gap-2 justify-end border-t border-gray-200 p-6">
          <Button onClick={() => navigate("/data/annotation")}>{t('dataAnnotation.create.cancel')}</Button>
          <Button type="primary" onClick={handleSubmit}>
            {t('dataAnnotation.create.submit')}
          </Button>
        </div>
      </div>

      {/* Custom Template Dialog */}
      <CustomTemplateDialog
        open={showCustomTemplateDialog}
        onOpenChange={setShowCustomTemplateDialog}
        onSaveTemplate={handleSaveCustomTemplate}
        datasetType={selectedDataset?.type || "image"}
      />
    </div>
  );
}
