;

import { useState } from "react";
import {
  Button,
  Card,
  Input,
  Switch,
  Select,
  Tabs,
  Badge,
  Checkbox,
  Divider,
  Modal,
  Form,
  message,
} from "antd";
import {
  SettingOutlined,
  DatabaseOutlined,
  ApiOutlined,
  BellOutlined,
  SaveOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  KeyOutlined,
  CopyOutlined,
  ReloadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  ExperimentOutlined,
  CloudServerOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

interface CallbackConfig {
  id: string;
  name: string;
  url: string;
  method: string;
  status: "active" | "inactive";
  events: string[];
}

interface EnvironmentConfig {
  id: string;
  name: string;
  type: string;
  endpoint: string;
  status: "connected" | "disconnected" | "error";
  lastSync: string;
}

interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  events: string[];
  status: "active" | "inactive";
  secret: string;
  retryCount: number;
}

interface VectorDBConfig {
  id: string;
  name: string;
  type: "pinecone" | "weaviate" | "qdrant" | "milvus" | "chroma";
  url: string;
  apiKey: string;
  dimension: number;
  metric: string;
  status: "connected" | "disconnected" | "error";
}

interface ModelConfig {
  id: string;
  name: string;
  provider: "openai" | "anthropic" | "google" | "azure" | "local";
  model: string;
  apiKey: string;
  endpoint?: string;
  status: "active" | "inactive";
  usage: number;
}

interface WebhookEvent {
  id: string;
  name: string;
  description: string;
  category: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("system");
  const [showApiKey, setShowApiKey] = useState<{ [key: string]: boolean }>({});
  const [showWebhookDialog, setShowWebhookDialog] = useState(false);
  const [showVectorDBDialog, setShowVectorDBDialog] = useState(false);
  const [showModelDialog, setShowModelDialog] = useState(false);

  // System Settings State
  const [systemConfig, setSystemConfig] = useState({
    siteName: "ML Dataset Tool",
    maxFileSize: "100",
    autoBackup: true,
    logLevel: "info",
    sessionTimeout: "30",
    enableNotifications: true,
  });

  // Callback Registration State
  const [callbacks, setCallbacks] = useState<CallbackConfig[]>([
    {
      id: "1",
      name: "数据处理完成回调",
      url: "https://api.example.com/callback/process-complete",
      method: "POST",
      status: "active",
      events: ["process_complete", "process_failed"],
    },
    {
      id: "2",
      name: "任务状态更新",
      url: "https://api.example.com/callback/task-update",
      method: "POST",
      status: "inactive",
      events: ["task_created", "task_updated", "task_completed"],
    },
  ]);

  // Environment Integration State
  const [environments, setEnvironments] = useState<EnvironmentConfig[]>([
    {
      id: "1",
      name: "生产环境数据库",
      type: "MySQL",
      endpoint: "mysql://prod.example.com:3306",
      status: "connected",
      lastSync: "2025-01-18 14:30:00",
    },
    {
      id: "2",
      name: "测试环境API",
      type: "REST API",
      endpoint: "https://test-api.example.com",
      status: "error",
      lastSync: "2025-01-18 12:15:00",
    },
  ]);

  const [vectorDBs, setVectorDBs] = useState<VectorDBConfig[]>([
    {
      id: "1",
      name: "Pinecone Production",
      type: "pinecone",
      url: "https://your-index.svc.us-east1-gcp.pinecone.io",
      apiKey: "pc-****-****-****",
      dimension: 1536,
      metric: "cosine",
      status: "connected",
    },
    {
      id: "2",
      name: "Weaviate Local",
      type: "weaviate",
      url: "http://localhost:8080",
      apiKey: "",
      dimension: 768,
      metric: "cosine",
      status: "disconnected",
    },
  ]);

  const [models, setModels] = useState<ModelConfig[]>([
    {
      id: "1",
      name: "GPT-4 Turbo",
      provider: "openai",
      model: "gpt-4-turbo-preview",
      apiKey: "sk-****-****-****",
      status: "active",
      usage: 85,
    },
    {
      id: "2",
      name: "Claude 3 Sonnet",
      provider: "anthropic",
      model: "claude-3-sonnet-20240229",
      apiKey: "sk-ant-****-****",
      status: "active",
      usage: 42,
    },
  ]);

