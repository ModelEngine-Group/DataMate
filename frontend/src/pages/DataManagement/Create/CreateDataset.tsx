import { useEffect, useState } from "react";

import { ArrowLeft } from "lucide-react";
import { Select, Card, Button, Input, Form, Radio, Divider, App } from "antd";
import RadioCard from "@/components/RadioCard";
import { Link, useNavigate, useParams } from "react-router";
import { useImportFile } from "../hooks/useImportFile";
import { datasetTypes, dataSourceOptions } from "../dataset.const";
import {
  createDatasetUsingPost,
  queryDatasetByIdUsingGet,
  queryDatasetTagsUsingGet,
  updateDatasetByIdUsingPut,
} from "../dataset.api";
import { DatasetSubType, DatasetType, DataSource } from "../dataset.model";
import { queryTasksUsingPost } from "@/pages/DataCollection/collection.apis";
import { mockPreparedTags } from "@/components/TagManagement";

export default function DatasetCreate() {
  const navigate = useNavigate();
  const { id } = useParams(); // 获取动态路由参数
  const { message } = App.useApp();
  const [form] = Form.useForm();

  const { importFileRender, fileList, handleUpload } = useImportFile();
  const [newDataset, setNewDataset] = useState({
    name: "",
    description: "",
    datasetType: DatasetType.TEXT,
    type: DatasetSubType.TEXT_DOCUMENT,
    tags: [],
    source: DataSource.UPLOAD,
    target: DataSource.UPLOAD,
  });
  const [collectionOptions, setCollectionOptions] = useState([]);
  const [tagOptions, setTagOptions] = useState<
    {
      label: JSX.Element;
      title: string;
      options: { label: JSX.Element; value: string }[];
    }[]
  >([]);

  // 获取标签
  const fetchTags = async () => {
    try {
      const { data } = await queryDatasetTagsUsingGet();
      const preparedTags = mockPreparedTags.map((tag) => ({
        label: tag.name,
        value: tag.name,
      }));
      const customTags = data.map((tag) => ({
        label: tag.name,
        value: tag.name,
      }));
      setTagOptions([
        {
          label: <span>预置标签</span>,
          title: "prepared",
          options: preparedTags,
        },
        {
          label: <span>自定义标签</span>,
          title: "custom",
          options: customTags,
        },
      ]);
    } catch (error) {
      console.error("Error fetching tags: ", error);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  // 获取归集任务列表
  const fetchCollectionTasks = async () => {
    try {
      const { data } = await queryTasksUsingPost({ pageNum: 1, pageSize: 100 });
      const options = data.map((task: any) => ({
        label: task.name,
        value: task.id,
      }));
      setCollectionOptions(options);
    } catch (error) {
      console.error("Error fetching collection tasks:", error);
    }
  };

  useEffect(() => {
    fetchCollectionTasks();
  }, []);

  const fetchDataset = async () => {
    // 如果有id，说明是编辑模式
    if (id) {
      const { data } = await queryDatasetByIdUsingGet(id);
      setNewDataset({
        ...data,
        datasetType: DatasetType.TEXT,
        type: DatasetSubType.TEXT_DOCUMENT,
        tags: data.tags || [],
        source: DataSource.UPLOAD,
        target: DataSource.UPLOAD,
      });
    }
  };

  useEffect(() => {
    fetchDataset();
  }, [id, form]);

  const [importConfig, setImportConfig] = useState({
    source: DataSource.UPLOAD,
    target: DataSource.UPLOAD,
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
    const formValues = await form.validateFields();

    const params = {
      ...formValues,
      files: undefined,
    };
    let dataset;
    try {
      const callFn = id
        ? () => updateDatasetByIdUsingPut(id, params)
        : () => createDatasetUsingPost(params);
      const { data } = await callFn();
      dataset = data;
      message.success(`数据集${id ? "更新" : "创建"}成功`);

      if (importConfig.source === DataSource.UPLOAD) {
        if (fileList.length === 0) {
          message.error("请上传文件");
          return;
        }
        handleUpload(message, dataset);
      }
      if (importConfig.source === DataSource.NAS) {
        message.error("请填写NAS地址和共享路径");
        return;
      }
      if (importConfig.source === DataSource.OBS) {
        message.error("请填写完整的OBS配置信息");
        return;
      }
      if (importConfig.source === DataSource.COLLECTION) {
        message.error("请选择归集任务");
        return;
      }
      if (importConfig.target === DataSource.DATABASE) {
        message.error("请填写完整的数据库配置信息");
        return;
      }

      navigate("/data/management");
    } catch (error) {
      message.error("数据集创建失败，请重试");
      return;
    }
  };

  const handleDatasourceChange = (e: RadioChangeEvent) => {
    const value = e.target?.value ?? DataSource.UPLOAD;
    let defaultTarget = "";
    // 根据数据源自动设置目标位置
    if (value === DataSource.DATABASE) {
      defaultTarget = DataSource.DATABASE;
    } else if (
      value === DataSource.UPLOAD ||
      value === DataSource.NAS ||
      value === DataSource.OBS
    ) {
      defaultTarget = DataSource.UPLOAD;
    }
    setImportConfig({
      ...importConfig,
      source: value,
      target: defaultTarget,
    });
  };

  const handleValuesChange = (currentValue, allValues) => {
    if (Object.keys(currentValue).includes("datasetType")) {
      // 重置type
      allValues.type =
        datasetTypes.find((item) => item.value === currentValue.datasetType)
          ?.options?.[0]?.value || "";
      form.setFieldValue("type", allValues.type);
    }
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
            <Select className="w-full" mode="tags" options={tagOptions} />
          </Form.Item>

          {/* Import Configuration */}
          <div className="space-y-4 pt-4">
            <h2 className="font-medium text-gray-900 mt-4 text-base">
              数据导入配置
            </h2>
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
                  { label: "本地文件夹", value: DataSource.UPLOAD },
                  { label: "数据库", value: DataSource.DATABASE },
                ]}
                disabled
                value={importConfig.target || DataSource.UPLOAD}
                defaultValue={importConfig.target || DataSource.UPLOAD}
                onChange={(value) =>
                  setImportConfig({ ...importConfig, target: value })
                }
              ></Select>
            </Form.Item>
            {importConfig.source === DataSource.COLLECTION && (
              <Form.Item
                name={["config", "collectionId"]}
                label="归集任务"
                required
              >
                <Select
                  placeholder="请选择归集任务"
                  options={collectionOptions}
                  value={importConfig.sourceConfig.collectionName || ""}
                  onChange={(value) =>
                    setImportConfig({
                      ...importConfig,
                      sourceConfig: {
                        ...importConfig.sourceConfig,
                        collectionName: value,
                      },
                    })
                  }
                />
              </Form.Item>
            )}

            {/* nas import */}
            {importConfig.source === DataSource.NAS && (
              <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
                <Form.Item
                  name={["config", "nasPath"]}
                  rules={[{ required: true }]}
                  label="NAS地址"
                >
                  <Input
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
                <Form.Item
                  name={["config", "sharePath"]}
                  rules={[{ required: true }]}
                  label="共享路径"
                >
                  <Input
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
                <Form.Item
                  name={["config", "sharePath"]}
                  rules={[{ required: true }]}
                  label="用户名"
                >
                  <Input
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
                <Form.Item
                  name={["config", "password"]}
                  rules={[{ required: true }]}
                  label="密码"
                >
                  <Input
                    type="password"
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
            {importConfig.source === DataSource.OBS && (
              <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
                <Form.Item
                  name={["config", "endpoint"]}
                  rules={[{ required: true }]}
                  label="Endpoint"
                >
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
                <Form.Item
                  name={["config", "bucket"]}
                  rules={[{ required: true }]}
                  label="Bucket"
                >
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
                <Form.Item
                  name={["config", "accessKey"]}
                  rules={[{ required: true }]}
                  label="Access Key"
                >
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
                <Form.Item
                  name={["config", "secretKey"]}
                  rules={[{ required: true }]}
                  label="Secret Key"
                >
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
            {importConfig.source === DataSource.UPLOAD && (
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
                      return Promise.reject();
                    },
                  }),
                ]}
              >
                {importFileRender()}
              </Form.Item>
            )}

            {/* Target Configuration */}
            {importConfig.target &&
              importConfig.target !== DataSource.UPLOAD && (
                <div className="space-y-3 p-4 bg-blue-50 rounded-lg">
                  {importConfig.target === DataSource.DATABASE && (
                    <div className="grid grid-cols-2 gap-3">
                      <Form.Item
                        name={["config", "datasetType"]}
                        rules={[{ required: true }]}
                        label="数据库类型"
                      >
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
                      <Form.Item
                        name={["config", "tableName"]}
                        rules={[{ required: true }]}
                        label="表名"
                      >
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
                      <Form.Item
                        name={["config", "connectionString"]}
                        rules={[{ required: true }]}
                        label="连接字符串"
                      >
                        <Input
                          className="h-8 text-xs col-span-2"
                          placeholder="数据库连接字符串"
                          value={
                            importConfig.targetConfig.connectionString || ""
                          }
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
