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
  index?: number;
  properties?: Record<string, TemplateFieldDef>;
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
    type: "daily",
    time: "00:00",
    cronExpression: "0 0 * * *",
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

  const parseJsonObjectInput = (value: any) => {
    if (value === undefined || value === null) return value;
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (!trimmed) return undefined;
      const parsed = JSON.parse(trimmed);
      if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
        throw new Error("必须是JSON对象");
      }
      return parsed;
    }
    if (typeof value === "object") {
      if (Array.isArray(value) || value === null) {
        throw new Error("必须是JSON对象");
      }
      return value;
    }
    throw new Error("必须是JSON对象");
  };

  const tryFormatJsonValue = (value: any) => {
    const parsed = parseJsonObjectInput(value);
    if (parsed === undefined) return undefined;
    return JSON.stringify(parsed, null, 2);
  };

  const handleFormatJsonField = (name: (string | number)[]) => {
    const currentValue = form.getFieldValue(name);
    try {
      const formatted = tryFormatJsonValue(currentValue);
      if (formatted !== undefined) {
        form.setFieldValue(name, formatted);
      }
    } catch (error: any) {
      message.error(error?.message || "JSON格式错误");
    }
  };

  const normalizeConfigSection = (
    sectionValue: any,
    defs?: Record<string, TemplateFieldDef>
  ) => {
    if (!defs || typeof defs !== "object") return sectionValue;
    const normalized =
      Array.isArray(sectionValue) ? [...sectionValue] : { ...(sectionValue || {}) };

    Object.entries(defs).forEach(([key, def]) => {
      const fieldType = (def?.type || "input").toLowerCase();
      const required = def?.required !== false;
      const value = sectionValue?.[key];

      if (fieldType === "jsonobject") {
        const parsed = parseJsonObjectInput(value);
        if (parsed === undefined && !required) {
          if (normalized && !Array.isArray(normalized)) {
            delete normalized[key];
          }
        } else if (normalized && !Array.isArray(normalized)) {
          normalized[key] = parsed;
        }
        return;
      }

      if (fieldType === "multiple") {
        if (value && typeof value === "object") {
          normalized[key] = normalizeConfigSection(value, def?.properties);
        }
        return;
      }

      if (fieldType === "multiplelist") {
        if (Array.isArray(value)) {
          normalized[key] = value.map((item) =>
            normalizeConfigSection(item, def?.properties)
          );
        }
      }
    });

    return normalized;
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = { ...newTask, ...values };
      if (payload.syncMode === SyncMode.SCHEDULED) {
        if (!payload.scheduleExpression) {
          payload.scheduleExpression = scheduleExpression.cronExpression;
        }
        if (!payload.scheduleExpression) {
          message.error("请输入Cron表达式");
          return;
        }
      } else {
        delete payload.scheduleExpression;
      }
      if (selectedTemplate?.templateContent) {
        payload.config = {
          ...(payload.config || {}),
          parameter: normalizeConfigSection(
            payload.config?.parameter,
            selectedTemplate.templateContent.parameter
          ),
          reader: normalizeConfigSection(
            payload.config?.reader,
            selectedTemplate.templateContent.reader
          ),
          writer: normalizeConfigSection(
            payload.config?.writer,
            selectedTemplate.templateContent.writer
          ),
        };
      }
      await createTaskUsingPost(payload);
      message.success("任务创建成功");
      navigate("/data/collection");
    } catch (error) {
      message.error(`${error?.data?.message}：${error?.data?.data}`);
    }
  };

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  const renderTemplateFields = (
    section: any[],
    defs: Record<string, TemplateFieldDef> | undefined
  ) => {
    if (!defs || typeof defs !== "object") return null;
    let items_ = []

    Object.entries(defs).sort(([key1, def1], [key2, def2]) => {
      const def1Order = def1?.index || 0;
      const def2Order = def2?.index || 0;
      return def1Order - def2Order;
    }).forEach(([key, def]) => {
      const label = def?.name || key;
      const description = def?.description;
      const fieldType = (def?.type || "input").toLowerCase();
      const required = def?.required !== false;
      const rules: any[] = [];
      if (required) {
        rules.push({ required: true, message: `请输入${label}` });
      }
      if (fieldType === "jsonobject") {
        rules.push({
          validator: (_: any, value: any) => {
            if (
              value === undefined ||
              value === null ||
              (typeof value === "string" && value.trim() === "")
            ) {
              return Promise.resolve();
            }
            try {
              parseJsonObjectInput(value);
              return Promise.resolve();
            } catch (e) {
              return Promise.reject(
                new Error(
                  `JSON格式错误：${(e as Error)?.message || "请输入合法的JSON对象"}`
                )
              );
            }
          },
        });
      }
      const name = section.concat(key)

      switch (fieldType) {
        case "password":
          items_.push((
            <Form.Item
              key={`${section}.${key}`}
              name={name}
              label={label}
              tooltip={description}
              rules={rules}
            >
              <Input.Password placeholder={description || `请输入${label}`} />
            </Form.Item>
          ));
          break;
        case "jsonobject":
          items_.push((
            <Form.Item
              key={`${section}.${key}`}
              name={name}
              label={label}
              tooltip={description}
              rules={rules.length ? rules : undefined}
              extra={(
                <div className="flex justify-end">
                  <Button size="small" onClick={() => handleFormatJsonField(name)}>
                    格式化JSON
                  </Button>
                </div>
              )}
            >
              <TextArea
                placeholder={description || `请输入${label}`}
                autoSize={{ minRows: 4, maxRows: 12 }}
                className="font-mono"
              />
            </Form.Item>
          ));
          break;
        case "selecttag":
          items_.push((
            <Form.Item
              name={name}
              label={label}
              rules={rules.length ? rules : undefined}
            >
              <Select placeholder={description || `请输入${label}`} mode="tags" />
            </Form.Item>
          ));
          break;
        case "select":
        case "option":
          const options = (def?.options || []).map((opt: any) => {
            if (typeof opt === "string" || typeof opt === "number") {
              return { label: String(opt), value: opt };
            }
            return { label: opt?.label ?? String(opt?.value), value: opt?.value };
          });
          items_.push((
            <Form.Item
              key={`${section}.${key}`}
              name={name}
              label={label}
              tooltip={description}
              rules={rules.length ? rules : undefined}
            >
              <Select placeholder={description || `请选择${label}`} options={options} />
            </Form.Item>
          ));
          break;
        case "multiple":
          const itemsMultiple = renderTemplateFields(name, def?.properties)
          items_.push(itemsMultiple)
          break;
        case "multiplelist":
          const realName = name.concat(0)
          const itemsMultipleList = renderTemplateFields(realName, def?.properties)
          items_.push(itemsMultipleList)
          break;
        case "inputlist":
          items_.push((
            <Form.Item
              key={`${section}.${key}`}
              name={name.concat(0)}
              label={label}
              tooltip={description}
              rules={rules.length ? rules : undefined}
            >
              <Input placeholder={description || `请输入${label}`} />
            </Form.Item>
          ));
          break;
        default:
          items_.push((
            <Form.Item
              key={`${section}.${key}`}
              name={name}
              label={label}
              tooltip={description}
              rules={rules.length ? rules : undefined}
            >
              <Input placeholder={description || `请输入${label}`} />
            </Form.Item>
          ));
      }
    })

    return items_
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
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
                    {renderTemplateFields(
                      ["config", "parameter"],
                      selectedTemplate.templateContent?.parameter as Record<string, TemplateFieldDef>
                    )}
                    </div>
                  </>
                ): null}

                {getPropertyCountSafe(selectedTemplate.templateContent?.reader) > 0 ? (
                  <>
                    <h3 className="font-medium text-gray-900 pt-2 mb-2">
                      源端参数
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
                    {renderTemplateFields(
                      ["config", "reader"],
                      selectedTemplate.templateContent?.reader as Record<string, TemplateFieldDef>
                    )}
                    </div>
                  </>
                ) : null}

                {getPropertyCountSafe(selectedTemplate.templateContent?.writer) > 0 ? (
                  <>
                    <h3 className="font-medium text-gray-900 pt-2 mb-2">
                      目标端参数
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
                    {renderTemplateFields(
                      ["config", "writer"],
                      selectedTemplate.templateContent?.writer as Record<string, TemplateFieldDef>
                    )}
                    </div>
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
