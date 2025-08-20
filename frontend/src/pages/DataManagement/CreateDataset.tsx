import { useState } from "react";

import { ArrowLeft } from "lucide-react";
import { InboxOutlined } from "@ant-design/icons";
import {
  Select,
  Card,
  Button,
  Input,
  Form,
  Radio,
  Divider,
  message,
  Upload,
  type UploadProps,
} from "antd";
import { datasetTypes, mockTags } from "@/mock/dataset";
import RadioCard from "@/components/RadioCard";
import { Link, useNavigate } from "react-router";
import type { Dataset } from "@/types/dataset";

const { Dragger } = Upload;

const dataSourceOptions = [
  { label: "本地上传", value: "local" },
  { label: "数据库导入", value: "database" },
  { label: "NAS导入", value: "nas" },
  { label: "OBS导入", value: "obs" },
];

type FileType = Parameters<GetProp<UploadProps, "beforeUpload">>[0];

export default function DatasetCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [availableTags, setAvailableTags] = useState<string[]>(mockTags);
  const [newDataset, setNewDataset] = useState({
    name: "",
    description: "",
    datasetType: "PRETRAIN",
    type: "PRETRAIN_TEXT",
    tags: [],
    source: "local",
    target: "local",
  });
  const [fileList, setFileList] = useState([]);
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

  const handleUpload = (data: Dataset) => {
    const formData = new FormData();
    fileList.forEach((file) => {
      formData.append("files[]", file);
    });

    console.log("Uploading files for dataset ID:", formData, data.id);
    fetch(`/api/dataset/v2/file/upload/${data.id}`, {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then(() => {
        setFileList([]);
        message.success("数据集创建成功");
        navigate("/data/management/details/" + data.id);
      })
      .catch(() => {
        message.error("上传失败.");
      })
      .finally(() => {});
  };

  const handleCreateDataset = async () => {
    const formValues = await form.validateFields();
    const res = await fetch("/api/dataset/v2/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...formValues, files: undefined }),
    });
    if (!res.ok) throw new Error("Failed to fetch datasets");
    const data = await res.json();
    handleUpload(data);
  };

  const options: SelectProps["options"] = [];

  for (let i = 10; i < 36; i++) {
    options.push({
      value: i.toString(36) + i,
      label: i.toString(36) + i,
    });
  }

  const onFinishFailed = (errorInfo) => {
    console.log("Failed:", errorInfo);
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
          <h1 className="text-xl font-bold bg-clip-text">创建数据集</h1>
        </div>
      </div>

      {/* form */}
      <Card className="overflow-y-auto p-2">
        <Form
          form={form}
          initialValues={newDataset}
          onFinishFailed={onFinishFailed}
          onValuesChange={handleValuesChange}
          layout="vertical"
        >
          <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>
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
              value={newDataset.usageType}
              onChange={(usageType) =>
                setNewDataset({ ...newDataset, usageType })
              }
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
            <h2 className="font-medium text-gray-900 mt-4 text-lg">
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
                <Dragger
                  className="w-full"
                  fileList={fileList}
                  onRemove={(file) => {
                    const index = fileList.indexOf(file);
                    const newFileList = fileList.slice();
                    newFileList.splice(index, 1);
                    setFileList(newFileList);
                  }}
                  beforeUpload={(file) => {
                    setFileList([...fileList, file]);

                    return false;
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">本地文件上传</p>
                  <p className="ant-upload-hint">
                    拖拽文件到此处或点击选择文件,支持 JPG, PNG, TXT, JSON 等格式
                  </p>
                </Dragger>
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
            <Button type="primary" onClick={handleCreateDataset}>
              创建
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
