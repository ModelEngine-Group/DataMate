import RadioCard from "@/components/RadioCard";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import {
  datasetTypeMap,
  datasetTypes,
  mapDataset,
} from "@/pages/DataManagement/dataset.const";
import {
  Dataset,
  DatasetSubType,
  DatasetType,
} from "@/pages/DataManagement/dataset.model";
import { Input, Select, Form } from "antd";
import TextArea from "antd/es/input/TextArea";
import { Database } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

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
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 0, size: 1000 });
    setDatasets(data.content.map(mapDataset) || []);
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
      <h2 className="font-medium text-gray-900 text-base mb-2">任务信息</h2>
      <Form.Item label="名称" name="name" required>
        <Input placeholder="输入清洗任务名称" />
      </Form.Item>
      <Form.Item label="描述" name="description">
        <TextArea placeholder="描述清洗任务的目标和要求" rows={4} />
      </Form.Item>
      <h2 className="font-medium text-gray-900 pt-6 mb-2 text-base">
        数据源选择
      </h2>
      <Form.Item label="源数据集" name="srcDatasetId" required>
        <Select
          placeholder="请选择源数据集"
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
      <Form.Item label="目标数据集名称" name="destDatasetName" required>
        <Input placeholder="输入目标数据集名称" />
      </Form.Item>
      <Form.Item
        label="目标数据集类型"
        name="destDatasetType"
        rules={[{ required: true, message: "请选择目标数据集类型" }]}
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
