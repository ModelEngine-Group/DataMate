"use client";

import type React from "react";
import { useState } from "react";
import { Card, Button, Input, Select, Badge, Typography, message } from "antd";
import TextArea from "antd/es/input/TextArea";
import {
  ArrowLeftOutlined,
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
import { useNavigate } from "react-router";

const { Title, Paragraph } = Typography;
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
  const [taskName, setTaskName] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [datasetFilter, setDatasetFilter] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("Computer Vision");
  const [showCustomTemplateDialog, setShowCustomTemplateDialog] =
    useState(false);

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
    if (dataset?.type === "image") {
      setSelectedCategory("Computer Vision");
    } else if (dataset?.type === "text") {
      setSelectedCategory("Natural Language Processing");
    }
    setSelectedTemplate(null);
  };

  const getDatasetTypeIcon = (type: string) => {
    switch (type) {
      case "text":
        return <FileTextOutlined style={{ color: "#1677ff" }} />;
      case "image":
        return <PictureOutlined style={{ color: "#52c41a" }} />;
      default:
        return <FileTextOutlined style={{ color: "#888" }} />;
    }
  };

  const getDatasetTypeBadge = (type: string) => {
    return (
      <Badge
        color={
          type === "text" ? "blue" : type === "image" ? "green" : "default"
        }
        text={type === "text" ? "文本" : type === "image" ? "图像" : ""}
      />
    );
  };

  const handleSubmit = () => {
    if (!taskName.trim()) {
      message.error("请输入任务名称");
      return;
    }
    if (!taskDescription.trim()) {
      message.error("请输入任务描述");
      return;
    }
    if (!selectedDataset) {
      message.error("请选择数据集");
      return;
    }
    if (!selectedTemplate) {
      message.error("请选择标注模板");
      return;
    }
    const taskData = {
      name: taskName,
      description: taskDescription,
      dataset: selectedDataset,
      template: selectedTemplate,
    };
    onCreateTask(taskData);
  };

  const handleSaveCustomTemplate = (templateData: any) => {
    setSelectedTemplate(templateData);
    message.success(`自定义模板 "${templateData.name}" 已创建`);
  };

  return (
    <div className="w-full p-6 mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate("/data/annotation")}
        >
          返回
        </Button>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            创建标注任务
          </Title>
          <Paragraph type="secondary" style={{ margin: 0 }}>
            配置新的数据标注任务
          </Paragraph>
        </div>
      </div>

      {/* Main Form */}
      <Card>
        <div className="space-y-6 pt-4">
          {/* Basic Information */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="taskName">任务名称 *</label>
                <Input
                  id="taskName"
                  placeholder="输入任务名称"
                  value={taskName}
                  onChange={(e) => setTaskName(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label htmlFor="taskDescription">任务描述 *</label>
              <TextArea
                id="taskDescription"
                placeholder="详细描述标注任务的要求和目标"
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          {/* Dataset Selection */}
          <div className="space-y-4">
            <h3 className="text-base font-medium flex items-center space-x-2">
              <DatabaseOutlined />
              <span>数据集选择</span>
            </h3>
            <Select
              value={selectedDataset?.id}
              onChange={handleDatasetSelect}
              placeholder="选择数据集"
              style={{ width: 300 }}
              showSearch
              optionFilterProp="children"
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
          </div>

          {/* Template Selection */}
          <div className="space-y-4">
            <h3 className="text-base font-medium flex items-center space-x-2">
              <span>模板选择</span>
            </h3>
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
                          selectedTemplate?.id === template.id
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-200"
                        }`}
                        onClick={() => setSelectedTemplate(template)}
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
                            {selectedTemplate?.id === template.id && (
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
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-end space-x-4">
        <Button onClick={() => navigate("/data/annotation")}>取消</Button>
        <Button type="primary" onClick={handleSubmit}>
          创建任务
        </Button>
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
