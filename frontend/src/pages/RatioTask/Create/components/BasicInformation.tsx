import React from "react";
import { Form, Input } from "antd";
import { useTranslation } from "react-i18next";

const { TextArea } = Input;

interface BasicInformationProps {
  totalTargetCount: number;
}

const BasicInformation: React.FC<BasicInformationProps> = ({
  totalTargetCount,
}) => {
  const { t } = useTranslation();
  return (
    <div className="grid grid-cols-2 gap-2">
      <Form.Item
        label={t("ratioTask.create.basicInfo.nameLabel")}
        name="name"
        rules={[{ required: true, message: t("ratioTask.create.basicInfo.nameRequired") }]}
      >
        <Input placeholder={t("ratioTask.create.basicInfo.namePlaceholder")} />
      </Form.Item>
      <Form.Item
        label={t("ratioTask.create.basicInfo.totalTargetLabel")}
        name="totalTargetCount"
        rules={[{ required: true, message: t("ratioTask.create.basicInfo.totalTargetRequired") }]}
      >
        <Input type="number" placeholder={t("ratioTask.create.basicInfo.totalTargetPlaceholder")} min={1} />
      </Form.Item>
      <Form.Item label={t("ratioTask.create.basicInfo.descriptionLabel")} name="description" className="col-span-2">
        <TextArea placeholder={t("ratioTask.create.basicInfo.descriptionPlaceholder")} rows={2} />
      </Form.Item>
    </div>
  );
};

export default BasicInformation;
