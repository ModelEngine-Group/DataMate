import { useState } from "react";
import { Card, Button, Input, Steps, Form, Divider } from "antd";
import { Link, useNavigate } from "react-router";
import RadioCard from "@/components/RadioCard";

import { ArrowLeft } from "lucide-react";
import OperatorLibrary from "./components/OperatorLibrary";
import OperatorOrchestration from "./components/OperatorOrchestration";
import OperatorConfig from "./components/OperatorConfig";
import { templateTypes, OPERATOR_CATEGORIES } from "@/mock/cleansing";
import { createCleaningTemplateUsingPost } from "../cleansing.api";
import { useDragOperators } from "./hooks/useDragOperators";
import { useOperatorOperations } from "./hooks/useOperatorOperations";

const { TextArea } = Input;

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
      operators,
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
    templates,
    operators,
    currentTemplate,
    currentStep,
    setCurrentTemplate,
    setOperators,
    selectedOperator,
    setSelectedOperator,
    toggleOperator,
    removeOperator,
    handleNext,
    handlePrev,
  } = useOperatorOperations();

  const canProceed = () => {
    const values = form.getFieldsValue();
    switch (currentStep) {
      case 0:
        return values.name && values.type;
      case 1:
        return operators.length > 0;
      default:
        return false;
    }
  };

  const {
    handleDragStart,
    handleDragEnd,
    handleContainerDragOver,
    handleContainerDragLeave,
    handleItemDragOver,
    handleItemDragLeave,
    handleItemDrop,
    handleDropToContainer,
  } = useDragOperators({ operators, setOperators });

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
              <Input placeholder="输入模板名称" />
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
          <div className="flex w-full h-full">
            {/* 左侧算子库 */}
            <OperatorLibrary
              operators={operators}
              operatorList={currentTemplate?.instance || []}
              OPERATOR_CATEGORIES={OPERATOR_CATEGORIES}
              toggleOperator={toggleOperator}
              handleDragStart={handleDragStart}
            />

            {/* 中间算子编排区域 */}
            <OperatorOrchestration
              templates={templates}
              currentTemplate={currentTemplate}
              setCurrentTemplate={setCurrentTemplate}
              operators={operators}
              setOperators={setOperators}
              OPERATOR_CATEGORIES={OPERATOR_CATEGORIES}
              selectedOperator={selectedOperator}
              setSelectedOperator={setSelectedOperator}
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
              selectedOp={operators.find((op) => op.id === selectedOperator)}
            />
          </div>
        );
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
        </div>
      </Card>
    </div>
  );
}
