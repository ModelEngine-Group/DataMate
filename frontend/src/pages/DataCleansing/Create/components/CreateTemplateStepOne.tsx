import { Input, Form } from "antd";

const { TextArea } = Input;

export default function CreateTemplateStepOne({
  form,
  templateConfig,
  setTemplateConfig,
}: {
  form: any;
  templateConfig: { name: string; description: string; type: string };
  setTemplateConfig: React.Dispatch<
    React.SetStateAction<{ name: string; description: string; type: string }>
  >;
}) {
  const handleValuesChange = (_, allValues) => {
    setTemplateConfig({ ...templateConfig, ...allValues });
  };
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
    </Form>
  );
}