  const availableEvents: WebhookEvent[] = [
    {
      id: "project_created",
      name: "项目创建",
      description: "新项目被创建时触发",
      category: "项目管理",
    },
    {
      id: "project_updated",
      name: "项目更新",
      description: "项目信息被修改时触发",
      category: "项目管理",
    },
    {
      id: "project_deleted",
      name: "项目删除",
      description: "项目被删除时触发",
      category: "项目管理",
    },
    {
      id: "task_created",
      name: "任务创建",
      description: "新任务被创建时触发",
      category: "任务管理",
    },
    {
      id: "task_updated",
      name: "任务更新",
      description: "任务状态或内容被更新时触发",
      category: "任务管理",
    },
    {
      id: "task_completed",
      name: "任务完成",
      description: "任务被标记为完成时触发",
      category: "任务管理",
    },
    {
      id: "annotation_created",
      name: "标注创建",
      description: "新标注被创建时触发",
      category: "标注管理",
    },
    {
      id: "annotation_updated",
      name: "标注更新",
      description: "标注被修改时触发",
      category: "标注管理",
    },
    {
      id: "annotation_deleted",
      name: "标注删除",
      description: "标注被删除时触发",
      category: "标注管理",
    },
    {
      id: "model_trained",
      name: "模型训练完成",
      description: "模型训练任务完成时触发",
      category: "模型管理",
    },
    {
      id: "prediction_created",
      name: "预测生成",
      description: "新预测结果生成时触发",
      category: "预测管理",
    },
  ];

  // Webhook State
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([
    {
      id: "1",
      name: "数据同步Webhook",
      url: "https://webhook.example.com/data-sync",
      events: ["task_created", "task_completed", "annotation_created"],
      status: "active",
      secret: "wh_secret_123456",
      retryCount: 3,
    },
    {
      id: "2",
      name: "任务通知Webhook",
      url: "https://webhook.example.com/task-notify",
      events: ["task_started", "task_completed", "task_failed"],
      status: "inactive",
      secret: "wh_secret_789012",
      retryCount: 5,
    },
  ]);

  const [newWebhook, setNewWebhook] = useState({
    name: "",
    url: "",
    events: [] as string[],
    secret: "",
    retryCount: 3,
  });
  const [newVectorDB, setNewVectorDB] = useState({
    name: "",
    type: "pinecone",
    url: "",
    apiKey: "",
    dimension: 1536,
    metric: "cosine",
  });
  const [newModel, setNewModel] = useState({
    name: "",
    provider: "openai",
    model: "",
    apiKey: "",
    endpoint: "",
  });

