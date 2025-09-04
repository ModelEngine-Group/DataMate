import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Select,
  Radio,
  Form,
  InputNumber,
  Divider,
} from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";

const { TextArea } = Input;

interface ScheduleConfig {
  type: "immediate" | "scheduled";
  scheduleType?: "daily" | "weekly" | "monthly" | "custom";
  time?: string;
  dayOfWeek?: string;
  dayOfMonth?: string;
  cronExpression?: string;
  maxExecutions?: number;
}

const templatesByFormat = {
  csv: [
    {
      id: "csv-to-mysql",
      name: "CSV到MySQL",
      description: "从CSV文件导入数据到MySQL数据库",
      config: {
        reader: "txtfilereader",
        writer: "mysqlwriter",
      },
    },
    {
      id: "csv-to-hive",
      name: "CSV到Hive",
      description: "从CSV文件导入数据到Hive数据仓库",
      config: {
        reader: "txtfilereader",
        writer: "hdfswriter",
      },
    },
  ],
  json: [
    {
      id: "json-to-mysql",
      name: "JSON到MySQL",
      description: "从JSON文件导入数据到MySQL数据库",
      config: {
        reader: "streamreader",
        writer: "mysqlwriter",
      },
    },
    {
      id: "json-to-elasticsearch",
      name: "JSON到Elasticsearch",
      description: "从JSON文件导入数据到Elasticsearch",
      config: {
        reader: "streamreader",
        writer: "elasticsearchwriter",
      },
    },
  ],
  excel: [
    {
      id: "excel-to-mysql",
      name: "Excel到MySQL",
      description: "从Excel文件导入数据到MySQL数据库",
      config: {
        reader: "streamreader",
        writer: "mysqlwriter",
      },
    },
    {
      id: "excel-to-hive",
      name: "Excel到Hive",
      description: "从Excel文件导入数据到Hive数据仓库",
      config: {
        reader: "streamreader",
        writer: "hdfswriter",
      },
    },
  ],
  xml: [
    {
      id: "xml-to-mysql",
      name: "XML到MySQL",
      description: "从XML文件导入数据到MySQL数据库",
      config: {
        reader: "streamreader",
        writer: "mysqlwriter",
      },
    },
  ],
};

