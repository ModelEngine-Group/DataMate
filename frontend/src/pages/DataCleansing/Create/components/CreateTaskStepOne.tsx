import RadioCard from "@/components/RadioCard";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { getDatasetTypeMap, mapDataset } from "@/pages/DataManagement/dataset.const";
import {
  Dataset,
  DatasetSubType,
  DatasetType,
} from "@/pages/DataManagement/dataset.model";
import { Input, Select, Form, AutoComplete } from "antd";
import TextArea from "antd/es/input/TextArea";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

export default function CreateTaskStepOne({
  form,
  taskConfig,
  setTaskConfig,
}: {
  form: any;
  taskConfig: {
    name: string;
    description: string;
    datasetId: string;
    destDatasetName: string;
    type: DatasetType;
    destDatasetType: DatasetSubType;
  };
  setTaskConfig: (config: any) => void;
}) {
  const { t } = useTranslation();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const datasetTypes = [...Object.values(getDatasetTypeMap(t))];

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 1, size: 1000 });
    setDatasets(data.content.map(dataset => mapDataset(dataset, t)) || []);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleValuesChange = (currentValue, allValues) => {
    const [key, value] = Object.entries(currentValue)[0];
    let dataset = null;
    if (key === "srcDatasetId") {
      dataset = datasets.find((d) => d.id === value);
      setTaskConfig({
        ...taskConfig,
        ...allValues,
        srcDatasetName: dataset?.name || "",
      });
    } else if (key === "destDatasetName") {
      dataset = datasets.find((d) => d.name === value);
      setTaskConfig({
        ...taskConfig,
        ...allValues,
        destDatasetId: dataset?.id || "",
      });
    } else {
      setTaskConfig({ ...taskConfig, ...allValues });
    }
  };

  return (
    <Form
      layout="vertical"
      form={form}
      initialValues={taskConfig}
      onValuesChange={handleValuesChange}
    >
      <h2 className="font-medium text-gray-900 text-base mb-2">{t("dataCleansing.task.sections.taskInfo")}</h2>
      <Form.Item label={t("dataCleansing.task.form.name")} name="name" required>
        <Input placeholder={t("dataCleansing.task.form.namePlaceholder")} />
      </Form.Item>
      <Form.Item label={t("dataCleansing.task.form.description")} name="description">
        <TextArea placeholder={t("dataCleansing.task.form.descriptionPlaceholder")} rows={4} />
      </Form.Item>
      <h2 className="font-medium text-gray-900 pt-6 mb-2 text-base">
        {t("dataCleansing.task.sections.dataSourceSelection")}
      </h2>
      <Form.Item label={t("dataCleansing.task.form.srcDataset")} name="srcDatasetId" required>
        <Select
          placeholder={t("dataCleansing.task.form.srcDatasetPlaceholder")}
          options={datasets.map((dataset) => {
            return {
              label: (
                <div className="flex items-center justify-between gap-3 py-2">
                  <div className="flex items-center font-sm text-gray-900">
                    <span className="mr-2">{dataset.icon}</span>
                    <span>{dataset.name}</span>
                  </div>
                  <div className="text-xs text-gray-500">{dataset.size}</div>
                </div>
              ),
              value: dataset.id,
            };
          })}
        />
      </Form.Item>
      <Form.Item label={t("dataCleansing.task.form.destDatasetName")} name="destDatasetName" required>
        <AutoComplete
          options={datasets.map((dataset) => {
            return {
              label: (
                <div className="flex items-center justify-between gap-3 py-2">
                  <div className="flex items-center font-sm text-gray-900">
                    <span className="mr-2">{dataset.icon}</span>
                    <span>{dataset.name}</span>
                  </div>
                  <div className="text-xs text-gray-500">{dataset.size}</div>
                </div>
              ),
              value: dataset.name,
            };
          })}
          filterOption={(inputValue, option) => {
            return option.value.toLowerCase().startsWith(inputValue.toLowerCase());
          }}
          placeholder={t("dataCleansing.task.form.destDatasetNamePlaceholder")}
        />
      </Form.Item>
      <Form.Item
        label={t("dataCleansing.task.form.destDatasetType")}
        name="destDatasetType"
        rules={[{ required: true, message: t("dataCleansing.task.form.destDatasetTypeRequired") }]}
      >
        <RadioCard
          options={datasetTypes}
          value={taskConfig.destDatasetType}
          onChange={(type) => {
            form.setFieldValue("destDatasetType", type);
            setTaskConfig({
              ...taskConfig,
              destDatasetType: type as DatasetSubType,
            });
          }}
        />
      </Form.Item>
    </Form>
  );
}
