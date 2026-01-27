import {useEffect, useState} from "react";
import {Button, Steps, Form, message} from "antd";
import {Link, useNavigate, useParams} from "react-router";

import { ArrowLeft } from "lucide-react";
import {
  createCleaningTemplateUsingPost,
  queryCleaningTemplateByIdUsingGet,
  updateCleaningTemplateByIdUsingPut
} from "../cleansing.api";
import CleansingTemplateStepOne from "./components/CreateTemplateStepOne";
import { useCreateStepTwo } from "./hooks/useCreateStepTwo";

export default function CleansingTemplateCreate() {
  const { id = "" } = useParams()
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [templateConfig, setTemplateConfig] = useState({
    name: "",
    description: "",
  });

  const fetchTemplateDetail = async () => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTemplateByIdUsingGet(id);
      setTemplateConfig(data);
    } catch (error) {
      message.error("获取任务详情失败");
      navigate("/data/cleansing");
    }
  };

  useEffect(() => {
    fetchTemplateDetail()
  }, [id]);

  const handleSave = async () => {
    const template = {
      ...templateConfig,
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

    !id && await createCleaningTemplateUsingPost(template) && message.success("模板创建成功");
    id && await updateCleaningTemplateByIdUsingPut(id, template) && message.success("模板更新成功");
    navigate("/data/cleansing?view=template");
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
        return values.name;
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Link to="/data/cleansing">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold">{id ? '更新模板' : '创建模板'}</h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            current={currentStep}
            items={[{ title: "基本信息" }, { title: "算子编排" }]}
          />
        </div>
      </div>

      <div className="flex-overflow-auto border-card">
        <div className="flex-1 overflow-auto m-6">{renderStepContent()}</div>
        <div className="flex justify-end p-6 gap-3 border-top">
          <Button onClick={() => navigate("/data/cleansing")}>取消</Button>
          {currentStep > 1 && <Button onClick={handlePrev}>上一步</Button>}
          {currentStep === 2 ? (
            <Button
              type="primary"
              onClick={handleSave}
              disabled={!canProceed()}
            >
              {id ? '更新模板' : '创建模板'}
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
