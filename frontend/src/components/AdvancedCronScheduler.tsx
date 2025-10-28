import React, { useState, useCallback, useEffect } from "react";
import {
  Card,
  Select,
  Input,
  Space,
  Typography,
  Row,
  Col,
  Divider,
  Button,
  Tooltip,
} from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;
const { Option } = Select;

export interface AdvancedCronConfig {
  second: string;
  minute: string;
  hour: string;
  day: string;
  month: string;
  weekday: string;
  year?: string;
  cronExpression: string;
}

interface AdvancedCronSchedulerProps {
  value?: AdvancedCronConfig;
  onChange?: (config: AdvancedCronConfig) => void;
  showYear?: boolean; // 是否显示年份字段
  className?: string;
}

// Cron字段的选项配置
const CRON_OPTIONS = {
  second: {
    label: "秒",
    range: [0, 59],
    examples: ["0", "*/5", "10,20,30", "0-30"],
    description: "秒钟 (0-59)",
  },
  minute: {
    label: "分钟",
    range: [0, 59],
    examples: ["0", "*/15", "5,10,15", "0-30"],
    description: "分钟 (0-59)",
  },
  hour: {
    label: "小时",
    range: [0, 23],
    examples: ["0", "*/2", "8,14,20", "9-17"],
    description: "小时 (0-23)",
  },
  day: {
    label: "日",
    range: [1, 31],
    examples: ["*", "1", "1,15", "1-15", "*/2"],
    description: "日期 (1-31)",
  },
  month: {
    label: "月",
    range: [1, 12],
    examples: ["*", "1", "1,6,12", "3-9", "*/3"],
    description: "月份 (1-12)",
  },
  year: {
    label: "年",
    range: [1970, 2099],
    examples: ["*", "2024", "2024-2026", "*/2"],
    description: "年份 (1970-2099)",
  },
  weekday: {
    label: "周",
    range: [0, 7], // 0和7都表示周日
    examples: ["*", "1", "1-5", "1,3,5", "0,6"],
    description: "星期 (0-7, 0和7都表示周日)",
    weekNames: ["周日", "周一", "周二", "周三", "周四", "周五", "周六"],
  },
};

// 生成常用的cron表达式选项
const generateCommonOptions = (field: keyof typeof CRON_OPTIONS) => {
  const options = [
    { label: "* (任意)", value: "*" },
    { label: "? (不指定)", value: "?" }, // 仅用于日和周字段
  ];

  const config = CRON_OPTIONS[field];
  const [start, end] = config.range;

  // 添加具体数值选项
  if (field === "weekday") {
    const weekdayConfig = config as { weekNames?: string[] };
    weekdayConfig.weekNames?.forEach((name: string, index: number) => {
      options.push({ label: `${index} (${name})`, value: index.toString() });
    });
    // 添加7作为周日的别名
    options.push({ label: "7 (周日)", value: "7" });
  } else {
    // 添加部分具体数值
    const step =
      field === "year" ? 5 : field === "day" || field === "month" ? 3 : 5;
    for (let i = start; i <= end; i += step) {
      if (i <= end) {
        options.push({ label: i.toString(), value: i.toString() });
      }
    }
  }

  // 添加间隔选项
  if (field !== "year") {
    options.push(
      { label: "*/2 (每2个)", value: "*/2" },
      { label: "*/5 (每5个)", value: "*/5" },
      { label: "*/10 (每10个)", value: "*/10" }
    );
  }

  // 添加范围选项
  if (field === "hour") {
    options.push(
      { label: "9-17 (工作时间)", value: "9-17" },
      { label: "0-6 (凌晨)", value: "0-6" }
    );
  } else if (field === "weekday") {
    options.push(
      { label: "1-5 (工作日)", value: "1-5" },
      { label: "0,6 (周末)", value: "0,6" }
    );
  } else if (field === "day") {
    options.push(
      { label: "1-15 (上半月)", value: "1-15" },
      { label: "16-31 (下半月)", value: "16-31" }
    );
  }

  return options;
};

// 验证cron字段值
const validateCronField = (
  value: string,
  field: keyof typeof CRON_OPTIONS
): boolean => {
  if (!value || value === "*" || value === "?") return true;

  const config = CRON_OPTIONS[field];
  const [min, max] = config.range;

  // 验证基本格式
  const patterns = [
    /^\d+$/, // 单个数字
    /^\d+-\d+$/, // 范围
    /^\*\/\d+$/, // 间隔
    /^(\d+,)*\d+$/, // 列表
    /^(\d+-\d+,)*(\d+-\d+|\d+)$/, // 复合表达式
  ];

  if (!patterns.some((pattern) => pattern.test(value))) {
    return false;
  }

  // 验证数值范围
  const numbers = value.match(/\d+/g);
  if (numbers) {
    return numbers.every((num) => {
      const n = parseInt(num);
      return n >= min && n <= max;
    });
  }

  return true;
};

