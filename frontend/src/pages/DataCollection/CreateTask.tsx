import { useState } from "react";
import { Card, Input, Button, Select, Radio, Form, Divider } from "antd";
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

  const [templateType, setTemplateType] = useState<"default" | "custom">(
    "default"
  );
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [customConfig, setCustomConfig] = useState("");

  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    type: "immediate",
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
          <Form.Item label="文件格式" name="fileFormat">
            <Input placeholder="请填写文件格式，使用正则表达式" />
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