export default function CollectionTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const [templateType, setTemplateType] = useState<"default" | "custom">(
    "default"
  );
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [customConfig, setCustomConfig] = useState("");

  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    type: "immediate",
  });

  const getAvailableTemplates = (fileFormat?: string) => {
    if (!fileFormat) return [];
    return (
      templatesByFormat[fileFormat as keyof typeof templatesByFormat] || []
    );
  };

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
    console.log("Creating task:", {
      ...formData,
      templateType,
      selectedTemplate: templateType === "default" ? selectedTemplate : null,
      customConfig: templateType === "custom" ? customConfig : null,
      scheduleConfig,
    });
    window.alert("任务创建成功！");
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
          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label="数据集名称"
              name="datasetName"
              rules={[{ required: true, message: "请输入数据集名称" }]}
            >
              <Input placeholder="请输入数据集名称" />
            </Form.Item>
            <Form.Item
              label="文件格式"
              name="fileFormat"
              rules={[{ required: true, message: "请选择文件格式" }]}
            >
              <Select
                placeholder="请选择文件格式"
                options={[
                  { value: "csv", label: "CSV" },
                  { value: "json", label: "JSON" },
                  { value: "excel", label: "Excel" },
                  { value: "xml", label: "XML" },
                ]}
                onChange={() => setSelectedTemplate("")}
              />
            </Form.Item>
          </div>
          <Form.Item label="Cron表达式" name="cronExpression">
            <Input placeholder="例如: 0 0 2 * * ?" />
          </Form.Item>
          {/* 高级配置 */}
          <h2 className="font-medium text-gray-900 my-4 text-lg">高级配置</h2>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item label="重试次数" name="retryCount">
              <InputNumber min={0} max={10} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item label="超时时间 (秒)" name="timeout">
              <InputNumber min={60} style={{ width: "100%" }} />
            </Form.Item>
          </div>
          <Form.Item label="增量字段" name="incrementalField">
            <Input placeholder="例如: updated_at" />
          </Form.Item>
          <Form.Item>
            <Radio.Group
              value={scheduleConfig.type}
              onChange={(e) =>
                setScheduleConfig({ ...scheduleConfig, type: e.target.value })
              }
            >
              <Radio value="immediate">立即同步</Radio>
              <Radio value="scheduled">定时任务</Radio>
            </Radio.Group>
          </Form.Item>
          {scheduleConfig.type === "scheduled" && (
            <div className="p-4 bg-gray-50 rounded-md">
              <Form.Item label="调度类型">
                <Select
                  value={scheduleConfig.scheduleType || "daily"}
                  onChange={(value) =>
                    setScheduleConfig({
                      ...scheduleConfig,
                      scheduleType: value,
                    })
                  }
                  options={[
                    { value: "daily", label: "每日" },
                    { value: "weekly", label: "每周" },
                    { value: "monthly", label: "每月" },
                    { value: "custom", label: "自定义" },
                  ]}
                />
              </Form.Item>
              <Form.Item label="执行时间">
                <Input
                  type="time"
                  value={scheduleConfig.time || "00:00"}
                  onChange={(e) =>
                    setScheduleConfig({
                      ...scheduleConfig,
                      time: e.target.value,
                    })
                  }
                />
              </Form.Item>
              {scheduleConfig.scheduleType === "weekly" && (
                <Form.Item label="星期几">
                  <Select
                    value={scheduleConfig.dayOfWeek || "1"}
                    onChange={(value) =>
                      setScheduleConfig({ ...scheduleConfig, dayOfWeek: value })
                    }
                    options={[
                      { value: "1", label: "星期一" },
                      { value: "2", label: "星期二" },
                      { value: "3", label: "星期三" },
                      { value: "4", label: "星期四" },
                      { value: "5", label: "星期五" },
                      { value: "6", label: "星期六" },
                      { value: "0", label: "星期日" },
                    ]}
                  />
                </Form.Item>
              )}
              {scheduleConfig.scheduleType === "monthly" && (
                <Form.Item label="每月第几天">
                  <InputNumber
                    min={1}
                    max={31}
                    value={
                      scheduleConfig.dayOfMonth
                        ? Number(scheduleConfig.dayOfMonth)
                        : 1
                    }
                    onChange={(value) =>
                      setScheduleConfig({
                        ...scheduleConfig,
                        dayOfMonth: String(value),
                      })
                    }
                    className="w-full"
                  />
                </Form.Item>
              )}
              {scheduleConfig.scheduleType === "custom" && (
                <Form.Item label="Cron表达式">
                  <Input
                    placeholder="格式: 分 时 日 月 周 (例如: 0 9 * * 1 表示每周一上午9点)"
                    value={scheduleConfig.cronExpression || ""}
                    onChange={(e) =>
                      setScheduleConfig({
                        ...scheduleConfig,
                        cronExpression: e.target.value,
                      })
                    }
                  />
                </Form.Item>
              )}
              <Form.Item label="最大执行次数">
                <InputNumber
                  min={1}
                  value={scheduleConfig.maxExecutions || 10}
                  onChange={(value) =>
                    setScheduleConfig({
                      ...scheduleConfig,
                      maxExecutions: value ?? 10,
                    })
                  }
                  className="w-full"
                />
              </Form.Item>
            </div>
          )}

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
              {!form.getFieldValue("fileFormat") ? (
                <div className="text-gray-500">请先选择文件格式</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {getAvailableTemplates(form.getFieldValue("fileFormat")).map(
                    (template) => (
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
                        <div className="text-gray-500">
                          {template.description}
                        </div>
                        <div className="text-gray-400">
                          {template.config.reader} → {template.config.writer}
                        </div>
                      </div>
                    )
                  )}
                </div>
              )}
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

          <Divider />
          <div className="flex gap-2 justify-end">
            <Button onClick={() => navigate("/data/collection")}>取消</Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSubmit}
            >
              创建任务
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
