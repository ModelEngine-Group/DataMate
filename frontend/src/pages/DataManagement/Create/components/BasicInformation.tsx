import RadioCard from "@/components/RadioCard";
import { Input, Select, Form } from "antd";
import { getDatasetTypes } from "../../dataset.const";
import { useEffect, useState } from "react";
import { queryDatasetTagsUsingGet } from "../../dataset.api";
import {queryTasksUsingGet} from "@/pages/DataCollection/collection.apis.ts";
import { useTranslation } from "react-i18next";

export default function BasicInformation({
  data,
  setData,
  hidden = [],
}: {
  data: any;
  setData: any;
  hidden?: string[];
}) {
  const { t } = useTranslation();
  const datasetTypes = getDatasetTypes(t);
  const [tagOptions, setTagOptions] = useState<
    {
      label: JSX.Element;
      title: string;
      options: { label: JSX.Element; value: string }[];
    }[]
  >([]);
  const [collectionOptions, setCollectionOptions] = useState([]);

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

  // 获取归集任务
  const fetchCollectionTasks = async () => {
    try {
      const res = await queryTasksUsingGet({ page: 0, size: 100 });
      const options = res.data.content.map((task: any) => ({
        label: task.name,
        value: task.id,
      }));
      setCollectionOptions(options);
    } catch (error) {
      console.error("Error fetching collection tasks:", error);
    }
  };

  useEffect(() => {
    fetchTags();
    fetchCollectionTasks();
  }, []);
  return (
    <>
      <Form.Item
        label={t("dataManagement.formLabels.name")}
        name="name"
        rules={[{ required: true, message: t("dataManagement.validation.nameRequired") }]}
      >
        <Input placeholder={t("dataManagement.placeholders.datasetName")} />
      </Form.Item>
      {!hidden.includes("description") && (
        <Form.Item name="description" label={t("dataManagement.formLabels.description")}>
          <Input.TextArea
            placeholder={t("dataManagement.placeholders.datasetDescription")}
            rows={3}
          />
        </Form.Item>
      )}

      {/* 数据集类型选择 - 使用卡片形式 */}
      {!hidden.includes("datasetType") && (
        <Form.Item
          label={t("dataManagement.formLabels.type")}
          name="datasetType"
          rules={[{ required: true, message: t("dataManagement.validation.typeRequired") }]}
        >
          <RadioCard
            options={datasetTypes}
            value={data.type}
            onChange={(datasetType) => setData({ ...data, datasetType })}
          />
        </Form.Item>
      )}
      {!hidden.includes("tags") && (
        <Form.Item label={t("dataManagement.formLabels.tags")} name="tags">
          <Select
            className="w-full"
            mode="tags"
            options={tagOptions}
            placeholder={t("dataManagement.placeholders.selectTags")}
          />
        </Form.Item>
      )}
      {!hidden.includes("dataSource") && (
        <Form.Item
          name="dataSource"
          label={t("dataManagement.formLabels.collectionTask")}
        >
          <Select
            placeholder={t("dataManagement.placeholders.selectCollectionTask")}
            options={collectionOptions}
          />
        </Form.Item>
      )}
    </>
  );
}