  const generateApiKey = () => {
    const chars =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let result = "sk-";
    for (let i = 0; i < 48; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const toggleApiKeyVisibility = (id: string) => {
    setShowApiKey((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSaveSystemSettings = () => {
    // Save system settings logic
    console.log("Saving system settings:", systemConfig);
  };

  const handleAddCallback = () => {
    // Add new callback logic
    console.log("Adding new callback");
  };

  const handleAddEnvironment = () => {
    // Add new environment logic
    console.log("Adding new environment");
  };

  const handleAddWebhook = () => {
    setNewWebhook({
      name: "",
      url: "",
      events: [],
      secret: generateApiKey(),
      retryCount: 3,
    });
    setShowWebhookDialog(true);
  };

  const handleAddVectorDB = () => {
    setNewVectorDB({
      name: "",
      type: "pinecone",
      url: "",
      apiKey: "",
      dimension: 1536,
      metric: "cosine",
    });
    setShowVectorDBDialog(true);
  };

  const handleAddModel = () => {
    setNewModel({
      name: "",
      provider: "openai",
      model: "",
      apiKey: generateApiKey(),
      endpoint: "",
    });
    setShowModelDialog(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">系统设置</h1>
        </div>
      </div>

      {/* Settings Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className="space-y-6"
        items={[
          {
            key: "system",
            label: (
              <span>
                <SettingOutlined className="mr-1" />
                系统设置
              </span>
            ),
            children: (
              <Card>
                <Divider orientation="left">
                  <SettingOutlined /> 基础设置
                </Divider>
                <Form layout="vertical">
                  <div className="grid grid-cols-2 gap-6">
                    <Form.Item label="站点名称">
                      <Input
                        value={systemConfig.siteName}
                        onChange={(e) =>
                          setSystemConfig({
                            ...systemConfig,
                            siteName: e.target.value,
                          })
                        }
                      />
                    </Form.Item>
                    <Form.Item label="最大文件大小 (MB)">
                      <Input
                        type="number"
                        value={systemConfig.maxFileSize}
                        onChange={(e) =>
                          setSystemConfig({
                            ...systemConfig,
                            maxFileSize: e.target.value,
                          })
                        }
                      />
                    </Form.Item>
                    <Form.Item label="日志级别">
                      <Select
                        value={systemConfig.logLevel}
                        onChange={(value) =>
                          setSystemConfig({ ...systemConfig, logLevel: value })
                        }
                      >
                        <Option value="debug">Debug</Option>
                        <Option value="info">Info</Option>
                        <Option value="warn">Warning</Option>
                        <Option value="error">Error</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item label="会话超时 (分钟)">
                      <Input
                        type="number"
                        value={systemConfig.sessionTimeout}
                        onChange={(e) =>
                          setSystemConfig({
                            ...systemConfig,
                            sessionTimeout: e.target.value,
                          })
                        }
                      />
                    </Form.Item>
                  </div>
                  <Divider />
                  <div className="space-y-4">
                    <h4 className="font-medium">功能开关</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <span>自动备份</span>
                          <p className="text-sm text-gray-500">
                            定期自动备份系统数据
                          </p>
                        </div>
                        <Switch
                          checked={systemConfig.autoBackup}
                          onChange={(checked) =>
                            setSystemConfig({
                              ...systemConfig,
                              autoBackup: checked,
                            })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <span>启用通知</span>
                          <p className="text-sm text-gray-500">
                            接收系统通知和提醒
                          </p>
                        </div>
                        <Switch
                          checked={systemConfig.enableNotifications}
                          onChange={(checked) =>
                            setSystemConfig({
                              ...systemConfig,
                              enableNotifications: checked,
                            })
                          }
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-end mt-6">
                    <Button
                      type="primary"
                      icon={<SaveOutlined />}
                      onClick={handleSaveSystemSettings}
                    >
                      保存设置
                    </Button>
                  </div>
                </Form>
              </Card>
            ),
          },
          {
            key: "environment",
            label: (
              <span>
                <DatabaseOutlined className="mr-1" />
                环境接入
              </span>
            ),
            children: (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <Divider orientation="left">
                    <CloudServerOutlined /> 向量数据库
                  </Divider>
                  <div className="flex justify-end mb-2">
                    <Button
                      icon={<PlusOutlined />}
                      onClick={handleAddVectorDB}
                      size="small"
                    >
                      添加向量库
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {vectorDBs.map((db) => (
                      <Card key={db.id} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{db.name}</span>
                            <Badge
                              status={
                                db.status === "connected"
                                  ? "success"
                                  : db.status === "error"
                                  ? "error"
                                  : "default"
                              }
                              text={
                                db.status === "connected"
                                  ? "已连接"
                                  : db.status === "error"
                                  ? "异常"
                                  : "未连接"
                              }
                            />
                          </div>
                          <div className="flex items-center gap-1">
                            <Button icon={<ExperimentOutlined />} size="small" />
                            <Button icon={<EditOutlined />} size="small" />
                            <Button
                              icon={<DeleteOutlined />}
                              size="small"
                              danger
                            />
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>类型: {db.type}</p>
                          <p>地址: {db.url}</p>
                          <p>
                            维度: {db.dimension} | 距离度量: {db.metric}
                          </p>
                        </div>
                      </Card>
                    ))}
                  </div>
                </Card>
                <Card>
                  <Divider orientation="left">
                    <ThunderboltOutlined /> 模型接入
                  </Divider>
                  <div className="flex justify-end mb-2">
                    <Button
                      icon={<PlusOutlined />}
                      onClick={handleAddModel}
                      size="small"
                    >
                      添加模型
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {models.map((model) => (
                      <Card key={model.id} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{model.name}</span>
                            <Badge
                              status={model.status === "active" ? "success" : "default"}
                              text={model.status === "active" ? "启用" : "禁用"}
                            />
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              icon={
                                showApiKey[model.id] ? (
                                  <EyeInvisibleOutlined />
                                ) : (
                                  <EyeOutlined />
                                )
                              }
                              size="small"
                              onClick={() => toggleApiKeyVisibility(model.id)}
                            />
                            <Button icon={<ReloadOutlined />} size="small" />
                            <Button icon={<EditOutlined />} size="small" />
                            <Button
                              icon={<DeleteOutlined />}
                              size="small"
                              danger
                            />
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>提供商: {model.provider}</p>
                          <p>模型: {model.model}</p>
                          <div className="flex items-center gap-2">
                            <span>API Key:</span>
                            <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                              {showApiKey[model.id]
                                ? model.apiKey
                                : "sk-****-****-****"}
                            </code>
                            <Button
                              icon={<CopyOutlined />}
                              size="small"
                              onClick={() =>
                                navigator.clipboard.writeText(model.apiKey)
                              }
                            />
                          </div>
                          <div className="flex items-center gap-2">
                            <span>使用率:</span>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full"
                                style={{ width: `${model.usage}%` }}
                              />
                            </div>
                            <span className="text-xs">{model.usage}%</span>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </Card>
              </div>
            ),
          },
          {
            key: "webhook",
            label: (
              <span>
                <ApiOutlined className="mr-1" />
                Webhook
              </span>
            ),
            children: (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium">Webhook 配置</h3>
                    <p className="text-gray-600">
                      管理系统事件的Webhook通知，类似Label Studio的事件系统
                    </p>
                  </div>
                  <Button
                    icon={<PlusOutlined />}
                    onClick={handleAddWebhook}
                  >
                    新增Webhook
                  </Button>
                </div>
                <div className="grid gap-4">
                  {webhooks.map((webhook) => (
                    <Card key={webhook.id}>
                      <div className="flex items-start justify-between p-6">
                        <div className="space-y-3">
                          <div className="flex items-center gap-3">
                            <span className="font-medium">{webhook.name}</span>
                            <Badge
                              status={
                                webhook.status === "active"
                                  ? "success"
                                  : "default"
                              }
                              text={webhook.status === "active" ? "启用" : "禁用"}
                            />
                          </div>
                          <div className="space-y-2">
                            <p className="text-sm text-gray-600 flex items-center gap-2">
                              <ThunderboltOutlined />
                              {webhook.url}
                            </p>
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-sm text-gray-500">事件:</span>
                              {webhook.events.map((event) => {
                                const eventInfo = availableEvents.find(
                                  (e) => e.id === event
                                );
                                return (
                                  <Badge
                                    key={event}
                                    status="default"
                                    text={eventInfo?.name || event}
                                  />
                                );
                              })}
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <span className="flex items-center gap-1">
                                <KeyOutlined />
                                Secret: {webhook.secret.substring(0, 12)}...
                              </span>
                              <span className="flex items-center gap-1">
                                <ReloadOutlined />
                                重试: {webhook.retryCount}次
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button icon={<ExperimentOutlined />} size="small" />
                          <Button icon={<EditOutlined />} size="small" />
                          <Button
                            icon={<DeleteOutlined />}
                            size="small"
                            danger
                          />
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ),
          },
        ]}
      />

      {/* Webhook Modal */}
      <Modal
        open={showWebhookDialog}
        onCancel={() => setShowWebhookDialog(false)}
        title="新增 Webhook"
        footer={[
          <Button key="cancel" onClick={() => setShowWebhookDialog(false)}>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={() => setShowWebhookDialog(false)}>
            创建Webhook
          </Button>,
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="Webhook名称">
            <Input
              value={newWebhook.name}
              onChange={(e) =>
                setNewWebhook({ ...newWebhook, name: e.target.value })
              }
              placeholder="输入Webhook名称"
            />
          </Form.Item>
          <Form.Item label="重试次数">
            <Input
              type="number"
              value={newWebhook.retryCount}
              onChange={(e) =>
                setNewWebhook({
                  ...newWebhook,
                  retryCount: Number.parseInt(e.target.value),
                })
              }
            />
          </Form.Item>
          <Form.Item label="Webhook URL">
            <Input
              value={newWebhook.url}
              onChange={(e) =>
                setNewWebhook({ ...newWebhook, url: e.target.value })
              }
              placeholder="https://your-domain.com/webhook"
            />
          </Form.Item>
          <Form.Item label="Secret Key">
            <Input
              value={newWebhook.secret}
              onChange={(e) =>
                setNewWebhook({ ...newWebhook, secret: e.target.value })
              }
              placeholder="用于验证Webhook请求的密钥"
              addonAfter={
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() =>
                    setNewWebhook({ ...newWebhook, secret: generateApiKey() })
                  }
                />
              }
            />
          </Form.Item>
          <Form.Item label="选择事件">
            <div className="max-h-48 overflow-y-auto border rounded-lg p-3 space-y-3">
              {Object.entries(
                availableEvents.reduce((acc, event) => {
                  if (!acc[event.category]) acc[event.category] = [];
                  acc[event.category].push(event);
                  return acc;
                }, {} as Record<string, WebhookEvent[]>)
              ).map(([category, events]) => (
                <div key={category} className="space-y-2">
                  <h4 className="font-medium text-sm text-gray-700">
                    {category}
                  </h4>
                  <div className="space-y-2 pl-4">
                    {events.map((event) => (
                      <div key={event.id} className="flex items-start space-x-2">
                        <Checkbox
                          checked={newWebhook.events.includes(event.id)}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            if (checked) {
                              setNewWebhook({
                                ...newWebhook,
                                events: [...newWebhook.events, event.id],
                              });
                            } else {
                              setNewWebhook({
                                ...newWebhook,
                                events: newWebhook.events.filter(
                                  (ev) => ev !== event.id
                                ),
                              });
                            }
                          }}
                        >
                          <span className="text-sm font-medium">{event.name}</span>
                        </Checkbox>
                        <span className="text-xs text-gray-500">
                          {event.description}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Form.Item>
        </Form>
      </Modal>

      {/* VectorDB Modal */}
      <Modal
        open={showVectorDBDialog}
        onCancel={() => setShowVectorDBDialog(false)}
        title="添加向量数据库"
        footer={[
          <Button key="cancel" onClick={() => setShowVectorDBDialog(false)}>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={() => setShowVectorDBDialog(false)}>
            添加数据库
          </Button>,
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="数据库名称">
            <Input
              value={newVectorDB.name}
              onChange={(e) =>
                setNewVectorDB({ ...newVectorDB, name: e.target.value })
              }
              placeholder="输入数据库名称"
            />
          </Form.Item>
          <Form.Item label="数据库类型">
            <Select
              value={newVectorDB.type}
              onChange={(value) =>
                setNewVectorDB({ ...newVectorDB, type: value })
              }
            >
              <Option value="pinecone">Pinecone</Option>
              <Option value="weaviate">Weaviate</Option>
              <Option value="qdrant">Qdrant</Option>
              <Option value="milvus">Milvus</Option>
              <Option value="chroma">Chroma</Option>
            </Select>
          </Form.Item>
          <Form.Item label="连接地址">
            <Input
              value={newVectorDB.url}
              onChange={(e) =>
                setNewVectorDB({ ...newVectorDB, url: e.target.value })
              }
              placeholder="https://your-index.svc.region.pinecone.io"
            />
          </Form.Item>
          <Form.Item label="API Key">
            <Input
              type="password"
              value={newVectorDB.apiKey}
              onChange={(e) =>
                setNewVectorDB({ ...newVectorDB, apiKey: e.target.value })
              }
              placeholder="输入API密钥"
            />
          </Form.Item>
          <Form.Item label="向量维度">
            <Input
              type="number"
              value={newVectorDB.dimension}
              onChange={(e) =>
                setNewVectorDB({
                  ...newVectorDB,
                  dimension: Number.parseInt(e.target.value),
                })
              }
            />
          </Form.Item>
          <Form.Item label="距离度量">
            <Select
              value={newVectorDB.metric}
              onChange={(value) =>
                setNewVectorDB({ ...newVectorDB, metric: value })
              }
            >
              <Option value="cosine">Cosine</Option>
              <Option value="euclidean">Euclidean</Option>
              <Option value="dotproduct">Dot Product</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Model Modal */}
      <Modal
        open={showModelDialog}
        onCancel={() => setShowModelDialog(false)}
        title="添加AI模型"
        footer={[
          <Button key="cancel" onClick={() => setShowModelDialog(false)}>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={() => setShowModelDialog(false)}>
            添加模型
          </Button>,
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="模型名称">
            <Input
              value={newModel.name}
              onChange={(e) =>
                setNewModel({ ...newModel, name: e.target.value })
              }
              placeholder="输入模型名称"
            />
          </Form.Item>
          <Form.Item label="服务提供商">
            <Select
              value={newModel.provider}
              onChange={(value) =>
                setNewModel({ ...newModel, provider: value })
              }
            >
              <Option value="openai">OpenAI</Option>
              <Option value="anthropic">Anthropic</Option>
              <Option value="google">Google</Option>
              <Option value="azure">Azure</Option>
              <Option value="local">本地部署</Option>
            </Select>
          </Form.Item>
          <Form.Item label="模型标识">
            <Input
              value={newModel.model}
              onChange={(e) =>
                setNewModel({ ...newModel, model: e.target.value })
              }
              placeholder="gpt-4-turbo-preview"
            />
          </Form.Item>
          <Form.Item label="API Key">
            <Input
              value={newModel.apiKey}
              onChange={(e) =>
                setNewModel({ ...newModel, apiKey: e.target.value })
              }
              placeholder="输入或生成API密钥"
              addonAfter={
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() =>
                    setNewModel({ ...newModel, apiKey: generateApiKey() })
                  }
                />
              }
            />
          </Form.Item>
          {newModel.provider === "local" && (
            <Form.Item label="自定义端点">
              <Input
                value={newModel.endpoint}
                onChange={(e) =>
                  setNewModel({ ...newModel, endpoint: e.target.value })
                }
                placeholder="http://localhost:8000/v1"
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
