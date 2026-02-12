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
import { useTranslation } from "react-i18next";

export default function CleansingTemplateCreate() {
  const { id = "" } = useParams()
  const navigate = useNavigate();
  const { t } = useTranslation();
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
      message.error(t("dataCleansing.template.messages.templateDetailFailed"));
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

    !id && await createCleaningTemplateUsingPost(template) && message.success(t("dataCleansing.template.messages.templateCreated"));
    id && await updateCleaningTemplateByIdUsingPut(id, template) && message.success(t("dataCleansing.template.messages.templateUpdated"));
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
          <h1 className="text-xl font-bold">{id ? t("dataCleansing.actions.updateTemplate") : t("dataCleansing.actions.createTemplate")}</h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            current={currentStep}
            items={[{ title: t("dataCleansing.steps.basicInfo") }, { title: t("dataCleansing.steps.operatorOrchestration") }]}
          />
        </div>
      </div>

      <div className="flex-overflow-auto border-card">
        <div className="flex-1 overflow-auto m-6">{renderStepContent()}</div>
        <div className="flex justify-end p-6 gap-3 border-top">
          <Button onClick={() => navigate("/data/cleansing")}>{t("dataCleansing.actions.cancel")}</Button>
          {currentStep > 1 && <Button onClick={handlePrev}>{t("dataCleansing.actions.previous")}</Button>}
          {currentStep === 2 ? (
            <Button
              type="primary"
              onClick={handleSave}
              disabled={!canProceed()}
            >
              {id ? t("dataCleansing.actions.updateTemplate") : t("dataCleansing.actions.createTemplate")}
            </Button>
          ) : (
            <Button
              type="primary"
              onClick={handleNext}
              disabled={!canProceed()}
            >
              {t("dataCleansing.actions.next")}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
