import { useEffect, useState } from "react";
import { Input, Button, Radio, Form, App, Select, InputNumber } from "antd";
import { Link, useNavigate, useSearchParams } from "react-router";
import { ArrowLeft } from "lucide-react";
import { createTaskUsingPost, updateTaskUsingPut, queryDataXTemplatesUsingGet, queryTasksUsingGet } from "../collection.apis";
import SimpleCronScheduler from "@/pages/DataCollection/Create/SimpleCronScheduler";
import { getSyncModeMap } from "../collection.const";
import { SyncMode } from "../collection.model";
import { useTranslation } from "react-i18next";

const { TextArea } = Input;

// IP 地址校验正则
const IP_REGEX = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
// IP:端口 校验正则
const IP_PORT_REGEX = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):([0-9]{1,5}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/;
// HTTP/HTTPS URL 校验正则
const URL_REGEX = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&/=]*)$/i;
// JDBC URL 校验函数
const validateJdbcUrl = (url: string): boolean => {
  // 基本格式检查
  if (!url.startsWith('jdbc:')) return false;

  // 检查是否包含 :// 或 :@ （Oracle格式）
  const hasDoubleSlash = url.includes('://');
  const hasAtSymbol = url.includes(':@');

  if (!hasDoubleSlash && !hasAtSymbol) {
    return false;
  }

  // 额外检查：不允许以 : 或 / 结尾
  if (url.endsWith(':') || url.endsWith('/')) {
    return false;
  }

  if (hasDoubleSlash) {
    // 检查 // 后面的部分
    const afterSlashMatch = url.match(/:\/\/([^/?]+)(\/|$)/);
    if (!afterSlashMatch) return false;

    const hostPort = afterSlashMatch[1];
    if (!hostPort) return false;

    // 如果有端口号，检查端口格式
    if (hostPort.includes(':')) {
      const parts = hostPort.split(':');
      const host = parts[0];
      const port = parts[1];

      if (!host) return false;
      if (!port || !/^\d{1,5}$/.test(port)) {
        return false;
      }
    }
  }

  return true;
};


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
  const [searchParams] = useSearchParams();
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const { t } = useTranslation();
  const syncModeOptions = Object.values(getSyncModeMap(t));

  // 编辑模式
  const taskId = searchParams.get("taskId");
  const isEditMode = !!taskId;
  const [editLoading, setEditLoading] = useState(false);

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

  // 解析 cron 表达式
  const parseCronExpression = (cronExpr: string) => {
    const parts = cronExpr.trim().split(/\s+/);
    if (parts.length !== 5) {
      // 无效的 cron 表达式，返回默认值
      return {
        type: "daily" as const,
        time: "00:00",
        cronExpression: cronExpr,
      };
    }

    const [minute, hour, day, month, weekday] = parts;
    const formattedHour = hour.padStart(2, "0");
    const formattedMinute = minute.padStart(2, "0");
    const time = `${formattedHour}:${formattedMinute}`;

    // 判断类型：monthly (指定日期), weekly (指定星期), daily (都是 *)
    if (day !== "*" && month === "*") {
      // monthly: 例如 "0 9 1 * *" 表示每月1号9点
      return {
        type: "monthly" as const,
        time,
        monthDay: parseInt(day, 10),
        cronExpression: cronExpr,
      };
    } else if (weekday !== "*" && day === "*") {
      // weekly: 例如 "0 9 * * 1" 表示每周一9点
      return {
        type: "weekly" as const,
        time,
        weekDay: parseInt(weekday, 10),
        cronExpression: cronExpr,
      };
    } else {
      // daily: 例如 "0 9 * * *" 表示每天9点
      return {
        type: "daily" as const,
        time,
        cronExpression: cronExpr,
      };
    }
  };

  useEffect(() => {
    const loadTemplates = async () => {
      setTemplatesLoading(true);
      try {
        const resp: any = await queryDataXTemplatesUsingGet({ page: 1, size: 1000 });
        const list: CollectionTemplate[] = resp?.data?.content || [];
        setTemplates(list);
      } catch (e) {
        message.error(t("dataCollection.createTask.messages.loadTemplatesFailed"));
      } finally {
        setTemplatesLoading(false);
      }
    };

    const loadTask = async () => {
      if (!taskId) return;
      setEditLoading(true);
      try {
        const resp: any = await queryTasksUsingGet({ page: 1, size: 1 });
        const task = resp?.data?.content?.find((t: any) => t.id === taskId);
        if (task) {
          // 设置表单值
          setSelectedTemplateId(task.templateId);
          form.setFieldsValue({
            name: task.name,
            description: task.description,
            syncMode: task.syncMode,
            scheduleExpression: task.scheduleExpression || "",
            timeoutSeconds: task.timeoutSeconds || 3600,
            templateId: task.templateId,
            config: task.config || { parameter: {}, reader: {}, writer: {} },
          });
          setNewTask({
            name: task.name,
            description: task.description,
            syncMode: task.syncMode,
            scheduleExpression: task.scheduleExpression || "",
            timeoutSeconds: task.timeoutSeconds || 3600,
            templateId: task.templateId,
            config: task.config || { parameter: {}, reader: {}, writer: {} },
          });
          // 解析 cron 表达式
          if (task.scheduleExpression) {
            const parsedSchedule = parseCronExpression(task.scheduleExpression);
            setScheduleExpression(parsedSchedule);
          }
        } else {
          message.error(t("dataCollection.taskManagement.messages.updateFailed"));
          navigate("/data/collection");
        }
      } catch (e) {
        message.error(t("dataCollection.taskManagement.messages.updateFailed"));
        navigate("/data/collection");
      } finally {
        setEditLoading(false);
      }
    };

    loadTemplates();
    if (isEditMode) {
      loadTask();
    }
  }, [taskId]);

  const parseJsonObjectInput = (value: any) => {
    if (value === undefined || value === null) return value;
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (!trimmed) return undefined;
      const parsed = JSON.parse(trimmed);
      if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
        throw new Error(t("dataCollection.createTask.messages.jsonObjectRequired"));
      }
      return parsed;
    }
    if (typeof value === "object") {
      if (Array.isArray(value) || value === null) {
        throw new Error(t("dataCollection.createTask.messages.jsonObjectRequired"));
      }
      return value;
    }
    throw new Error(t("dataCollection.createTask.messages.jsonObjectRequired"));
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
      message.error(error?.message || t("dataCollection.createTask.messages.jsonFormatError"));
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
          message.error(t("dataCollection.createTask.syncConfig.cronRequired"));
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

      if (isEditMode) {
        // 编辑模式：只更新允许的字段
        const updateData: any = {
          description: payload.description,
          timeoutSeconds: payload.timeoutSeconds,
          config: payload.config,
        };
        if (payload.syncMode === SyncMode.SCHEDULED && payload.scheduleExpression) {
          updateData.scheduleExpression = payload.scheduleExpression;
        }
        await updateTaskUsingPut(taskId!, updateData);
        message.success(t("dataCollection.taskManagement.messages.updateSuccess"));
      } else {
        // 创建模式
        await createTaskUsingPost(payload);
        message.success(t("dataCollection.createTask.messages.createSuccess"));
      }
      navigate("/data/collection");
    } catch (error) {
      if (error.errorFields) {
        // 表单验证错误，不显示消息
        return;
      }
      message.error(
        t("dataCollection.createTask.messages.errorWithDetail", {
          message: error?.data?.message ?? "",
          detail: error?.data?.data ?? "",
        })
      );
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
        rules.push({
          required: true,
          message: t("dataCollection.createTask.placeholders.enterWithLabel", { label }),
        });
      }

      // 根据字段名判断是否需要特殊校验
      const needsIPValidation = key === "ip";
      const needsHTTPURLValidation = key === "endpoint" || key === "api";
      const needsJDBCURLValidation = key === "jdbcUrl";

      // 添加字段类型特定的校验
      if (needsIPValidation) {
        // IP 地址校验
        rules.push({
          validator: (_: any, value: any) => {
            if (!value || value.trim() === "") {
              return Promise.resolve();
            }
            const isValid = IP_REGEX.test(value) || IP_PORT_REGEX.test(value);
            if (!isValid) {
              return Promise.reject(
                new Error(t("dataCollection.createTask.messages.invalidIP", { label }))
              );
            }
            return Promise.resolve();
          },
        });
      } else if (needsHTTPURLValidation) {
        // HTTP/HTTPS URL 校验
        rules.push({
          validator: (_: any, value: any) => {
            if (!value || value.trim() === "") {
              return Promise.resolve();
            }
            if (!URL_REGEX.test(value)) {
              return Promise.reject(
                new Error(t("dataCollection.createTask.messages.invalidURL", { label }))
              );
            }
            return Promise.resolve();
          },
        });
      } else if (needsJDBCURLValidation) {
        // JDBC URL 校验
        rules.push({
          validator: (_: any, value: any) => {
            if (!value || value.trim() === "") {
              return Promise.resolve();
            }
            if (!validateJdbcUrl(value)) {
              return Promise.reject(
                new Error(t("dataCollection.createTask.messages.invalidJdbcURL", { label }))
              );
            }
            return Promise.resolve();
          },
        });
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
                  t("dataCollection.createTask.messages.jsonFormatErrorWithMessage", {
                    message:
                      (e as Error)?.message ||
                      t("dataCollection.createTask.messages.jsonObjectInvalid"),
                  })
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
              <Input.Password
                placeholder={
                  description ||
                  t("dataCollection.createTask.placeholders.enterWithLabel", { label })
                }
              />
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
                    {t("dataCollection.createTask.actions.formatJson")}
                  </Button>
                </div>
              )}
            >
              <TextArea
                placeholder={
                  description ||
                  t("dataCollection.createTask.placeholders.enterWithLabel", { label })
                }
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
              <Select
                placeholder={
                  description ||
                  t("dataCollection.createTask.placeholders.enterWithLabel", { label })
                }
                mode="tags"
              />
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
              <Select
                placeholder={
                  description ||
                  t("dataCollection.createTask.placeholders.selectWithLabel", { label })
                }
                options={options}
              />
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
              <Input
                placeholder={
                  description ||
                  t("dataCollection.createTask.placeholders.enterWithLabel", { label })
                }
              />
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
              <Input
                placeholder={
                  description ||
                  t("dataCollection.createTask.placeholders.enterWithLabel", { label })
                }
              />
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
      {editLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">{t("common.loading")}</div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <Link to="/data/collection">
                <Button type="text">
                  <ArrowLeft className="w-4 h-4 mr-1" />
                </Button>
              </Link>
              <h1 className="text-xl font-bold bg-clip-text">
                {isEditMode
                  ? t("dataCollection.createTask.editTitle")
                  : t("dataCollection.createTask.title")}
              </h1>
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
            <h2 className="font-medium text-gray-900 text-lg mb-2">
              {t("dataCollection.createTask.basicInfo.title")}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
              <Form.Item
                label={t("dataCollection.createTask.basicInfo.name")}
                name="name"
                rules={[{ required: true, message: t("dataCollection.createTask.basicInfo.nameRequired") }]}
              >
                <Input
                  placeholder={t("dataCollection.createTask.basicInfo.namePlaceholder")}
                  disabled={isEditMode}
                />
              </Form.Item>

              <Form.Item
                label={t("dataCollection.createTask.basicInfo.timeout")}
                name="timeoutSeconds"
                rules={[{ required: true, message: t("dataCollection.createTask.basicInfo.timeoutRequired") }]}
                initialValue={3600}
              >
                <InputNumber
                  className="w-full"
                  min={1}
                  precision={0}
                  placeholder={t("dataCollection.createTask.basicInfo.timeoutPlaceholder")}
                />
              </Form.Item>

              <Form.Item
                className="md:col-span-2"
                label={t("dataCollection.createTask.basicInfo.description")}
                name="description"
              >
                <TextArea
                  placeholder={t("dataCollection.createTask.basicInfo.descriptionPlaceholder")}
                  rows={2}
                />
              </Form.Item>
            </div>

            {/* 同步配置 */}
            <h2 className="font-medium text-gray-900 pt-2 mb-1 text-lg">
              {t("dataCollection.createTask.syncConfig.title")}
            </h2>
            <Form.Item
              name="syncMode"
              label={t("dataCollection.createTask.syncConfig.syncMode.label")}
            >
              <Radio.Group
                value={newTask.syncMode}
                options={syncModeOptions}
                disabled={isEditMode}
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
                rules={[{ required: true, message: t("dataCollection.createTask.syncConfig.cronRequired") }]}
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
              {t("dataCollection.createTask.templateConfig.title")}
            </h2>

            <Form.Item
              label={t("dataCollection.createTask.templateConfig.selectTemplate")}
              name="templateId"
              rules={[{ required: true, message: t("dataCollection.createTask.templateConfig.selectTemplateRequired") }]}
            >
              <Select
                placeholder={t("dataCollection.createTask.templateConfig.selectTemplatePlaceholder")}
                loading={templatesLoading}
                disabled={isEditMode}
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
                      {t("dataCollection.createTask.templateParams.title")}
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
                      {t("dataCollection.createTask.sourceParams.title")}
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
                      {t("dataCollection.createTask.targetParams.title")}
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
              <Button onClick={() => navigate("/data/collection")}>
                {t("dataCollection.createTask.cancel")}
              </Button>
              <Button type="primary" onClick={handleSubmit}>
                {isEditMode
                  ? t("dataCollection.createTask.updateButton")
                  : t("dataCollection.createTask.submit")}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
