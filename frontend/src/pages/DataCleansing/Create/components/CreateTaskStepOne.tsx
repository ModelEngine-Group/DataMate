import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { datasetSubTypeMap } from "@/pages/DataManagement/dataset.const";
import { Input, Select, Form } from "antd";
import TextArea from "antd/es/input/TextArea";
import { Database } from "lucide-react";
import { useEffect, useState } from "react";

export default function CreateTaskStepOne({ taskConfig, setTaskConfig }) {
  const [datasets, setDatasets] = useState<any[]>([]);
  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 0, size: 1000 });
    setDatasets(data.content || []);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  return (
    <Form layout="vertical">
      <h2 className="font-medium text-gray-900 text-lg mb-2">任务信息</h2>
      <Form.Item label="任务名称" required>
        <Input
          value={taskConfig.name}
          onChange={(e) =>
            setTaskConfig({ ...taskConfig, name: e.target.value })
          }
          placeholder="输入清洗任务名称"
        />
      </Form.Item>
      <Form.Item label="任务描述">
        <TextArea
          value={taskConfig.description}
          onChange={(e) =>
            setTaskConfig({ ...taskConfig, description: e.target.value })
          }
          placeholder="描述清洗任务的目标和要求"
          rows={4}
        />
      </Form.Item>
      <h2 className="font-medium text-gray-900 mt-4 mb-2 text-lg">
        数据源选择
      </h2>
      <Form.Item label="源数据集" required>
        <Select
          value={taskConfig.datasetId}
          onChange={(value) =>
            setTaskConfig({ ...taskConfig, datasetId: value })
          }
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
                  {datasetSubTypeMap[dataset.type]?.label}
                </div>
              </div>
            ),
            value: dataset.id,
          }))}
        />
      </Form.Item>
      <Form.Item label="目标数据集名称" required>
        <Input
          value={taskConfig.newDatasetName}
          onChange={(e) =>
            setTaskConfig({
              ...taskConfig,
              newDatasetName: e.target.value,
            })
          }
          placeholder="输入目标数据集名称"
        />
      </Form.Item>
    </Form>
  );
}
