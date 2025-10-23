import { useState } from "react";

import { ArrowLeft } from "lucide-react";
import { Button, Form, App } from "antd";
import { Link, useNavigate } from "react-router";
import { createDatasetUsingPost } from "../dataset.api";
import { DatasetType } from "../dataset.model";
import BasicInformation from "./components/BasicInformation";

export default function DatasetCreate() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [form] = Form.useForm();

  const [newDataset, setNewDataset] = useState({
    name: "",
    description: "",
    datasetType: DatasetType.TEXT,
    tags: [],
  });

  const handleSubmit = async () => {
    const formValues = await form.validateFields();

    const params = {
      ...formValues,
      files: undefined,
    };
    try {
      const { data } = await createDatasetUsingPost(params);
      message.success(`数据集创建成功`);
      navigate("/data/management/detail/" + data.id);
    } catch (error) {
      console.error(error);
      message.error("数据集创建失败，请重试");
      return;
    }
  };

  const handleValuesChange = (_, allValues) => {
    setNewDataset({ ...newDataset, ...allValues });
  };

  return (
    <div className="h-full flex flex-col flex-1">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Link to="/data/management">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold bg-clip-text">创建数据集</h1>
        </div>
      </div>

      {/* form */}
      <div className="flex-overflow-auto border-card">
        <div className="flex-1 p-6 overflow-auto">
          <Form
            form={form}
            initialValues={newDataset}
            onValuesChange={handleValuesChange}
            layout="vertical"
          >
            <BasicInformation data={newDataset} setData={setNewDataset} />
          </Form>
        </div>
        <div className="flex gap-2 justify-end p-6 border-top">
          <Button onClick={() => navigate("/data/management")}>取消</Button>
          <Button
            type="primary"
            disabled={!newDataset.name || !newDataset.datasetType}
            onClick={handleSubmit}
          >
            确定
          </Button>
        </div>
      </div>
    </div>
  );
}
