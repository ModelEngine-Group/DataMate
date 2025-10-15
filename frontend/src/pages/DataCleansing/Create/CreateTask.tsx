import { useState } from "react";
import { Card, Steps, Button, message, Form } from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { createCleaningTaskUsingPost } from "../cleansing.api";
import CreateTaskStepOne from "./components/CreateTaskStepOne";
import { useCreateStepTwo } from "./hooks/useCreateStepTwo";
import {
  DatasetSubType,
  DatasetType,
} from "@/pages/DataManagement/dataset.model";

export default function CleansingTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [taskConfig, setTaskConfig] = useState({
    name: "",
    description: "",
    srcDatasetId: "",
    destDatasetName: "",
    destDatasetType: DatasetSubType.TEXT_DOCUMENT,
    type: DatasetType.TEXT,
  });

  const {
    renderStepTwo,
    selectedOperators,
    currentStep,
    handlePrev,
    handleNext,
  } = useCreateStepTwo();

  const handleSave = async () => {
    const task = {
      ...taskConfig,
      operators: selectedOperators,
    };
    console.log("创建任务:", task);
    navigate("/data/cleansing");
    await createCleaningTaskUsingPost(task);
    message.success("任务已创建");
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: {
        const values = form.getFieldsValue();
        return (
          values.name &&
          values.srcDatasetId &&
          values.destDatasetName &&
          values.destDatasetType
        );
      }
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
          <CreateTaskStepOne
            form={form}
            taskConfig={taskConfig}
            setTaskConfig={setTaskConfig}
          />
        );
      case 2:
        return renderStepTwo;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Link to="/data/cleansing">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold">创建清洗任务</h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            current={currentStep - 1}
            items={[{ title: "基本信息" }, { title: "算子编排" }]}
          />
        </div>
      </div>
      {/* Step Content */}
      <Card>
        {renderStepContent()}
        <div className="flex justify-end gap-3 mt-8">
          <Button onClick={() => navigate("/data/cleansing")}>取消</Button>
          {currentStep > 1 && <Button onClick={handlePrev}>上一步</Button>}
          {currentStep === 2 ? (
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              disabled={!canProceed()}
            >
              创建任务
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
