import RadioCard from "@/components/RadioCard";
import { Input, Select, Form } from "antd";
import { datasetTypes } from "../../dataset.const";
import { useEffect, useState } from "react";
import { queryDatasetTagsUsingGet } from "../../dataset.api";

export default function BasicInformation({
  data,
  setData,
  hidden = [],
}: {
  data: any;
  setData: any;
  hidden?: string[];
}) {
  const [tagOptions, setTagOptions] = useState<
    {
      label: JSX.Element;
      title: string;
      options: { label: JSX.Element; value: string }[];
    }[]
  >([]);

  // 获取标签
  const fetchTags = async () => {
    if (hidden.includes("tags")) return;
    try {
      const { data } = await queryDatasetTagsUsingGet();
      const customTags = data.map((tag) => ({
        label: tag.name,
        value: tag.name,
      }));
      setTagOptions(customTags);
    } catch (error) {
      console.error("Error fetching tags: ", error);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);
  return (
    <>
      <Form.Item
        label="名称"
        name="name"
        rules={[{ required: true, message: "请输入数据集名称" }]}
      >
        <Input placeholder="输入数据集名称" />
      </Form.Item>
      {!hidden.includes("description") && (
        <Form.Item name="description" label="描述">
          <Input.TextArea placeholder="描述数据集的用途和内容" rows={3} />
        </Form.Item>
      )}

      {/* 数据集类型选择 - 使用卡片形式 */}
      {!hidden.includes("datasetType") && (
        <Form.Item
          label="类型"
          name="datasetType"
          rules={[{ required: true, message: "请选择数据集类型" }]}
        >
          <RadioCard
            options={datasetTypes}
            value={data.type}
            onChange={(datasetType) => setData({ ...data, datasetType })}
          />
        </Form.Item>
      )}
      {!hidden.includes("tags") && (
        <Form.Item label="标签" name="tags">
          <Select
            className="w-full"
            mode="tags"
            options={tagOptions}
            placeholder="请选择标签"
          />
        </Form.Item>
      )}
    </>
  );
}
