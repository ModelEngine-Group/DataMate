import { useState } from "react";
import { Card, Button, Input,  Steps, Form, Divider } from "antd";
import OperatorOrchestrationPage from "./components/Orchestration";
import { Link, useNavigate } from "react-router";
import RadioCard from "@/components/RadioCard";
import { ArrowLeft } from "lucide-react";

const { TextArea } = Input;

export default function CleansingTemplateCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedOperators, setSelectedOperators] = useState<any[]>([]);

  // 模板类型选项
  const templateTypes = [
    {
      value: "text",
      label: "文本",
      icon: "📝",
      description: "处理文本数据的清洗模板",
    },
    {
      value: "image",
      label: "图片",
      icon: "🖼️",
      description: "处理图像数据的清洗模板",
    },
    {
      value: "video",
      label: "视频",
      icon: "🎥",
      description: "处理视频数据的清洗模板",
    },
    {
      value: "audio",
      label: "音频",
      icon: "🎵",
      description: "处理音频数据的清洗模板",
    },
    {
      value: "image-to-text",
      label: "图片转文本",
      icon: "🔄",
      description: "图像识别转文本的处理模板",
    },
  ];

  const [templateConfig, setTemplateConfig] = useState({
    name: "",
    description: "",
    type: "",
    category: "",
  });

  const addOperator = (operator: any) => {
    const newOperator = {
      ...operator,
      id: `${operator.id}_${Date.now()}`,
      originalId: operator.id,
      config: Object.keys(operator.params || {}).reduce(
        (acc: any, param: any) => {
          acc[param.name] = param.default;
          return acc;
        },
        {}
      ),
    };
    setSelectedOperators([...selectedOperators, newOperator]);
  };

  const removeOperator = (id: string) => {
    setSelectedOperators(selectedOperators.filter((item) => item.id !== id));
  };

  const handleNext = () => {
    if (currentStep < 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSave = () => {
    const values = form.getFieldsValue();
    const template = {
      ...values,
      operators: selectedOperators,
      createdAt: new Date().toISOString(),
    };
    // onSave(template); // 需要实现保存逻辑
  };

  const canProceed = () => {
    const values = form.getFieldsValue();
    switch (currentStep) {
      case 0:
        return values.name && values.description && values.type;
      case 1:
        return selectedOperators.length > 0;
      default:
        return false;
    }
  };

  const handleValuesChange = (_, allValues) => {
    setTemplateConfig({ ...templateConfig, ...allValues });
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Form
            form={form}
            layout="vertical"
            initialValues={templateConfig}
            onValuesChange={handleValuesChange}
          >
            <Form.Item
              label="模板名称"
              name="name"
              rules={[{ required: true, message: "请输入模板名称" }]}
            >
              <Input placeholder="输入模板名称" size="large" />
            </Form.Item>
            <Form.Item label="模板描述" name="description">
              <TextArea placeholder="描述模板的用途和特点" rows={4} />
            </Form.Item>
            <Form.Item
              label="模板类型"
              name="type"
              rules={[{ required: true, message: "请选择模板类型" }]}
            >
              <RadioCard
                options={templateTypes}
                value={templateConfig.type}
                onChange={(type) =>
                  setTemplateConfig({ ...templateConfig, type })
                }
              />
            </Form.Item>
          </Form>
        );
      case 1:
        return (
          <OperatorOrchestrationPage
            handleAdd={addOperator}
            handleRemove={removeOperator}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Link to="/data/cleansing">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold">创建清洗模板</h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            current={currentStep}
            items={[{ title: "基本信息" }, { title: "算子编排" }]}
          />
        </div>
      </div>

      {/* Progress Steps */}
      <Card>
        {renderStepContent()}
        <Divider />
        <div className="w-full mt-8 flex justify-end border-t pt-6 gap-4">
          <Button onClick={() => navigate("/data/cleansing")}>取消</Button>
          {currentStep > 0 && <Button onClick={handlePrev}>上一步</Button>}
          {currentStep === 1 ? (
            <Button
              type="primary"
              onClick={handleSave}
              disabled={!canProceed()}
            >
              创建模板
            </Button>
          ) : (
            <Button
              type="primary"
              onClick={handleNext}
              disabled={!canProceed()}
            >
              下一步
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}
