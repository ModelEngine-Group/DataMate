import { useEffect, useState } from "react";

import { ArrowLeft } from "lucide-react";
import {
  Select,
  Card,
  Button,
  Input,
  Form,
  Radio,
  Divider,
  message,
} from "antd";
import RadioCard from "@/components/RadioCard";
import { Link, useNavigate, useParams } from "react-router";
import { useImportFile } from "./hooks/useImportFile";
import { datasetTypes } from "./dataset-model";
import { queryDatasetByIdUsingGet } from "./dataset-apis";

const dataSourceOptions = [
  { label: "本地上传", value: "local" },
  { label: "数据库导入", value: "database" },
  { label: "NAS导入", value: "nas" },
  { label: "OBS导入", value: "obs" },
];

export default function DatasetCreate() {
  const navigate = useNavigate();
  const { id } = useParams(); // 获取动态路由参数
  const [messageApi] = message.useMessage();
  const [form] = Form.useForm();

  const { importFileRender, fileList, handleUpload } = useImportFile();
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [newDataset, setNewDataset] = useState({
    name: "",
    description: "",
    datasetType: "PRETRAIN",
    type: "PRETRAIN_TEXT",
    tags: [],
    source: "local",
    target: "local",
  });

  const fetchDataset = async () => {
    // 如果有id，说明是编辑模式
    if (id) {
      const { data } = await queryDatasetByIdUsingGet(id);
      setNewDataset({
        name: data.name,
        description: data.description,
        datasetType: "PRETRAIN",
        type: "PRETRAIN_IMAGE",
        tags: data.tags || [],
        source: "local",
        target: "local",
      });
    }
  };

  useEffect(() => {
    fetchDataset();
  }, [id, form]);

  const [importConfig, setImportConfig] = useState({
    source: "local",
    target: "local",
    sourceConfig: {
      nasHost: "",
      sharePath: "",
      username: "",
      password: "",
      endpoint: "",
      bucket: "",
      accessKey: "",
      secretKey: "",
    },
    targetConfig: {
      databaseType: "",
      databaseName: "",
      tableName: "",
      username: "",
      password: "",
      dbType: "",
      connectionString: "",
    },
  });

  const handleSubmit = async () => {
    const url = id ? `/api/datasets/${id}` : "/api/datasets";
    const method = id ? "PUT" : "POST";
    const formValues = await form.validateFields();
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...formValues, files: undefined }),
    });
    if (!res.ok) throw new Error("Failed to fetch datasets");
    const data = await res.json();
    handleUpload(messageApi, data);
  };

  const handleDatasourceChange = (e: RadioChangeEvent) => {
    const value = e.target?.value ?? "local";
    let defaultTarget = "";
    // 根据数据源自动设置目标位置
    if (value === "database") {
      defaultTarget = "database";
    } else if (value === "local" || value === "nas" || value === "obs") {
      defaultTarget = "local";
    }
    setImportConfig({
      ...importConfig,
      source: value,
      target: defaultTarget,
    });
  };

  const handleValuesChange = (_, allValues: any) => {
    setNewDataset({ ...newDataset, ...allValues });
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Link to="/data/management">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold bg-clip-text">
            {id ? "编辑" : "创建"}数据集
          </h1>
        </div>
      </div>

      {/* form */}
      <Card className="overflow-y-auto p-2">
        <Form
          form={form}
          initialValues={newDataset}
          onValuesChange={handleValuesChange}
          layout="vertical"
        >
          <h2 className="font-medium text-gray-900 text-base mb-2">基本信息</h2>
          <Form.Item
            label="数据集名称"
            name="name"
            rules={[{ required: true, message: "请输入数据集名称" }]}
          >
            <Input placeholder="输入数据集名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="描述数据集的用途和内容" rows={3} />
          </Form.Item>

          {/* 数据集类型选择 - 使用卡片形式 */}
          <Form.Item
            label="数据集类型"
            name="datasetType"
            rules={[{ required: true, message: "Please input your password!" }]}
          >
            <Radio.Group
              buttonStyle="solid"
              options={datasetTypes}
              optionType="button"
            />
          </Form.Item>
          <Form.Item
            name="type"
            rules={[{ required: true, message: "请选择使用场景" }]}
          >
            <RadioCard
              options={
                datasetTypes.find(
                  (item) => item.value === newDataset.datasetType
                )?.options ?? []
              }
              value={newDataset.type}
              onChange={(type) => setNewDataset({ ...newDataset, type })}
            />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Select
              className="w-full"
              mode="tags"
              options={availableTags.map((tag) => ({ value: tag, label: tag }))}
            />
          </Form.Item>

          {/* Import Configuration */}
          <div className="space-y-4 pt-4">
            <h2 className="font-medium text-gray-900 mt-4 text-base">
              数据导入配置
            </h2>
            <div className="grid grid-cols-2">
              <Form.Item
                label="数据源"
                name="source"
                rules={[{ required: true, message: "请选择数据源" }]}
              >
                <Radio.Group
                  buttonStyle="solid"
                  options={dataSourceOptions}
                  optionType="button"
                  value={importConfig.source}
                  onChange={handleDatasourceChange}
                />
              </Form.Item>
              <Form.Item
                label="目标位置"
                name="target"
                rules={[{ required: true, message: "请选择目标位置" }]}
              >
                <Select
                  className="w-full"
                  options={[
                    { label: "本地文件夹", value: "local" },
                    { label: "数据库", value: "database" },
                  ]}
                  disabled
                  value={importConfig.target || "local"}
                  defaultValue={importConfig.target || "local"}
                  onChange={(value) =>
                    setImportConfig({ ...importConfig, target: value })
                  }
                ></Select>
              </Form.Item>
            </div>

            {/* nas import */}
            {importConfig.source === "nas" && (
              <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
                <Form.Item label="NAS地址" className="space-y-1">
                  <Input
                    className="h-8 text-xs"
                    placeholder="192.168.1.100"
                    value={importConfig.sourceConfig.nasHost || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          nasHost: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
                <Form.Item label="共享路径" className="space-y-1">
                  <Input
                    className="h-8 text-xs"
                    placeholder="/share/data"
                    value={importConfig.sourceConfig.sharePath || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          sharePath: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
                <Form.Item label="共享路径" className="space-y-1">
                  <Input
                    className="h-8 text-xs"
                    placeholder="用户名"
                    value={importConfig.sourceConfig.username || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          username: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
                <Form.Item label="密码" className="space-y-1">
                  <Input
                    type="password"
                    className="h-8 text-xs"
                    placeholder="密码"
                    value={importConfig.sourceConfig.password || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          password: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
              </div>
            )}
            {/* obs import */}
            {importConfig.source === "obs" && (
              <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
                <Form.Item label="Endpoint" className="space-y-1">
                  <Input
                    className="h-8 text-xs"
                    placeholder="obs.cn-north-4.myhuaweicloud.com"
                    value={importConfig.sourceConfig.endpoint || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          endpoint: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
                <Form.Item label="Bucket名称" className="space-y-1">
                  <Input
                    className="h-8 text-xs"
                    placeholder="my-bucket"
                    value={importConfig.sourceConfig.bucket || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          bucket: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
                <Form.Item label="Access Key" className="space-y-1">
                  <Input
                    className="h-8 text-xs"
                    placeholder="Access Key"
                    value={importConfig.sourceConfig.accessKey || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          accessKey: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
                <Form.Item label="Secret Key" className="space-y-1">
                  <Input
                    type="password"
                    className="h-8 text-xs"
                    placeholder="Secret Key"
                    value={importConfig.sourceConfig.secretKey || ""}
                    onChange={(e) =>
                      setImportConfig({
                        ...importConfig,
                        sourceConfig: {
                          ...importConfig.sourceConfig,
                          secretKey: e.target.value,
                        },
                      })
                    }
                  />
                </Form.Item>
              </div>
            )}

            {/* Local Upload Component */}
            {importConfig.source === "local" && (
              <Form.Item
                label="上传文件"
                name="files"
                rules={[
                  {
                    required: true,
                    message: "请上传文件",
                  },
                  () => ({
                    validator(_, value) {
                      if (fileList.length > 0) {
                        return Promise.resolve();
                      }
                      return Promise.reject(
                        new Error(
                          "The new password that you entered do not match!"
                        )
                      );
                    },
                  }),
                ]}
              >
                {importFileRender()}
              </Form.Item>
            )}

            {/* Target Configuration */}
            {importConfig.target && importConfig.target !== "local" && (
              <div className="space-y-3 p-4 bg-blue-50 rounded-lg">
                {importConfig.target === "database" && (
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item label="数据库类型" className="space-y-1">
                      <Select
                        className="w-full"
                        value={importConfig.targetConfig.dbType || ""}
                        options={[
                          { label: "MySQL", value: "mysql" },
                          { label: "PostgreSQL", value: "postgresql" },
                          { label: "MongoDB", value: "mongodb" },
                        ]}
                        onChange={(value) =>
                          setImportConfig({
                            ...importConfig,
                            targetConfig: {
                              ...importConfig.targetConfig,
                              dbType: value,
                            },
                          })
                        }
                      ></Select>
                    </Form.Item>
                    <Form.Item label="表名" className="space-y-1">
                      <Input
                        className="h-8 text-xs"
                        placeholder="dataset_table"
                        value={importConfig.targetConfig.tableName || ""}
                        onChange={(e) =>
                          setImportConfig({
                            ...importConfig,
                            targetConfig: {
                              ...importConfig.targetConfig,
                              tableName: e.target.value,
                            },
                          })
                        }
                      />
                    </Form.Item>
                    <Form.Item name="连接字符串" className="space-y-1">
                      <Input
                        className="h-8 text-xs col-span-2"
                        placeholder="数据库连接字符串"
                        value={importConfig.targetConfig.connectionString || ""}
                        onChange={(e) =>
                          setImportConfig({
                            ...importConfig,
                            targetConfig: {
                              ...importConfig.targetConfig,
                              connectionString: e.target.value,
                            },
                          })
                        }
                      />
                    </Form.Item>
                  </div>
                )}
              </div>
            )}
          </div>
          <Divider />
          <div className="flex gap-2 justify-end">
            <Button onClick={() => navigate("/dataset-management")}>
              取消
            </Button>
            <Button type="primary" onClick={handleSubmit}>
              创建
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
