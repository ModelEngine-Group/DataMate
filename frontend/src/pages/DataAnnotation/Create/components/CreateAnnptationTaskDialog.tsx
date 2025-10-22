import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import {
  datasetTypeMap,
  mapDataset,
} from "@/pages/DataManagement/dataset.const";
import { Button, Form, Input, Modal, Select } from "antd";
import TextArea from "antd/es/input/TextArea";
import { Database } from "lucide-react";
import { useEffect, useState } from "react";
import { createAnnotationTaskUsingPost } from "../../annotation.api";
import { Dataset } from "@/pages/DataManagement/dataset.model";

export default function CreateAnnotationTask({
  open,
  onClose,
  onRefresh,
}: {
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const [form] = Form.useForm();
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  useEffect(() => {
    if (!open) return;
    const fetchDatasets = async () => {
      const { data } = await queryDatasetsUsingGet({
        page: 0,
        size: 1000,
      });
      setDatasets(data.content.map(mapDataset) || []);
    };
    fetchDatasets();
  }, [open]);

  const handleSubmit = async () => {
    const values = await form.validateFields();
    await createAnnotationTaskUsingPost(values);
    onClose();
    onRefresh();
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="创建标注任务"
      footer={
        <>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={handleSubmit}>
            确定
          </Button>
        </>
      }
    >
      <Form layout="vertical">
        <Form.Item
          label="名称"
          name="name"
          rules={[{ required: true, message: "请输入任务名称" }]}
        >
          <Input placeholder="输入任务名称" />
        </Form.Item>
        <Form.Item
          label="描述"
          name="description"
          rules={[{ required: true, message: "请输入任务描述" }]}
        >
          <TextArea placeholder="详细描述标注任务的要求和目标" rows={3} />
        </Form.Item>
        <Form.Item
          label="数据集"
          name="datasetId"
          rules={[{ required: true, message: "请选择数据集" }]}
        >
          <Select
            placeholder="请选择数据集"
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
      </Form>
    </Modal>
  );
}
