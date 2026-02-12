import { useState, useRef } from "react";
import {
  Card,
  Select,
  Input,
  Button,
  Badge,
  Divider,
  Form,
  message,
} from "antd";
import { Plus, ArrowLeft, Play, Save, RefreshCw, Code, X } from "lucide-react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { mockTemplates } from "@/mock/annotation";

const { TextArea } = Input;

export default function InstructionTemplateCreate() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [isTestingTemplate, setIsTestingTemplate] = useState(false);
  const [templates, setTemplates] = useState<Template[]>(mockTemplates);
  const [variables, setVariables] = useState<string[]>([]);
  const variableInputRef = useRef<Input | null>(null);

  const [form] = Form.useForm();

  // 初始化表单数据
  const initialValues = selectedTemplate
    ? {
        name: selectedTemplate.name,
        category: selectedTemplate.category,
        prompt: selectedTemplate.prompt,
        description: selectedTemplate.description,
        testInput: "",
        testOutput: "",
      }
    : {
        name: "",
        category: "",
        prompt: "",
        description: "",
        testInput: "",
        testOutput: "",
      };

  // 变量同步
  const handlePromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    form.setFieldValue("prompt", value);
    // 自动提取变量
    const matches = Array.from(value.matchAll(/\{(\w+)\}/g)).map((m) => m[1]);
    setVariables(Array.from(new Set(matches)));
  };

  // 添加变量（手动）
  const handleAddVariable = () => {
    const input = variableInputRef.current?.input;
    const value = input?.value.trim();
    if (value && !variables.includes(value)) {
      setVariables([...variables, value]);
      input.value = "";
    }
  };

  // 删除变量
  const handleRemoveVariable = (index: number) => {
    setVariables(variables.filter((_, i) => i !== index));
  };

  // 测试模板
  const handleTestTemplate = async () => {
    const values = form.getFieldsValue();
    if (!values.prompt || !values.testInput) return;
    setIsTestingTemplate(true);
    setTimeout(() => {
      form.setFieldValue(
        "testOutput",
        t('synthesisTask.createTemplate.messages.testOutput', { input: values.testInput })
      );
      setIsTestingTemplate(false);
    }, 2000);
  };

  // 保存模板
  const handleSaveTemplate = async () => {
    try {
      const values = await form.validateFields();
      if (!values.name || !values.prompt || !values.category) return;
      if (selectedTemplate) {
        setTemplates((prev) =>
          prev.map((t) =>
            t.id === selectedTemplate.id
              ? {
                  ...t,
                  ...values,
                  variables,
                  type: "custom" as const,
                  usageCount: t.usageCount,
                  lastUsed: new Date().toISOString().split("T")[0],
                }
              : t
          )
        );
      } else {
        const newTemplate: Template = {
          id: Date.now(),
          ...values,
          variables,
          type: "custom",
          usageCount: 0,
          quality: 85,
        };
        setTemplates([newTemplate, ...templates]);
      }
      message.success(t('synthesisTask.createTemplate.messages.saved'));
      navigate("/data/synthesis/task");
    } catch {
      // 校验失败
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Button onClick={() => navigate("/data/synthesis/task")} type="text">
            <ArrowLeft className="w-4 h-4 mr-2" />
          </Button>
          <h1 className="text-xl font-bold bg-clip-text">
            {selectedTemplate ? t('synthesisTask.createTemplate.editTitle') : t('synthesisTask.createTemplate.title')}
          </h1>
        </div>
      </div>
      <div className="flex-overflow-auto border-card p-4">
        <div className="flex-1 overflow-auto">
          <Form
            form={form}
            layout="vertical"
            initialValues={initialValues}
            autoComplete="off"
          >
            <h2 className="font-medium text-gray-900 text-lg mb-2">{t('synthesisTask.createTemplate.form.basicInfo')}</h2>
            <div className="grid grid-cols-2 gap-4">
              <Form.Item
                label={t('synthesisTask.createTemplate.form.name')}
                name="name"
                rules={[{ required: true, message: t('synthesisTask.createTemplate.form.nameRequired') }]}
              >
                <Input placeholder={t('synthesisTask.createTemplate.form.namePlaceholder')} />
              </Form.Item>
              <Form.Item
                label={t('synthesisTask.createTemplate.form.category')}
                name="category"
                rules={[{ required: true, message: t('synthesisTask.createTemplate.form.categoryRequired') }]}
              >
                <Select
                  placeholder={t('synthesisTask.createTemplate.form.categoryPlaceholder')}
                  options={[
                    { label: t('synthesisTask.createTemplate.categories.qa'), value: "qa" },
                    { label: t('synthesisTask.createTemplate.categories.distillation'), value: "distillation" },
                    { label: t('synthesisTask.createTemplate.categories.textGeneration'), value: "textGeneration" },
                    { label: t('synthesisTask.createTemplate.categories.multimodal'), value: "multimodal" },
                  ]}
                />
              </Form.Item>
            </div>
            <Form.Item label={t('synthesisTask.createTemplate.form.description')} name="description">
              <Input placeholder={t('synthesisTask.createTemplate.form.descriptionPlaceholder')} />
            </Form.Item>
            <h2 className="font-medium text-gray-900 text-lg mt-6 mb-2">
              {t('synthesisTask.createTemplate.form.promptContent')}
            </h2>
            <Form.Item
              label={t('synthesisTask.createTemplate.form.promptContent')}
              name="prompt"
              rules={[{ required: true, message: t('synthesisTask.createTemplate.form.promptRequired') }]}
            >
              <TextArea
                placeholder={t('synthesisTask.createTemplate.form.promptPlaceholder')}
                rows={10}
                className="font-mono text-xs resize-none"
                onChange={handlePromptChange}
              />
            </Form.Item>
            <p className="text-xs text-gray-500 mb-2">
              {t('synthesisTask.createTemplate.form.promptHint')}
            </p>
            <div className="mb-4">
              <span className="text-sm font-semibold text-gray-700">
                {t('synthesisTask.createTemplate.variables.title')}
              </span>
              <div className="flex flex-wrap gap-2 min-h-[50px] p-3 border rounded-xl bg-gray-50 mt-2">
                {variables.map((variable, index) => (
                  <Badge
                    key={index}
                    count={
                      <X
                        className="w-3 h-3 cursor-pointer"
                        onClick={() => handleRemoveVariable(index)}
                      />
                    }
                    style={{ backgroundColor: "#fff" }}
                  >
                    <span className="flex items-center gap-1 px-2 py-1 text-xs">
                      <Code className="w-3 h-3" />
                      {variable}
                    </span>
                  </Badge>
                ))}
                {variables.length === 0 && (
                  <span className="text-xs text-gray-400">
                    {t('synthesisTask.createTemplate.variables.empty')}
                  </span>
                )}
              </div>
              <div className="flex gap-2 mt-2">
                <Input
                  ref={variableInputRef}
                  placeholder={t('synthesisTask.createTemplate.variables.addPlaceholder')}
                  className="h-8 text-sm"
                  onPressEnter={handleAddVariable}
                />
                <Button
                  onClick={handleAddVariable}
                  type="default"
                  className="px-4 text-sm"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  {t('synthesisTask.createTemplate.variables.add')}
                </Button>
              </div>
            </div>
            <h2 className="font-medium text-gray-900 text-lg mb-2 pt-2">
              {t('synthesisTask.createTemplate.test.title')}
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <Form.Item label={t('synthesisTask.createTemplate.form.testInput')} name="testInput">
                <TextArea
                  placeholder={t('synthesisTask.createTemplate.form.testInputPlaceholder')}
                  rows={5}
                  className="resize-none text-sm"
                />
              </Form.Item>
              <Form.Item label={t('synthesisTask.createTemplate.form.testOutput')} name="testOutput">
                <TextArea
                  readOnly
                  placeholder={t('synthesisTask.createTemplate.form.testOutputPlaceholder')}
                  rows={5}
                  className="resize-none bg-gray-50 text-sm"
                />
              </Form.Item>
            </div>
            <Button
              onClick={handleTestTemplate}
              disabled={
                !form.getFieldValue("prompt") ||
                !form.getFieldValue("testInput") ||
                isTestingTemplate
              }
              type="default"
              className="px-4 py-2 text-sm"
            >
              {isTestingTemplate ? (
                <>
                  <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                  {t('synthesisTask.createTemplate.test.testing')}
                </>
              ) : (
                <>{t('synthesisTask.createTemplate.test.testButton')}</>
              )}
            </Button>
          </Form>
        </div>
        <div className="flex gap-2 justify-end p-4 border-top">
          <Button
            type="primary"
            onClick={handleSaveTemplate}
            disabled={
              !form.getFieldValue("name") ||
              !form.getFieldValue("prompt") ||
              !form.getFieldValue("category")
            }
            className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
          >
            <Save className="w-3 h-3 mr-1" />
            {t('synthesisTask.createTemplate.actions.saveTemplate')}
          </Button>
          <Button
            onClick={() => navigate("/data/synthesis/task")}
            type="default"
            className="px-4 py-2 text-sm"
          >
            {t('synthesisTask.createTemplate.actions.cancel')}
          </Button>
        </div>
      </div>
    </div>
  );
}
