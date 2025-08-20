import type React from "react";
import { useState } from "react";
import { Card, Button, Input, Select, Badge, Divider, Form, message } from "antd";
import TextArea from "antd/es/input/TextArea";
import {
  DatabaseOutlined,
  FileTextOutlined,
  PictureOutlined,
  CheckOutlined,
  EyeOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { mockDatasets } from "@/mock/dataset";
import { mockTemplates } from "@/mock/annotation";
import { CustomTemplateDialog } from "./components/AnnotationTemplate";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";

const { Option } = Select;

interface Dataset {
  id: string;
  name: string;
  type: "text" | "image";
  description: string;
  fileCount: number;
  size: string;
  createdAt: string;
}

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

const templateCategories = ["Computer Vision", "Natural Language Processing"];

export default function AnnotationTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [showCustomTemplateDialog, setShowCustomTemplateDialog] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("Computer Vision");
  const [searchQuery, setSearchQuery] = useState("");
  const [datasetFilter, setDatasetFilter] = useState("all");
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  // 用于Form的受控数据
  const [formValues, setFormValues] = useState({
    name: "",
    description: "",
    datasetId: "",
    templateId: "",
  });

  const filteredDatasets = mockDatasets.filter((dataset) => {
    const matchesSearch =
      dataset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dataset.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter =
      datasetFilter === "all" || dataset.type === datasetFilter;
    return matchesSearch && matchesFilter;
  });

  const filteredTemplates = mockTemplates.filter(
    (template) => template.category === selectedCategory
  );

  const handleDatasetSelect = (datasetId: string) => {
    const dataset = mockDatasets.find((ds) => ds.id === datasetId) || null;
    setSelectedDataset(dataset);
    setFormValues((prev) => ({ ...prev, datasetId }));
    if (dataset?.type === "image") {
      setSelectedCategory("Computer Vision");
    } else if (dataset?.type === "text") {
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
      const dataset = mockDatasets.find((ds) => ds.id === values.datasetId);
      const template = mockTemplates.find((tpl) => tpl.id === values.templateId);
      if (!dataset) {
        message.error("请选择数据集");
        return;
      }
      if (!template) {
        message.error("请选择标注模板");
        return;
      }
      const taskData = {
        name: values.name,
        description: values.description,
        dataset,
        template,
      };
      // onCreateTask(taskData); // 实际创建逻辑
      message.success("标注任务创建成功");
      navigate("/data/annotation");
    } catch (e) {
      // 校验失败
    }
  };

  const handleSaveCustomTemplate = (templateData: any) => {
    setSelectedTemplate(templateData);
    setFormValues((prev) => ({ ...prev, templateId: templateData.id }));
    message.success(`自定义模板 "${templateData.name}" 已创建`);
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center mb-2">
        <Link to="/data/annotation">
          <Button type="text">
            <ArrowLeft className="w-4 h-4 mr-1" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold bg-clip-text">创建标注任务</h1>
      </div>

      <Card className="overflow-y-auto p-2">
        <Form
          form={form}
          initialValues={formValues}
          onValuesChange={handleValuesChange}
          layout="vertical"
        >
          {/* 基本信息 */}
          <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>
          <Form.Item
            label="任务名称"
            name="name"
            rules={[{ required: true, message: "请输入任务名称" }]}
          >
            <Input placeholder="输入任务名称" />
          </Form.Item>
          <Form.Item
            label="任务描述"
            name="description"
            rules={[{ required: true, message: "请输入任务描述" }]}
          >
            <TextArea placeholder="详细描述标注任务的要求和目标" rows={3} />
          </Form.Item>
          <Form.Item
            label="选择数据集"
            name="datasetId"
            rules={[{ required: true, message: "请选择数据集" }]}
          >
            <Select
              placeholder="选择数据集"
              showSearch
              optionFilterProp="children"
              onChange={handleDatasetSelect}
              value={formValues.datasetId}
              className="w-full"
            >
              {filteredDatasets.map((dataset) => (
                <Option key={dataset.id} value={dataset.id}>
                  <div className="flex items-center gap-2">
                    <DatabaseOutlined />
                    <div>
                      <div className="font-medium">{dataset.name}</div>
                      <div className="text-xs text-gray-500">
                        {dataset.fileCount} 个文件 • {dataset.size}
                      </div>
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          {/* 模板选择 */}
          <h2 className="font-medium text-gray-900 text-lg mt-6 mb-2 flex items-center gap-2">
            模板选择
          </h2>
          <Form.Item
            label=""
            name="templateId"
            rules={[{ required: true, message: "请选择标注模板" }]}
          >
            <div className="flex">
              {/* Category Sidebar */}
              <div className="w-64 pr-6 border-r">
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
                        {category}
                      </Button>
                    );
                  })}
                  <Button
                    type="dashed"
                    block
                    icon={<PlusOutlined />}
                    onClick={() => setShowCustomTemplateDialog(true)}
                  >
                    自定义模板
                  </Button>
                </div>
              </div>
              {/* Template Grid */}
              <div className="flex-1 pl-6">
                <div style={{ maxHeight: 384, overflowY: "auto" }}>
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
                            {formValues.templateId === template.id && (
                              <CheckOutlined style={{ color: "#1677ff" }} />
                            )}
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
                        <PlusOutlined style={{ fontSize: 32, color: "#bbb" }} />
                      </div>
                      <div className="p-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <PlusOutlined />
                            <span className="font-medium text-sm">
                              自定义模板
                            </span>
                          </div>
                          {selectedTemplate?.isCustom && (
                            <CheckOutlined style={{ color: "#1677ff" }} />
                          )}
                        </div>
                        <p className="text-xs text-gray-600">
                          创建符合特定需求的标注模板
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
                  <EyeOutlined style={{ color: "#1677ff" }} />
                  <span
                    className="text-sm font-medium"
                    style={{ color: "#1677ff" }}
                  >
                    已选择模板
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
          <Divider />
          <div className="flex gap-2 justify-end">
            <Button onClick={() => navigate("/data/annotation")}>取消</Button>
            <Button type="primary" onClick={handleSubmit}>
              创建任务
            </Button>
          </div>
        </Form>
      </Card>
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
