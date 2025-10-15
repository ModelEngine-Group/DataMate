import RadioCard from "@/components/RadioCard";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import {
  datasetSubTypeMap,
  datasetTypes,
} from "@/pages/DataManagement/dataset.const";
import {
  Dataset,
  DatasetSubType,
  DatasetType,
} from "@/pages/DataManagement/dataset.model";
import { Input, Select, Form, Radio } from "antd";
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
    targetDatasetName: string;
    type: DatasetType;
    targetDatasetType: DatasetSubType;
  };
  setTaskConfig: (config: any) => void;
}) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 0, size: 1000 });
    setDatasets(data.content || []);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const targetDatasetTypeOptions = useMemo(() => {
    const options =
      datasetTypes.find((item) => item.value === taskConfig?.type)?.options ??
      [];

    return options;
  }, [taskConfig?.type]);

  return (
    <Form
      layout="vertical"
      form={form}
      initialValues={taskConfig}
      onValuesChange={(_, values) =>
        setTaskConfig({ ...taskConfig, ...values })
      }
    >
      <h2 className="font-medium text-gray-900 text-lg mb-2">任务信息</h2>
      <Form.Item label="任务名称" name="name" required>
        <Input placeholder="输入清洗任务名称" />
      </Form.Item>
      <Form.Item label="任务描述" name="description">
        <TextArea placeholder="描述清洗任务的目标和要求" rows={4} />
      </Form.Item>
      <h2 className="font-medium text-gray-900 mt-4 mb-2 text-lg">
        数据源选择
      </h2>
      <Form.Item label="源数据集" name="srcDatasetId" required>
        <Select
          placeholder="请选择数据集"
          options={datasets.map((dataset) => ({
            label: (
              <div className="flex items-center justify-between gap-3 py-2">
                <div className="flex items-center font-sm text-gray-900">
                  <span>
                    {dataset.icon || <Database className="w-4 h-4 mr-2" />}
                  </span>
                  <span>{dataset.name}</span>
                </div>
                <div className="text-xs text-gray-500">
                  {datasetSubTypeMap[dataset?.type]?.label}
                </div>
              </div>
            ),
            value: dataset.id,
          }))}
        />
      </Form.Item>
      <Form.Item label="目标数据集名称" name="targetDatasetName" required>
        <Input placeholder="输入目标数据集名称" />
      </Form.Item>
      <Form.Item
        label="目标数据类型"
        name="type"
        rules={[{ required: true, message: "请选择目标数据类型" }]}
      >
        <Radio.Group
          buttonStyle="solid"
          options={datasetTypes}
          optionType="button"
        />
      </Form.Item>
      <Form.Item
        name="targetDatasetType"
        rules={[{ required: true, message: "请选择目标数据类型" }]}
      >
        <RadioCard
          options={targetDatasetTypeOptions}
          value={taskConfig.targetDatasetType}
          onChange={(type) => {
            form.setFieldValue("targetDatasetType", type);
            setTaskConfig({
              ...taskConfig,
              targetDatasetType: type as DatasetSubType,
            });
          }}
        />
      </Form.Item>
    </Form>
  );
}
