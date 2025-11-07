import React from "react";
import { Form, Input } from "antd";

const { TextArea } = Input;

interface BasicInformationProps {
  totalTargetCount: number;
}

const BasicInformation: React.FC<BasicInformationProps> = ({
  totalTargetCount,
}) => {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Form.Item
        label="任务名称"
        name="name"
        rules={[{ required: true, message: "请输入配比任务名称" }]}
      >
        <Input placeholder="输入配比任务名称" />
      </Form.Item>
      <Form.Item
        label="目标总数量"
        name="totalTargetCount"
        rules={[{ required: true, message: "请输入目标总数量" }]}
      >
        <Input type="number" placeholder="目标总数量" min={1} />
      </Form.Item>
      <Form.Item label="任务描述" name="description" className="col-span-2">
        <TextArea placeholder="描述配比任务的目的和要求（可选）" rows={2} />
      </Form.Item>
    </div>
  );
};

export default BasicInformation;
