import { useState } from "react";
import { Steps, Button, message, Form } from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { createCleaningTaskUsingPost } from "../cleansing.api";
import CreateTaskStepOne from "./components/CreateTaskStepOne";
import { useCreateStepTwo } from "./hooks/useCreateStepTwo";
import { DatasetType } from "@/pages/DataManagement/dataset.model";

export default function CleansingTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [taskConfig, setTaskConfig] = useState({
    name: "",
    description: "",
    srcDatasetId: "",
    srcDatasetName: "",
    destDatasetName: "",
    destDatasetType: DatasetType.TEXT,
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
      instance: selectedOperators.map((item) => ({
        id: item.id,
        overrides: {
          ...item.defaultParams,
          ...item.overrides,
        },
        categories: item.categories,
        inputs: item.inputs,
        outputs: item.outputs,
      })),
    };
    await createCleaningTaskUsingPost(task);
    message.success("任务已创建");
    navigate("/data/cleansing?view=task");
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Link to="/data/cleansing">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold">创建任务</h1>
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
      <div className="flex-overflow-auto bg-white border-card">
        <div className="flex-1 overflow-auto m-6">{renderStepContent()}</div>
        <div className="flex justify-end p-6 gap-3 border-top">
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
      </div>
    </div>
  );
}
