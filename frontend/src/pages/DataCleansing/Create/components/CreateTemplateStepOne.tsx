import RadioCard from "@/components/RadioCard";
import { templateTypes } from "@/mock/cleansing";
import { Input, Form } from "antd";

const { TextArea } = Input;

export default function CreateTemplateStepOne({
  form,
  templateConfig,
  setTemplateConfig,
  handleValuesChange,
}) {
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
          onChange={(type) => setTemplateConfig({ ...templateConfig, type })}
        />
      </Form.Item>
    </Form>
  );
}
