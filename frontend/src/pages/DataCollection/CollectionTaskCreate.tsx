"use client";

import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Select,
  Radio,
  Form,
  Typography,
  InputNumber,
} from "antd";
import { SaveOutlined, ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router";

const { TextArea } = Input;
const { Title } = Typography;

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
  const [formData, setFormData] = useState({
    name: "",
    datasetName: "",
    fileFormat: "",
    description: "",
    cronExpression: "",
    retryCount: 3,
    timeout: 3600,
    incrementalField: "",
  });

  const [templateType, setTemplateType] = useState<"default" | "custom">(
    "default"
  );
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [customConfig, setCustomConfig] = useState("");

  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    type: "immediate",
  });

  const handleInputChange = (field: string, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    if (field === "fileFormat") {
      setSelectedTemplate("");
    }
  };

  const getAvailableTemplates = () => {
    if (!formData.fileFormat) return [];
    return (
      templatesByFormat[
        formData.fileFormat as keyof typeof templatesByFormat
      ] || []
    );
  };

  const handleSubmit = () => {
    // Validate form
    if (!formData.name.trim()) {
      window.alert("请填写任务名称");
      return;
    }

    if (!formData.datasetName.trim()) {
      window.alert("请填写数据集名称");
      return;
    }

    if (!formData.fileFormat) {
      window.alert("请选择文件格式");
      return;
    }

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
    });

    window.alert("任务创建成功！");
    navigate("/data/collection");
  };

  return (
    <div style={{ gap: 24, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate("/data/collection")}
        />
        <div>
          <Title level={5} style={{ margin: 0 }}>
            创建数据归集任务
          </Title>
        </div>
      </div>

      <Card>
        <Form layout="vertical">
          {/* 基本信息 */}
          <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 8 }}>
            基本信息
          </div>
          <Form.Item label="任务名称 *" required>
            <Input
              placeholder="请输入任务名称"
              value={formData.name}
              onChange={(e) => handleInputChange("name", e.target.value)}
            />
          </Form.Item>
          <Form.Item label="数据集名称 *" required>
            <Input
              placeholder="请输入数据集名称"
              value={formData.datasetName}
              onChange={(e) => handleInputChange("datasetName", e.target.value)}
            />
          </Form.Item>
          <Form.Item label="文件格式 *" required>
            <Select
              placeholder="请选择文件格式"
              value={formData.fileFormat || undefined}
              onChange={(value) => handleInputChange("fileFormat", value)}
              options={[
                { value: "csv", label: "CSV" },
                { value: "json", label: "JSON" },
                { value: "excel", label: "Excel" },
                { value: "xml", label: "XML" },
              ]}
            />
          </Form.Item>
          <Form.Item label="描述">
            <TextArea
              placeholder="请输入任务描述"
              value={formData.description}
              onChange={(e) => handleInputChange("description", e.target.value)}
              rows={3}
            />
          </Form.Item>
          <Form.Item label="Cron表达式">
            <Input
              placeholder="例如: 0 0 2 * * ?"
              value={formData.cronExpression}
              onChange={(e) =>
                handleInputChange("cronExpression", e.target.value)
              }
            />
          </Form.Item>

          {/* 高级配置 */}
          <div
            style={{ fontWeight: 600, fontSize: 16, margin: "24px 0 8px 0" }}
          >
            高级配置
          </div>
          <Form.Item label="重试次数">
            <InputNumber
              min={0}
              max={10}
              value={formData.retryCount}
              onChange={(value) => handleInputChange("retryCount", value ?? 0)}
              style={{ width: "100%" }}
            />
          </Form.Item>
          <Form.Item label="超时时间 (秒)">
            <InputNumber
              min={60}
              value={formData.timeout}
              onChange={(value) => handleInputChange("timeout", value ?? 3600)}
              style={{ width: "100%" }}
            />
          </Form.Item>
          <Form.Item label="增量字段">
            <Input
              placeholder="例如: updated_at"
              value={formData.incrementalField}
              onChange={(e) =>
                handleInputChange("incrementalField", e.target.value)
              }
            />
          </Form.Item>

          {/* 同步配置 */}
          <div
            style={{ fontWeight: 600, fontSize: 16, margin: "24px 0 8px 0" }}
          >
            同步配置
          </div>
          <Form.Item label="同步方式">
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
            <div
              style={{
                background: "#f9f0ff",
                borderRadius: 8,
                padding: 16,
                marginTop: 8,
              }}
            >
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
                    style={{ width: "100%" }}
                  />
                </Form.Item>
              )}
              {scheduleConfig.scheduleType === "custom" && (
                <Form.Item label="Cron表达式">
                  <Input
                    placeholder="0 0 * * *"
                    value={scheduleConfig.cronExpression || ""}
                    onChange={(e) =>
                      setScheduleConfig({
                        ...scheduleConfig,
                        cronExpression: e.target.value,
                      })
                    }
                  />
                  <div style={{ fontSize: 12, color: "#888" }}>
                    格式: 分 时 日 月 周 (例如: 0 9 * * 1 表示每周一上午9点)
                  </div>
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
                  style={{ width: "100%" }}
                />
              </Form.Item>
            </div>
          )}

          {/* 模板配置 */}
          <div
            style={{ fontWeight: 600, fontSize: 16, margin: "24px 0 8px 0" }}
          >
            模板配置
          </div>
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
              {!formData.fileFormat ? (
                <div style={{ color: "#888" }}>请先选择文件格式</div>
              ) : (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 12,
                  }}
                >
                  {getAvailableTemplates().map((template) => (
                    <div
                      key={template.id}
                      style={{
                        border:
                          selectedTemplate === template.id
                            ? "2px solid #1677ff"
                            : "1px solid #eee",
                        borderRadius: 8,
                        background:
                          selectedTemplate === template.id ? "#e6f7ff" : "#fff",
                        padding: 12,
                        cursor: "pointer",
                      }}
                      onClick={() => setSelectedTemplate(template.id)}
                    >
                      <div style={{ fontWeight: 500 }}>{template.name}</div>
                      <div
                        style={{ color: "#888", fontSize: 13, margin: "4px 0" }}
                      >
                        {template.description}
                      </div>
                      <div style={{ fontSize: 12, color: "#aaa" }}>
                        {template.config.reader} → {template.config.writer}
                      </div>
                    </div>
                  ))}
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
                style={{ fontFamily: "monospace", fontSize: 13 }}
              />
            </Form.Item>
          )}

          {/* Actions */}
          <Form.Item>
            <div
              style={{ display: "flex", justifyContent: "flex-end", gap: 16 }}
            >
              <Button onClick={() => navigate("/data/collection")}>取消</Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSubmit}
              >
                创建任务
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
