import { useState } from "react";
import { Input, Button, Radio, Form, InputNumber, App, Select } from "antd";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { createTaskUsingPost } from "../collection.apis";
import SimpleCronScheduler from "@/pages/DataCollection/Create/SimpleCronScheduler";
import RadioCard from "@/components/RadioCard";
import { datasetTypes } from "@/pages/DataManagement/dataset.const";
import { SyncModeMap } from "../collection.const";
import { SyncMode } from "../collection.model";
import { DatasetSubType } from "@/pages/DataManagement/dataset.model";

const { TextArea } = Input;

const defaultTemplates = [
  {
    id: "NAS",
    name: "NAS到本地",
    description: "从NAS文件系统导入数据到本地文件系统",
    config: {
      reader: "nfsreader",
      writer: "localwriter",
    },
  },
  {
    id: "OBS",
    name: "OBS到本地",
    description: "从OBS文件系统导入数据到本地文件系统",
    config: {
      reader: "obsreader",
      writer: "localwriter",
    },
  },
  {
    id: "MYSQL",
    name: "Mysql到本地",
    description: "从Mysql中导入数据到本地文件系统",
    config: {
      reader: "mysqlreader",
      writer: "localwriter",
    },
  },
];

const syncModeOptions = Object.values(SyncModeMap);

enum TemplateType {
  NAS = "NAS",
  OBS = "OBS",
  MYSQL = "MYSQL",
}

