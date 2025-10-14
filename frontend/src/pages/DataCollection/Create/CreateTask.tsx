import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Select,
  Radio,
  Form,
  Divider,
  InputNumber,
  TimePicker,
  App,
} from "antd";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { createTaskUsingPost } from "../collection.apis";

const { TextArea } = Input;

interface ScheduleConfig {
  type: "immediate" | "scheduled";
  scheduleType?: "day" | "week" | "month" | "custom";
  time?: string;
  dayOfWeek?: string;
  dayOfMonth?: string;
  cronExpression?: string;
  maxRetries?: number;
}

const defaultTemplates = [
  {
    id: "nas-to-local",
    name: "NAS到本地",
    description: "从NAS文件系统导入数据到本地文件系统",
    config: {
      reader: "nasreader",
      writer: "localwriter",
    },
  },
  {
    id: "obs-to-local",
    name: "OBS到本地",
    description: "从OBS文件系统导入数据到本地文件系统",
    config: {
      reader: "obsreader",
      writer: "localwriter",
    },
  },
  {
    id: "web-tolocal",
    name: "Web到本地",
    description: "从Web URL导入数据到本地文件系统",
    config: {
      reader: "webreader",
      writer: "localwriter",
    },
  },
];

export default function CollectionTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const [templateType, setTemplateType] = useState<"default" | "custom">(
    "default"
  );
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [customConfig, setCustomConfig] = useState("");

  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    type: "immediate",
    maxRetries: 10,
    scheduleType: "daily",
  });

  const [isCreateDataset, setIsCreateDataset] = useState(false);

  const handleSubmit = async () => {
    const formData = await form.validateFields();
    if (templateType === "default" && !selectedTemplate) {
      window.alert("请选择默认模板");
      return;
    }
    if (templateType === "custom" && !customConfig.trim()) {
      window.alert("请填写自定义配置");
      return;
    }
    // Create task logic here
    const params = {
      ...formData,
      templateType,
      selectedTemplate: templateType === "default" ? selectedTemplate : null,
      customConfig: templateType === "custom" ? customConfig : null,
      scheduleConfig,
    };
    console.log("Creating task:", params);
    await createTaskUsingPost(params);
    message.success("任务创建成功");
    navigate("/data/collection");
  };

  return (
    <div className="min-h-screen">
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

      <Card>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            name: "",
            datasetName: "",
            fileFormat: "",
            description: "",
            cronExpression: "",
            retryCount: 3,
            timeout: 3600,
            incrementalField: "",
          }}
          onValuesChange={(_, allValues) => {
            // 文件格式变化时重置模板选择
            if (_.fileFormat !== undefined) setSelectedTemplate("");
          }}
        >
          {/* 基本信息 */}
          <h2 className="font-medium text-gray-900 text-lg mb-4">基本信息</h2>

          <Form.Item
            label="任务名称"
            name="name"
            rules={[{ required: true, message: "请输入任务名称" }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea placeholder="请输入任务描述" rows={3} />
          </Form.Item>
          <Form.Item label="文件格式" name="fileFormat">
            <Input placeholder="请填写文件格式，使用正则表达式" />
          </Form.Item>

          {/* 同步配置 */}
          <h2 className="font-medium text-gray-900 my-4 text-lg">同步配置</h2>
          <Form.Item label="同步方式">
            <Radio.Group
              value={scheduleConfig.type}
              onChange={(e) =>
                setScheduleConfig({
                  type: e.target.value as ScheduleConfig["type"],
                })
              }
            >
              <Radio value="immediate">立即同步</Radio>
              <Radio value="scheduled">定时同步</Radio>
            </Radio.Group>
          </Form.Item>
          {scheduleConfig.type === "scheduled" && (
            <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item label="调度类型">
                <Select
                  options={[
                    { label: "每日", value: "day" },
                    { label: "每周", value: "week" },
                    { label: "每月", value: "month" },
                    { label: "自定义Cron", value: "custom" },
                  ]}
                  value={scheduleConfig.scheduleType}
                  onChange={(value) =>
                    setScheduleConfig((prev) => ({
                      ...prev,
                      scheduleType: value as ScheduleConfig["scheduleType"],
                    }))
                  }
                />
              </Form.Item>
              {scheduleConfig.scheduleType === "custom" ? (
                <Form.Item
                  label="Cron表达式"
                  name="cronExpression"
                  rules={[{ required: true, message: "请输入Cron表达式" }]}
                >
                  <Input
                    placeholder="例如：0 0 * * * 表示每天午夜执行"
                    value={scheduleConfig.cronExpression}
                    onChange={(e) =>
                      setScheduleConfig((prev) => ({
                        ...prev,
                        cronExpression: e.target.value,
                      }))
                    }
                  />
                </Form.Item>
              ) : (
                <Form.Item label="执行时间" className="w-full">
                  {scheduleConfig.scheduleType === "day" ? (
                    <TimePicker />
                  ) : (
                    <Select
                      options={
                        scheduleConfig.scheduleType === "week"
                          ? [
                              { label: "周一", value: "1" },
                              { label: "周二", value: "2" },
                              { label: "周三", value: "3" },
                              { label: "周四", value: "4" },
                              { label: "周五", value: "5" },
                              { label: "周六", value: "6" },
                              { label: "周日", value: "0" },
                            ]
                          : [
                              { label: "每月1日", value: "1" },
                              { label: "每月5日", value: "5" },
                              { label: "每月10日", value: "10" },
                              { label: "每月15日", value: "15" },
                              { label: "每月20日", value: "20" },
                              { label: "每月25日", value: "25" },
                              { label: "每月30日", value: "30" },
                            ]
                      }
                      placeholder={
                        scheduleConfig.scheduleType === "week"
                          ? "选择星期几"
                          : "选择日期"
                      }
                      value={scheduleConfig.dayOfWeek}
                      onChange={(value) =>
                        setScheduleConfig((prev) => ({
                          ...prev,
                          dayOfWeek: value as string,
                        }))
                      }
                    />
                  )}
                </Form.Item>
              )}
            </div>
          )}
          <Form.Item label="最大执行次数">
            <InputNumber
              min={1}
              value={scheduleConfig.maxRetries}
              onChange={(value) =>
                setScheduleConfig((prev) => ({
                  ...prev,
                  maxRetries: value,
                }))
              }
              className="w-full"
              style={{ width: "100%" }}
            />
          </Form.Item>

          {/* 模板配置 */}
          <h2 className="font-medium text-gray-900 my-4 text-lg">模板配置</h2>
          <Form.Item label="模板类型">
            <Radio.Group
              value={templateType}
              onChange={(e) => setTemplateType(e.target.value)}
            >
              <Radio value="default">使用默认模板</Radio>
              <Radio value="custom">自定义DataX JSON配置</Radio>
            </Radio.Group>
          </Form.Item>
          {templateType === "default" && (
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
                    onClick={() => setSelectedTemplate(template.id)}
                  >
                    <div className="font-medium">{template.name}</div>
                    <div className="text-gray-500">{template.description}</div>
                    <div className="text-gray-400">
                      {template.config.reader} → {template.config.writer}
                    </div>
                  </div>
                ))}
              </div>
            </Form.Item>
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
                  onChange={(e) => setIsCreateDataset(e.target.value)}
                >
                  <Radio value={true}>是</Radio>
                  <Radio value={false}>否</Radio>
                </Radio.Group>
              </Form.Item>
              {isCreateDataset && (
                <>
                  <Form.Item
                    label="数据集名称"
                    name="datasetName"
                    rules={[{ required: true, message: "请输入数据集名称" }]}
                  >
                    <Input placeholder="请输入数据集名称" />
                  </Form.Item>
                </>
              )}
            </>
          )}

          {/* 提交按钮 */}
          <Divider />
          <div className="flex gap-2 justify-end">
            <Button onClick={() => navigate("/data/collection")}>取消</Button>
            <Button type="primary" onClick={handleSubmit}>
              创建任务
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
