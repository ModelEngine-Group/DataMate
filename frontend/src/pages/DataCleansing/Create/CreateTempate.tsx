import { useState } from "react";
import { Card, Button, Steps, Form, Divider } from "antd";
import { Link, useNavigate } from "react-router";

import { ArrowLeft } from "lucide-react";
import { createCleaningTemplateUsingPost } from "../cleansing.api";
import CleansingTemplateStepOne from "./components/CreateTemplateStepOne";
import { useCreateStepTwo } from "./hooks/useCreateStepTwo";

export default function CleansingTemplateCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [templateConfig, setTemplateConfig] = useState({
    name: "",
    description: "",
    type: "",
  });

  const handleSave = async () => {
    const values = form.getFieldsValue();
    const template = {
      ...values,
      ...templateConfig,
      operators: selectedOperators,
      createdAt: new Date().toISOString(),
    };
    console.log("保存模板数据:", template);
    await createCleaningTemplateUsingPost(template);
    navigate("/data/cleansing");
  };

  const handleValuesChange = (_, allValues) => {
    setTemplateConfig({ ...templateConfig, ...allValues });
  };

  const {
    renderStepTwo,
    selectedOperators,
    currentStep,
    handlePrev,
    handleNext,
  } = useCreateStepTwo();

  const canProceed = () => {
    const values = form.getFieldsValue();
    switch (currentStep) {
      case 1:
        return values.name && values.type;
      case 2:
        return selectedOperators.length > 0;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <CleansingTemplateStepOne
            form={form}
            handleValuesChange={handleValuesChange}
            templateConfig={templateConfig}
            setTemplateConfig={setTemplateConfig}
          />
        );
      case 2:
        return renderStepTwo;
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col flex-1">
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

      <Card className="h-full flex flex-col justify-between flex-1 overflow-auto">
        <div className="flex-1">{renderStepContent()}</div>
        <div className="flex-end">
          <Divider />
          <div className="w-full mt-4 flex justify-end gap-4">
            <Button onClick={() => navigate("/data/cleansing")}>取消</Button>
            {currentStep > 1 && <Button onClick={handlePrev}>上一步</Button>}
            {currentStep === 2 ? (
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
        </div>
      </Card>
    </div>
  );
}
