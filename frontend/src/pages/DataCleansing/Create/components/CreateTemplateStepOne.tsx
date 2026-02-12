import { Input, Form } from "antd";
import {useEffect} from "react";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  const handleValuesChange = (_, allValues) => {
    setTemplateConfig({ ...templateConfig, ...allValues });
  };

  useEffect(() => {
    form.setFieldsValue(templateConfig);
  }, [templateConfig]);

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={templateConfig}
      onValuesChange={handleValuesChange}
    >
      <Form.Item
        label={t("dataCleansing.template.form.name")}
        name="name"
        rules={[{ required: true, message: t("dataCleansing.template.form.nameRequired") }]}
      >
        <Input placeholder={t("dataCleansing.template.form.namePlaceholder")} />
      </Form.Item>
      <Form.Item label={t("dataCleansing.template.form.description")} name="description">
        <TextArea placeholder={t("dataCleansing.template.form.descriptionPlaceholder")} rows={4} />
      </Form.Item>
    </Form>
  );
}
