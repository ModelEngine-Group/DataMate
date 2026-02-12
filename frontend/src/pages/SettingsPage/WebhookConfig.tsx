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
import { useTranslation } from "react-i18next";

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

const getAvailableEvents = (t: any): WebhookEvent[] => [
  {
    id: "project_created",
    name: t('settings.webhook.eventTypes.projectCreated.name'),
    description: t('settings.webhook.eventTypes.projectCreated.description'),
    category: t('settings.webhook.events.projectManagement'),
  },
  {
    id: "project_updated",
    name: t('settings.webhook.eventTypes.projectUpdated.name'),
    description: t('settings.webhook.eventTypes.projectUpdated.description'),
    category: t('settings.webhook.events.projectManagement'),
  },
  {
    id: "project_deleted",
    name: t('settings.webhook.eventTypes.projectDeleted.name'),
    description: t('settings.webhook.eventTypes.projectDeleted.description'),
    category: t('settings.webhook.events.projectManagement'),
  },
  {
    id: "task_created",
    name: t('settings.webhook.eventTypes.taskCreated.name'),
    description: t('settings.webhook.eventTypes.taskCreated.description'),
    category: t('settings.webhook.events.taskManagement'),
  },
  {
    id: "task_updated",
    name: t('settings.webhook.eventTypes.taskUpdated.name'),
    description: t('settings.webhook.eventTypes.taskUpdated.description'),
    category: t('settings.webhook.events.taskManagement'),
  },
  {
    id: "task_completed",
    name: t('settings.webhook.eventTypes.taskCompleted.name'),
    description: t('settings.webhook.eventTypes.taskCompleted.description'),
    category: t('settings.webhook.events.taskManagement'),
  },
  {
    id: "annotation_created",
    name: t('settings.webhook.eventTypes.annotationCreated.name'),
    description: t('settings.webhook.eventTypes.annotationCreated.description'),
    category: t('settings.webhook.events.annotationManagement'),
  },
  {
    id: "annotation_updated",
    name: t('settings.webhook.eventTypes.annotationUpdated.name'),
    description: t('settings.webhook.eventTypes.annotationUpdated.description'),
    category: t('settings.webhook.events.annotationManagement'),
  },
  {
    id: "annotation_deleted",
    name: t('settings.webhook.eventTypes.annotationDeleted.name'),
    description: t('settings.webhook.eventTypes.annotationDeleted.description'),
    category: t('settings.webhook.events.annotationManagement'),
  },
  {
    id: "model_trained",
    name: t('settings.webhook.eventTypes.modelTrained.name'),
    description: t('settings.webhook.eventTypes.modelTrained.description'),
    category: t('settings.webhook.events.modelManagement'),
  },
  {
    id: "prediction_created",
    name: t('settings.webhook.eventTypes.predictionCreated.name'),
    description: t('settings.webhook.eventTypes.predictionCreated.description'),
    category: t('settings.webhook.events.predictionManagement'),
  },
];

export default function WebhookConfig() {
  const { t } = useTranslation();
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

  const availableEvents = getAvailableEvents(t);

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
          <h3 className="text-lg font-medium">{t('settings.webhook.title')}</h3>
        </div>
        <Button onClick={handleAddWebhook}>{t('settings.webhook.addWebhook')}</Button>
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
                    text={webhook.status === "active" ? t('settings.webhook.status.active') : t('settings.webhook.status.inactive')}
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 flex items-center gap-2">
                    <ThunderboltOutlined />
                    {webhook.url}
                  </p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm text-gray-500">{t('settings.webhook.details.events')}</span>
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
                      {t('settings.webhook.details.secret')} {webhook.secret.substring(0, 12)}...
                    </span>
                    <span className="flex items-center gap-1">
                      <ReloadOutlined />
                      {t('settings.webhook.details.retry')} {webhook.retryCount}次
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
        title={t('settings.webhook.modal.title')}
        footer={[
          <Button key="cancel" onClick={() => setShowWebhookDialog(false)}>
            {t('dataManagement.actions.cancel')}
          </Button>,
          <Button
            key="ok"
            type="primary"
            onClick={() => setShowWebhookDialog(false)}
          >
            {t('settings.webhook.buttons.create')}
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
          <Form.Item name="name" label={t('settings.webhook.modal.form.name')}>
            <Input placeholder={t('settings.webhook.modal.form.namePlaceholder')} />
          </Form.Item>
          <Form.Item name="retryCount" label={t('settings.webhook.modal.form.retryCount')}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="url" label={t('settings.webhook.modal.form.url')}>
            <Input placeholder={t('settings.webhook.modal.form.urlPlaceholder')} />
          </Form.Item>
          <Form.Item name="secret" label={t('settings.webhook.modal.form.secret')}>
            <Input
              placeholder={t('settings.webhook.modal.form.secretPlaceholder')}
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
          <Form.Item label={t('settings.webhook.modal.form.selectEvents')}>
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
