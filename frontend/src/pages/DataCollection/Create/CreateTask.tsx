import { useEffect, useState } from "react";
import { Input, Button, Radio, Form, App, Select, InputNumber } from "antd";
import { Link, useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { createTaskUsingPost, queryDataXTemplatesUsingGet } from "../collection.apis";
import SimpleCronScheduler from "@/pages/DataCollection/Create/SimpleCronScheduler";
import { SyncModeMap } from "../collection.const";
import { SyncMode } from "../collection.model";

const { TextArea } = Input;

const syncModeOptions = Object.values(SyncModeMap);

type CollectionTemplate = {
  id: string;
  name: string;
  description?: string;
  sourceType?: string;
  sourceName?: string;
  targetType?: string;
  targetName?: string;
  templateContent?: {
    parameter?: any;
    reader?: any;
    writer?: any;
  };
  builtIn?: boolean;
};

type TemplateFieldDef = {
  name?: string;
  type?: string;
  description?: string;
  required?: boolean;
  options?: Array<{ label: string; value: string | number } | string | number>;
  defaultValue?: any;
};

export default function CollectionTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const [templates, setTemplates] = useState<CollectionTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | undefined>(undefined);

  const [newTask, setNewTask] = useState<any>({
    name: "",
    description: "",
    syncMode: SyncMode.ONCE,
    scheduleExpression: "",
    timeoutSeconds: 3600,
    templateId: "",
    config: {
      parameter: {},
    },
  });
  const [scheduleExpression, setScheduleExpression] = useState({
    type: "once",
    time: "00:00",
    cronExpression: "0 0 0 * * ?",
  });

  useEffect(() => {
    const run = async () => {
      setTemplatesLoading(true);
      try {
        const resp: any = await queryDataXTemplatesUsingGet({ page: 1, size: 1000 });
        const list: CollectionTemplate[] = resp?.data?.content || [];
        setTemplates(list);
      } catch (e) {
        message.error("加载归集模板失败");
      } finally {
        setTemplatesLoading(false);
      }
    };
    run()
  }, []);

  const handleSubmit = async () => {
    try {
      await form.validateFields();

      const values = form.getFieldsValue(true);
      const payload = {
        name: values.name,
        description: values.description,
        syncMode: values.syncMode,
        scheduleExpression: values.scheduleExpression,
        timeoutSeconds: values.timeoutSeconds,
        templateId: values.templateId,
        config: values.config,
      };

      await createTaskUsingPost(payload);
      message.success("任务创建成功");
      navigate("/data/collection");
    } catch (error) {
      message.error(`${error?.data?.message}：${error?.data?.data}`);
    }
  };

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  const renderTemplateFields = (
    section: "parameter" | "reader" | "writer",
    defs: Record<string, TemplateFieldDef> | undefined
  ) => {
    if (!defs || typeof defs !== "object") return null;

    const items = Object.entries(defs).map(([key, def]) => {
      const label = def?.name || key;
      const description = def?.description;
      const fieldType = (def?.type || "input").toLowerCase();
      const required = def?.required !== false;

      const rules = required
        ? [{ required: true, message: `请输入${label}` }]
        : undefined;

      if (fieldType === "password") {
        return (
          <Form.Item
            key={`${section}.${key}`}
            name={["config", section, key]}
            label={label}
            tooltip={description}
            rules={rules}
          >
            <Input.Password placeholder={description || `请输入${label}`} />
          </Form.Item>
        );
      }

      if (fieldType === "textarea") {
        return (
          <Form.Item
            key={`${section}.${key}`}
            name={["config", section, key]}
            label={label}
            tooltip={description}
            rules={rules}
            className="md:col-span-2"
          >
            <TextArea rows={4} placeholder={description || `请输入${label}`} />
          </Form.Item>
        );
      }

      if (fieldType === "select") {
        const options = (def?.options || []).map((opt: any) => {
          if (typeof opt === "string" || typeof opt === "number") {
            return { label: String(opt), value: opt };
          }
          return { label: opt?.label ?? String(opt?.value), value: opt?.value };
        });
        return (
          <Form.Item
            key={`${section}.${key}`}
            name={["config", section, key]}
            label={label}
            tooltip={description}
            rules={rules}
          >
            <Select placeholder={description || `请选择${label}`} options={options} />
          </Form.Item>
        );
      }

      return (
        <Form.Item
          key={`${section}.${key}`}
          name={["config", section, key]}
          label={label}
          tooltip={description}
          rules={rules}
        >
          <Input placeholder={description || `请输入${label}`} />
        </Form.Item>
      );
    });

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
        {items}
      </div>
    );
  };

  const getPropertyCountSafe = (obj: any) => {
    // 类型检查
    if (obj === null || obj === undefined) {
      return 0;
    }
    // 处理普通对象
    return Object.keys(obj).length;
  }

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
        <div className="flex-1 overflow-auto p-4">
          <Form
            form={form}
            layout="vertical"
            className="[&_.ant-form-item]:mb-3 [&_.ant-form-item-label]:pb-1"
            initialValues={newTask}
            onValuesChange={(_, allValues) => {
              setNewTask({ ...newTask, ...allValues });
            }}
          >
            {/* 基本信息 */}
            <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
              <Form.Item
                label="名称"
                name="name"
                rules={[{ required: true, message: "请输入任务名称" }]}
              >
                <Input placeholder="请输入任务名称" />
              </Form.Item>

              <Form.Item
                label="超时时间（秒）"
                name="timeoutSeconds"
                rules={[{ required: true, message: "请输入超时时间" }]}
                initialValue={3600}
              >
                <InputNumber
                  className="w-full"
                  min={1}
                  precision={0}
                  placeholder="默认 3600"
                />
              </Form.Item>

              <Form.Item className="md:col-span-2" label="描述" name="description">
                <TextArea placeholder="请输入任务描述" rows={2} />
              </Form.Item>
            </div>

            {/* 同步配置 */}
            <h2 className="font-medium text-gray-900 pt-2 mb-1 text-lg">
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
                  className="px-2 py-1 rounded"
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

            {/* 模板配置 */}
            <h2 className="font-medium text-gray-900 pt-4 mb-2 text-lg">
              模板配置
            </h2>

            <Form.Item
              label="选择模板"
              name="templateId"
              rules={[{ required: true, message: "请选择归集模板" }]}
            >
              <Select
                placeholder="请选择归集模板"
                loading={templatesLoading}
                onChange={(templateId) => {
                  setSelectedTemplateId(templateId);
                  form.setFieldsValue({
                    templateId,
                    config: {},
                  });
                  setNewTask((prev: any) => ({
                    ...prev,
                    templateId,
                    config: {},
                  }));
                }}
                optionRender={(option) => {
                  const tpl = templates.find((t) => t.id === option.value);
                  return (
                    <div>
                      <div className="font-medium">{tpl?.name || option.label}</div>
                      <div className="text-xs text-gray-500 line-clamp-2">
                        {tpl?.description || ""}
                      </div>
                    </div>
                  );
                }}
                options={templates.map((template) => ({
                  label: template.name,
                  value: template.id,
                }))}
              />
            </Form.Item>

            {selectedTemplate ? (
              <>
                {getPropertyCountSafe(selectedTemplate.templateContent?.parameter) > 0 ? (
                  <>
                    <h3 className="font-medium text-gray-900 pt-2 mb-2">
                      模板参数
                    </h3>
                    {renderTemplateFields(
                      "parameter",
                      selectedTemplate.templateContent?.parameter as Record<string, TemplateFieldDef>
                    )}
                  </>
                ): null}

                {getPropertyCountSafe(selectedTemplate.templateContent?.reader) > 0 ? (
                  <>
                    <h3 className="font-medium text-gray-900 pt-2 mb-2">
                      源端参数
                    </h3>
                    {renderTemplateFields(
                      "reader",
                      selectedTemplate.templateContent?.reader as Record<string, TemplateFieldDef>
                    )}
                  </>
                ) : null}

                {getPropertyCountSafe(selectedTemplate.templateContent?.writer) > 0 ? (
                  <>
                    <h3 className="font-medium text-gray-900 pt-2 mb-2">
                      目标端参数
                    </h3>
                    {renderTemplateFields(
                      "writer",
                      selectedTemplate.templateContent?.writer as Record<string, TemplateFieldDef>
                    )}
                  </>
                ) : null}
              </>
            ) : null}
          </Form>
        </div>
        <div className="flex gap-2 justify-end border-top p-4">
          <Button onClick={() => navigate("/data/collection")}>取消</Button>
          <Button type="primary" onClick={handleSubmit}>
            创建任务
          </Button>
        </div>
      </div>
    </div>
  );
}