export default function CollectionTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const [templateType, setTemplateType] = useState<"default" | "custom">(
    "default"
  );
  // 默认模板类型设为 NAS
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateType>(
    TemplateType.NAS
  );
  const [customConfig, setCustomConfig] = useState("");

  // 将 newTask 设为 any，并初始化 config.templateType 为 NAS
  const [newTask, setNewTask] = useState<any>({
    name: "",
    description: "",
    syncMode: SyncMode.ONCE,
    cronExpression: "",
    maxRetries: 10,
    dataset: null,
    config: { templateType: TemplateType.NAS },
    createDataset: false,
  });
  const [scheduleExpression, setScheduleExpression] = useState({
    type: SyncMode.SCHEDULED,
    time: "00:00",
    cronExpression: "0 0 0 * * ?",
  });

  const [isCreateDataset, setIsCreateDataset] = useState(false);

  const handleSubmit = async () => {
    try {
      await form.validateFields();
      if (templateType === "default" && !selectedTemplate) {
        window.alert("请选择默认模板");
        return;
      }
      if (templateType === "custom" && !customConfig.trim()) {
        window.alert("请填写自定义配置");
        return;
      }

      // 构建最终 payload，不依赖异步 setState
      const payload = {
        ...newTask,
        taskType:
          templateType === "default" ? selectedTemplate : "CUSTOM",
        config: {
          ...((newTask && newTask.config) || {}),
          ...(templateType === "custom" ? { dataxJson: customConfig } : {}),
        },
      };

      console.log("创建任务 payload:", payload);

      await createTaskUsingPost(payload);
      message.success("任务创建成功");
      navigate("/data/collection");
    } catch (error) {
      message.error(`${error?.data?.message}：${error?.data?.data}`);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Link to="/data/collection">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold bg-clip-text">创建归集任务</h1>
        </div>
      </div>

      <div className="flex-overflow-auto border-card">
        <div className="flex-1 overflow-auto p-6">
          <Form
            form={form}
            layout="vertical"
            initialValues={newTask}
            onValuesChange={(_, allValues) => {
              setNewTask({ ...newTask, ...allValues });
            }}
          >
            {/* 基本信息 */}
            <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>

            <Form.Item
              label="名称"
              name="name"
              rules={[{ required: true, message: "请输入任务名称" }]}
            >
              <Input placeholder="请输入任务名称" />
            </Form.Item>
            <Form.Item label="描述" name="description">
              <TextArea placeholder="请输入任务描述" rows={3} />
            </Form.Item>

            {/* 同步配置 */}
            <h2 className="font-medium text-gray-900 pt-6 mb-2 text-lg">
              同步配置
            </h2>
            <Form.Item name="syncMode" label="同步方式">
              <Radio.Group
                value={newTask.syncMode}
                options={syncModeOptions}
                onChange={(e) => {
                  const value = e.target.value;
                  setNewTask({
                    ...newTask,
                    syncMode: value,
                    scheduleExpression:
                      value === SyncMode.SCHEDULED
                        ? scheduleExpression.cronExpression
                        : "",
                  });
                }}
              ></Radio.Group>
            </Form.Item>
            {newTask.syncMode === SyncMode.SCHEDULED && (
              <Form.Item
                label=""
                rules={[{ required: true, message: "请输入Cron表达式" }]}
              >
                <SimpleCronScheduler
                  className="px-2 rounded"
                  value={scheduleExpression}
                  onChange={(value) => {
                    setScheduleExpression(value);
                    setNewTask({
                      ...newTask,
                      scheduleExpression: value.cronExpression,
                    });
                  }}
                />
              </Form.Item>
            )}
            <Form.Item name="maxRetries" label="最大执行次数">
              <InputNumber min={1} style={{ width: "100%" }} />
            </Form.Item>

            {/* 模板配置 */}
            <h2 className="font-medium text-gray-900 pt-6 mb-2 text-lg">
              模板配置
            </h2>
            {/* <Form.Item label="模板类型">
              <Radio.Group
                value={templateType}
                onChange={(e) => setTemplateType(e.target.value)}
              >
                <Radio value="default">使用默认模板</Radio>
                <Radio value="custom">自定义DataX JSON配置</Radio>
              </Radio.Group>
            </Form.Item> */}
            {templateType === "default" && (
              <>
                {
                  <Form.Item label="选择模板">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                      {defaultTemplates.map((template) => (
                        <div
                          key={template.id}
                          className={`border p-4 rounded-md hover:shadow-lg transition-shadow ${
                            selectedTemplate === template.id
                              ? "border-blue-500"
                              : "border-gray-300"
                          }`}
                          onClick={() => {
                            setSelectedTemplate(template.id as TemplateType);
                            // 使用函数式更新，合并之前的 config
                            setNewTask((prev: any) => ({
                              ...prev,
                              config: {
                                templateType: template.id,
                              },
                            }));
                            // 同步表单显示
                            form.setFieldsValue({
                              config: { templateType: template.id },
                            });
                          }}
                        >
                          <div className="font-medium">{template.name}</div>
                          <div className="text-gray-500">
                            {template.description}
                          </div>
                          <div className="text-gray-400">
                            {template.config.reader} → {template.config.writer}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Form.Item>
                }
                {/* nas import */}
                {selectedTemplate === TemplateType.NAS && (
                  <div className="grid grid-cols-2 gap-3 px-2 bg-blue-50 rounded">
                    <Form.Item
                      name={["config", "ip"]}
                      rules={[{ required: true, message: "请输入NAS地址" }]}
                      label="NAS地址"
                    >
                      <Input placeholder="192.168.1.100" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "path"]}
                      rules={[{ required: true, message: "请输入共享路径" }]}
                      label="共享路径"
                    >
                      <Input placeholder="/share/importConfig" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "files"]}
                      label="文件列表"
                      className="col-span-2"
                    >
                      <Select placeholder="请选择文件列表" mode="tags" />
                    </Form.Item>
                  </div>
                )}

                {/* obs import */}
                {selectedTemplate === TemplateType.OBS && (
                  <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
                    <Form.Item
                      name={["config", "endpoint"]}
                      rules={[{ required: true }]}
                      label="Endpoint"
                    >
                      <Input
                        className="h-8 text-xs"
                        placeholder="obs.cn-north-4.myhuaweicloud.com"
                      />
                    </Form.Item>
                    <Form.Item
                      name={["config", "bucket"]}
                      rules={[{ required: true }]}
                      label="Bucket"
                    >
                      <Input className="h-8 text-xs" placeholder="my-bucket" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "accessKey"]}
                      rules={[{ required: true }]}
                      label="Access Key"
                    >
                      <Input className="h-8 text-xs" placeholder="Access Key" />
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
                      />
                    </Form.Item>
                    <Form.Item
                      name={["config", "prefix"]}
                      rules={[{ required: true }]}
                      label="Prefix"
                    >
                      <Input className="h-8 text-xs" placeholder="Prefix" />
                    </Form.Item>
                  </div>
                )}

                {/* mysql import */}
                {selectedTemplate === TemplateType.MYSQL && (
                  <div className="grid grid-cols-2 gap-3 px-2 bg-blue-50 rounded">
                    <Form.Item
                      name={["config", "jdbcUrl"]}
                      rules={[{ required: true, message: "请输入数据库链接" }]}
                      label="数据库链接"
                      className="col-span-2"
                    >
                      <Input placeholder="jdbc:mysql://localhost:3306/mysql?useUnicode=true&characterEncoding=utf8" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "username"]}
                      rules={[{ required: true, message: "请输入用户名" }]}
                      label="用户名"
                    >
                      <Input placeholder="mysql" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "password"]}
                      rules={[{ required: true, message: "请输入密码" }]}
                      label="密码"
                    >
                      <Input type="password" className="h-8 text-xs" placeholder="Secret Key" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "querySql"]}
                      rules={[{ required: true, message: "请输入查询语句" }]}
                      label="查询语句"
                    >
                      <Input placeholder="select * from your_table" />
                    </Form.Item>
                    <Form.Item
                      name={["config", "headers"]}
                      label="列名"
                      className="col-span-2"
                    >
                      <Select placeholder="请输入列名" mode="tags" />
                    </Form.Item>
                  </div>
                )}
              </>
            )}

            {templateType === "custom" && (
              <Form.Item label="DataX JSON配置">
                <TextArea
                  placeholder="请输入DataX JSON配置..."
                  value={customConfig}
                  onChange={(e) => setCustomConfig(e.target.value)}
                  rows={12}
                  className="w-full"
                />
              </Form.Item>
            )}

            {/* 数据集配置 */}
            {templateType === "default" && (
              <>
                <h2 className="font-medium text-gray-900 my-4 text-lg">
                  数据集配置
                </h2>
                <Form.Item
                  label="是否创建数据集"
                  name="createDataset"
                  required
                  rules={[{ required: true, message: "请选择是否创建数据集" }]}
                >
                  <Radio.Group
                    value={isCreateDataset}
                    onChange={(e) => {
                      const value = e.target.value;
                      let datasetInit = null;
                      if (value === true) {
                        datasetInit = {};
                      }
                      form.setFieldsValue({
                        dataset: datasetInit,
                      });
                      setNewTask((prev: any) => ({
                        ...prev,
                        dataset: datasetInit,
                      }));
                      setIsCreateDataset(e.target.value);
                    }}
                  >
                    <Radio value={true}>是</Radio>
                    <Radio value={false}>否</Radio>
                  </Radio.Group>
                </Form.Item>
                {isCreateDataset && (
                  <>
                    <Form.Item
                      label="数据集名称"
                      name={["dataset", "name"]}
                      required
                    >
                      <Input
                        placeholder="输入数据集名称"
                        onChange={(e) => {
                          setNewTask((prev: any) => ({
                            ...prev,
                            dataset: {
                              ...(prev.dataset || {}),
                              name: e.target.value,
                            },
                          }));
                        }}
                      />
                    </Form.Item>
                    <Form.Item
                      label="数据集类型"
                      name={["dataset", "datasetType"]}
                      rules={[{ required: true, message: "请选择数据集类型" }]}
                    >
                      <RadioCard
                        options={datasetTypes}
                        value={newTask.dataset?.datasetType}
                        onChange={(type) => {
                          form.setFieldValue(["dataset", "datasetType"], type);
                          setNewTask((prev: any) => ({
                            ...prev,
                            dataset: {
                              ...(prev.dataset || {}),
                              datasetType: type as DatasetSubType,
                            },
                          }));
                        }}
                      />
                    </Form.Item>
                  </>
                )}
              </>
            )}
          </Form>
        </div>
        <div className="flex gap-2 justify-end border-top p-6">
          <Button onClick={() => navigate("/data/collection")}>取消</Button>
          <Button type="primary" onClick={handleSubmit}>
            创建任务
          </Button>
        </div>
      </div>
    </div>
  );
}
