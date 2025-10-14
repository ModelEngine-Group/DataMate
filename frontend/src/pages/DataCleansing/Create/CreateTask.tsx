import { useState } from "react";
import { Card, Steps, Button, message } from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import OperatorLibrary from "./components/OperatorLibrary";
import OperatorOrchestration from "./components/OperatorOrchestration";
import OperatorConfig from "./components/OperatorConfig";
import { useDragOperators } from "./hooks/useDragOperators";
import { useOperatorOperations } from "./hooks/useOperatorOperations";
import { createCleaningTaskUsingPost } from "../cleansing.api";
import CleansingTaskStepOne from "./components/StepOne";

export default function CleansingTaskCreate() {
  const navigate = useNavigate();
  const [taskConfig, setTaskConfig] = useState({
    name: "",
    description: "",
    datasetId: "",
    newDatasetName: "",
    priority: "normal",
    batchSize: "100",
    keepOriginal: true,
    generateReport: true,
    autoBackup: false,
  });

  const {
    operators,
    selectedOperators,
    currentStep,
    templates,
    currentTemplate,
    configOperator,
    setCurrentTemplate,
    setConfigOperator,
    setSelectedOperators,
    handleConfigChange,
    toggleOperator,
    removeOperator,
    handleNext,
    handlePrev,
  } = useOperatorOperations();

  const {
    handleDragStart,
    handleDragEnd,
    handleContainerDragOver,
    handleContainerDragLeave,
    handleItemDragOver,
    handleItemDragLeave,
    handleItemDrop,
    handleDropToContainer,
  } = useDragOperators({
    operators: selectedOperators,
    setOperators: setSelectedOperators,
  });

  const handleSave = async () => {
    const task = {
      ...taskConfig,
      operators: selectedOperators,
      createdAt: new Date().toISOString(),
    };
    console.log("创建任务:", task);
    navigate("/data/cleansing");
    await createCleaningTaskUsingPost(task);
    message.success("任务已创建");
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return (
          taskConfig.name && taskConfig.datasetId && taskConfig.newDatasetName
        );
      case 2:
        return operators.length > 0;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <CleansingTaskStepOne
            taskConfig={taskConfig}
            setTaskConfig={setTaskConfig}
          />
        );
      case 2:
        return (
          <div className="flex w-full h-full">
            {/* 左侧算子库 */}
            <OperatorLibrary
              selectedOperators={selectedOperators}
              operatorList={operators}
              toggleOperator={toggleOperator}
              handleDragStart={handleDragStart}
            />

            {/* 中间算子编排区域 */}
            <OperatorOrchestration
              selectedOperators={selectedOperators}
              configOperator={configOperator}
              templates={templates}
              currentTemplate={currentTemplate}
              setSelectedOperators={setSelectedOperators}
              setConfigOperator={setConfigOperator}
              setCurrentTemplate={setCurrentTemplate}
              removeOperator={removeOperator}
              handleDragStart={handleDragStart}
              handleContainerDragLeave={handleContainerDragLeave}
              handleContainerDragOver={handleContainerDragOver}
              handleItemDragOver={handleItemDragOver}
              handleItemDragLeave={handleItemDragLeave}
              handleItemDrop={handleItemDrop}
              handleDropToContainer={handleDropToContainer}
              handleDragEnd={handleDragEnd}
            />

            {/* 右侧参数配置面板 */}
            <OperatorConfig
              selectedOp={configOperator}
              handleConfigChange={handleConfigChange}
            />
          </div>
        );
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
