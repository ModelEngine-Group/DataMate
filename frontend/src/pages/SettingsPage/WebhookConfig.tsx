import { Button, Card, Checkbox, Form, Input, Modal, Badge } from "antd";
import {
  EditOutlined,
  DeleteOutlined,
  KeyOutlined,
  ReloadOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { useState } from "react";

interface WebhookEvent {
  id: string;
  name: string;
  description: string;
  category: string;
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

export default function WebhookConfig() {
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    url: "",
    events: [] as string[],
    secret: "",
    retryCount: 3,
  });
  const [showWebhookDialog, setShowWebhookDialog] = useState(false);
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

  const generateApiKey = () => {
    const chars =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let result = "sk-";
    for (let i = 0; i < 48; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-medium">Webhook 配置</h3>
        </div>
        <Button onClick={handleAddWebhook}>新增Webhook</Button>
      </div>
      <div className="grid gap-4">
        {webhooks.map((webhook) => (
          <Card key={webhook.id}>
            <div className="flex items-start justify-between p-6">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="font-medium">{webhook.name}</span>
                  <Badge
                    status={webhook.status === "active" ? "success" : "default"}
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
                <Button icon={<DeleteOutlined />} size="small" danger />
              </div>
            </div>
          </Card>
        ))}
      </div>
      <Modal
        open={showWebhookDialog}
        onCancel={() => setShowWebhookDialog(false)}
        title="新增 Webhook"
        footer={[
          <Button key="cancel" onClick={() => setShowWebhookDialog(false)}>
            取消
          </Button>,
          <Button
            key="ok"
            type="primary"
            onClick={() => setShowWebhookDialog(false)}
          >
            创建Webhook
          </Button>,
        ]}
      >
        <Form
          layout="vertical"
          initialValues={newWebhook}
          onValuesChange={(changedValues) => {
            setNewWebhook({ ...newWebhook, ...changedValues });
          }}
        >
          <Form.Item name="name" label="Webhook名称">
            <Input placeholder="输入Webhook名称" />
          </Form.Item>
          <Form.Item name="retryCount" label="重试次数">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="url" label="Webhook URL">
            <Input placeholder="https://your-domain.com/webhook" />
          </Form.Item>
          <Form.Item name="secret" label="Secret Key">
            <Input
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
                      <div
                        key={event.id}
                        className="flex items-start space-x-2"
                      >
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
                          <span className="text-sm font-medium">
                            {event.name}
                          </span>
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
    </div>
  );
}
