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
import { mockTemplates } from "@/mock/annotation";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

const { TextArea } = Input;

export default function InstructionTemplateCreate() {
  return <DevelopmentInProgress showTime="2025.11.30" />;
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
        `基于输入"${values.testInput}"生成的测试结果：

这是一个模拟的输出结果，展示了模板的工作效果。在实际使用中，这里会显示AI模型根据您的模板和输入生成的真实结果。

模板变量已正确替换，输出格式符合预期。`
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
      message.success("模板已保存");
      navigate("/data/synthesis/task");
    } catch {
      // 校验失败
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Button onClick={() => navigate("/data/synthesis/task")} type="text">
            <ArrowLeft className="w-4 h-4 mr-2" />
          </Button>
          <h1 className="text-xl font-bold bg-clip-text">
            {selectedTemplate ? "编辑模板" : "创建新模板"}
          </h1>
        </div>
      </div>
      <Card className="overflow-y-auto p-2">
        <Form
          form={form}
          layout="vertical"
          initialValues={initialValues}
          autoComplete="off"
        >
          <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label="模板名称"
              name="name"
              rules={[{ required: true, message: "请输入模板名称" }]}
            >
              <Input placeholder="输入模板名称" />
            </Form.Item>
            <Form.Item
              label="分类"
              name="category"
              rules={[{ required: true, message: "请选择分类" }]}
            >
              <Select
                placeholder="选择分类"
                options={[
                  { label: "问答对生成", value: "问答对生成" },
                  { label: "蒸馏数据集", value: "蒸馏数据集" },
                  { label: "文本生成", value: "文本生成" },
                  { label: "多模态生成", value: "多模态生成" },
                ]}
              />
            </Form.Item>
          </div>
          <Form.Item label="模板描述" name="description">
            <Input placeholder="简要描述模板的用途和特点" />
          </Form.Item>
          <h2 className="font-medium text-gray-900 text-lg mt-6 mb-2">
            Prompt内容
          </h2>
          <Form.Item
            label="Prompt内容"
            name="prompt"
            rules={[{ required: true, message: "请输入Prompt内容" }]}
          >
            <TextArea
              placeholder="输入prompt内容，使用 {变量名} 格式定义变量"
              rows={10}
              className="font-mono text-xs resize-none"
              onChange={handlePromptChange}
            />
          </Form.Item>
          <p className="text-xs text-gray-500 mb-2">
            提示：使用 {"{变量名}"} 格式定义变量，例如 {"{text}"} 或 {"{input}"}
          </p>
          <div className="mb-4">
            <span className="text-sm font-semibold text-gray-700">
              变量管理
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
                  暂无变量，在Prompt中使用 {"{变量名}"} 格式定义
                </span>
              )}
            </div>
            <div className="flex gap-2 mt-2">
              <Input
                ref={variableInputRef}
                placeholder="添加变量名（如：text, input, question）"
                className="h-8 text-sm"
                onPressEnter={handleAddVariable}
              />
              <Button
                onClick={handleAddVariable}
                type="default"
                className="px-4 text-sm"
              >
                <Plus className="w-3 h-3 mr-1" />
                添加
              </Button>
            </div>
          </div>
          <h2 className="font-medium text-gray-900 text-lg mb-2 pt-2">
            模板测试
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item label="测试输入" name="testInput">
              <TextArea
                placeholder="输入测试数据"
                rows={5}
                className="resize-none text-sm"
              />
            </Form.Item>
            <Form.Item label="测试输出" name="testOutput">
              <TextArea
                readOnly
                placeholder="点击测试按钮查看输出结果"
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
                测试中...
              </>
            ) : (
              <>
                <Play className="w-3 h-3 mr-1" />
                测试模板
              </>
            )}
          </Button>
          <Divider />
          <div className="flex gap-2 justify-end">
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
              保存模板
            </Button>
            <Button
              onClick={() => navigate("/data/synthesis/task")}
              type="default"
              className="px-4 py-2 text-sm"
            >
              取消
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