// 生成cron表达式
const generateCronExpression = (
  config: Omit<AdvancedCronConfig, "cronExpression">
): string => {
  const { second, minute, hour, day, month, weekday, year } = config;

  const parts = [second, minute, hour, day, month, weekday];
  if (year && year !== "*") {
    parts.push(year);
  }

  return parts.join(" ");
};

// 解析cron表达式为人类可读的描述
const parseCronDescription = (cronExpression: string): string => {
  const parts = cronExpression.split(" ");
  if (parts.length < 6) return cronExpression;

  const [second, minute, hour, day, month, weekday, year] = parts;

  const descriptions = [];

  // 时间描述
  if (second === "0" && minute !== "*" && hour !== "*") {
    descriptions.push(`${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`);
  } else {
    if (hour !== "*") descriptions.push(`${hour}时`);
    if (minute !== "*") descriptions.push(`${minute}分`);
    if (second !== "*" && second !== "0") descriptions.push(`${second}秒`);
  }

  // 日期描述
  if (day !== "*" && day !== "?") {
    descriptions.push(`${day}日`);
  }

  // 月份描述
  if (month !== "*") {
    descriptions.push(`${month}月`);
  }

  // 星期描述
  if (weekday !== "*" && weekday !== "?") {
    const weekNames = [
      "周日",
      "周一",
      "周二",
      "周三",
      "周四",
      "周五",
      "周六",
      "周日",
    ];
    if (weekday === "1-5") {
      descriptions.push("工作日");
    } else if (weekday === "0,6") {
      descriptions.push("周末");
    } else if (/^\d$/.test(weekday)) {
      descriptions.push(weekNames[parseInt(weekday)]);
    } else {
      descriptions.push(`周${weekday}`);
    }
  }

  // 年份描述
  if (year && year !== "*") {
    descriptions.push(`${year}年`);
  }

  return descriptions.length > 0 ? descriptions.join(" ") : "每秒执行";
};

