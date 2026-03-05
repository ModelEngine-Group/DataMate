import RadioCard from "@/components/RadioCard";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { getDatasetTypeMap, mapDataset } from "@/pages/DataManagement/dataset.const";
import {
  Dataset,
  DatasetSubType,
  DatasetType,
} from "@/pages/DataManagement/dataset.model";
import { Input, Select, Form, AutoComplete, Checkbox, Tooltip } from "antd";
import TextArea from "antd/es/input/TextArea";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Lock } from "lucide-react";

export default function CreateTaskStepOne({
  form,
  taskConfig,
  setTaskConfig,
  useSourceDataset,
  setUseSourceDataset,
}: {
  form: any;
  taskConfig: {
    name: string;
    description: string;
    datasetId: string;
    destDatasetName: string;
    type: DatasetType;
    destDatasetType: DatasetSubType;
    srcDatasetId?: string;
    srcDatasetName?: string;
  };
  setTaskConfig: (config: any) => void;
  useSourceDataset: boolean;
  setUseSourceDataset: (checked: boolean) => void;
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
      // 如果勾选了"选择源数据集"，自动更新目标数据集名称
      const newDestName = useSourceDataset ? (dataset?.name || "") : allValues.destDatasetName;
      form.setFieldValue("destDatasetName", newDestName);
      setTaskConfig({
        ...taskConfig,
        ...allValues,
        srcDatasetName: dataset?.name || "",
        destDatasetName: newDestName,
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

  const handleUseSourceDatasetChange = (checked: boolean) => {
    setUseSourceDataset(checked);
    if (checked) {
      const srcDatasetId = form.getFieldValue("srcDatasetId");
      const srcDataset = datasets.find((d) => d.id === srcDatasetId);
      const srcName = srcDataset?.name || "";
      form.setFieldValue("destDatasetName", srcName);
      setTaskConfig({
        ...taskConfig,
        destDatasetName: srcName,
      });
    } else {
      form.setFieldValue("destDatasetName", "");
      setTaskConfig({
        ...taskConfig,
        destDatasetName: "",
      });
    }
  };

  // 过滤掉当前选中的源数据集（当不勾选"选择源数据集"时）
  const getFilteredDatasetOptions = () => {
    const srcDatasetId = form.getFieldValue("srcDatasetId");
    if (useSourceDataset || !srcDatasetId) {
      return datasets;
    }
    return datasets.filter((d) => d.id !== srcDatasetId);
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
      <div className="flex items-center gap-1 mb-1">
        <span className="text-red-500">*</span>
        <label className="text-sm text-gray-700 mr-4">{t("dataCleansing.task.form.destDatasetName")}</label>
        <Checkbox
          checked={useSourceDataset}
          onChange={(e) => handleUseSourceDatasetChange(e.target.checked)}
        >
          <span className="-ml-1">
            {t("dataCleansing.task.form.useSourceDataset")}
          </span>
        </Checkbox>
        {useSourceDataset && (
          <Tooltip title={t("dataCleansing.task.form.useSourceDatasetHint")}>
            <Lock className="w-3.5 h-3.5 text-gray-400 -ml-2.5" />
          </Tooltip>
        )}
      </div>
      <Form.Item 
        name="destDatasetName" 
        className="mb-0"
        rules={[
          { required: true, message: t("dataCleansing.task.form.destDatasetNameRequired") },
          {
            validator: (_, value) => {
              if (useSourceDataset) return Promise.resolve();
              const srcDatasetId = form.getFieldValue("srcDatasetId");
              const srcDataset = datasets.find((d) => d.id === srcDatasetId);
              if (srcDataset && value === srcDataset.name) {
                return Promise.reject(new Error(t("dataCleansing.task.form.cannotUseSourceDataset")));
              }
              return Promise.resolve();
            }
          }
        ]}
      >
        <AutoComplete
          options={getFilteredDatasetOptions().map((dataset) => {
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
          disabled={useSourceDataset}
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