const AdvancedCronScheduler: React.FC<AdvancedCronSchedulerProps> = ({
  value = {
    second: "0",
    minute: "0",
    hour: "0",
    day: "*",
    month: "*",
    weekday: "?",
    year: "*",
    cronExpression: "0 0 0 * * ?",
  },
  onChange,
  showYear = false,
  className,
}) => {
  const [config, setConfig] = useState<AdvancedCronConfig>(value);
  const [customMode, setCustomMode] = useState(false);

  // 更新配置
  const updateConfig = useCallback(
    (updates: Partial<AdvancedCronConfig>) => {
      const newConfig = { ...config, ...updates };
      newConfig.cronExpression = generateCronExpression(newConfig);
      setConfig(newConfig);
      onChange?.(newConfig);
    },
    [config, onChange]
  );

  // 同步外部值
  useEffect(() => {
    setConfig(value);
  }, [value]);

  // 处理字段变化
  const handleFieldChange = (
    field: keyof AdvancedCronConfig,
    fieldValue: string
  ) => {
    if (field === "cronExpression") {
      // 直接编辑cron表达式
      const parts = fieldValue.split(" ");
      if (parts.length >= 6) {
        const newConfig = {
          second: parts[0] || "0",
          minute: parts[1] || "0",
          hour: parts[2] || "0",
          day: parts[3] || "*",
          month: parts[4] || "*",
          weekday: parts[5] || "?",
          year: parts[6] || "*",
          cronExpression: fieldValue,
        };
        setConfig(newConfig);
        onChange?.(newConfig);
      }
    } else {
      updateConfig({ [field]: fieldValue });
    }
  };

  // 快速设置预设
  const setPreset = (preset: Partial<AdvancedCronConfig>) => {
    updateConfig(preset);
  };

  // 常用预设
  const commonPresets = [
    {
      label: "每秒",
      config: {
        second: "*",
        minute: "*",
        hour: "*",
        day: "*",
        month: "*",
        weekday: "?",
      },
    },
    {
      label: "每分钟",
      config: {
        second: "0",
        minute: "*",
        hour: "*",
        day: "*",
        month: "*",
        weekday: "?",
      },
    },
    {
      label: "每小时",
      config: {
        second: "0",
        minute: "0",
        hour: "*",
        day: "*",
        month: "*",
        weekday: "?",
      },
    },
    {
      label: "每天午夜",
      config: {
        second: "0",
        minute: "0",
        hour: "0",
        day: "*",
        month: "*",
        weekday: "?",
      },
    },
    {
      label: "每周一9点",
      config: {
        second: "0",
        minute: "0",
        hour: "9",
        day: "?",
        month: "*",
        weekday: "1",
      },
    },
    {
      label: "每月1日0点",
      config: {
        second: "0",
        minute: "0",
        hour: "0",
        day: "1",
        month: "*",
        weekday: "?",
      },
    },
    {
      label: "工作日9点",
      config: {
        second: "0",
        minute: "0",
        hour: "9",
        day: "?",
        month: "*",
        weekday: "1-5",
      },
    },
    {
      label: "每15分钟",
      config: {
        second: "0",
        minute: "*/15",
        hour: "*",
        day: "*",
        month: "*",
        weekday: "?",
      },
    },
  ];

  const fields: Array<keyof typeof CRON_OPTIONS> = [
    "second",
    "minute",
    "hour",
    "day",
    "month",
    "weekday",
  ];
  if (showYear) fields.push("year");

  return (
    <Card className={className} size="small">
      <Space direction="vertical" className="w-full" size="middle">
        {/* 标题和切换模式 */}
        <div className="flex justify-between items-center">
          <Title level={5} className="m-0">
            高级 Cron 表达式配置
          </Title>
          <Button
            size="small"
            type={customMode ? "primary" : "default"}
            onClick={() => setCustomMode(!customMode)}
          >
            {customMode ? "切换到向导模式" : "切换到手动模式"}
          </Button>
        </div>

        {/* 快速预设 */}
        <div>
          <Text strong>快速预设：</Text>
          <div className="mt-2 flex gap-2 flex-wrap">
            {commonPresets.map((preset, index) => (
              <Button
                key={index}
                size="small"
                onClick={() => setPreset(preset.config)}
              >
                {preset.label}
              </Button>
            ))}
          </div>
        </div>

        {customMode ? (
          /* 手动编辑模式 */
          <div>
            <Text strong>Cron 表达式：</Text>
            <Input
              className="mt-2"
              value={config.cronExpression}
              onChange={(e) =>
                handleFieldChange("cronExpression", e.target.value)
              }
              placeholder="秒 分 时 日 月 周 [年]"
            />
            <Text
              type="secondary"
              className="text-xs block mt-1"
            >
              格式：秒(0-59) 分(0-59) 时(0-23) 日(1-31) 月(1-12) 周(0-7)
              [年(1970-2099)]
            </Text>
          </div>
        ) : (
          /* 向导模式 */
          <Row gutter={[16, 16]}>
            {fields.map((field) => {
              const fieldConfig = CRON_OPTIONS[field];
              const options = generateCommonOptions(field);
              return (
                <Col xs={24} sm={12} md={8} key={field}>
                  <div>
                    <div className="flex items-center mb-1">
                      <Text strong>{fieldConfig.label}</Text>
                      <Tooltip title={fieldConfig.description}>
                        <InfoCircleOutlined className="ml-1 text-gray-400" />
                      </Tooltip>
                    </div>
                    <Select
                      className="w-full"
                      value={config[field]}
                      onChange={(val) => handleFieldChange(field, val)}
                      showSearch
                      optionFilterProp="label"
                      placeholder={`选择${fieldConfig.label}`}
                    >
                      {options.map((option) => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                    {/* 自定义输入 */}
                    <Input
                      className="mt-1"
                      size="small"
                      placeholder="或输入自定义值"
                      value={config[field] || ""}
                      onChange={(e) => handleFieldChange(field, e.target.value)}
                      status={
                        validateCronField(config[field] || "", field) ? "" : "error"
                      }
                    />
                  </div>
                </Col>
              );
            })}
          </Row>
        )}

        <Divider className="my-3" />

        {/* 结果预览 */}
        <div>
          <Text strong>生成的 Cron 表达式：</Text>
          <Input
            className="mt-2 bg-gray-100"
            value={config.cronExpression}
            readOnly
          />
          <Text
            type="secondary"
            className="text-xs block mt-1"
          >
            描述：{parseCronDescription(config.cronExpression)}
          </Text>
        </div>

        {/* 字段说明 */}
        <div>
          <Text strong>字段说明：</Text>
          <div className="mt-2 text-xs text-gray-600">
            <Row gutter={[16, 8]}>
              <Col span={12}>• * 表示任意值</Col>
              <Col span={12}>• ? 表示不指定值（仅日、周字段）</Col>
              <Col span={12}>• */5 表示每5个单位</Col>
              <Col span={12}>• 1-5 表示范围</Col>
              <Col span={12}>• 1,3,5 表示列表</Col>
              <Col span={12}>• 日和周字段不能同时指定具体值</Col>
            </Row>
          </div>
        </div>
      </Space>
    </Card>
  );
};

export default AdvancedCronScheduler;
