import React, { useState, useCallback, useEffect } from "react";
import {
  Select,
  Space,
  TimePicker,
  Button,
  Form,
} from "antd";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";

export interface SimpleCronConfig {
  type: "daily" | "weekly" | "monthly";
  time?: string; // HH:mm 格式
  weekDay?: number; // 0-6, 0 表示周日
  monthDay?: number; // 1-31
  cronExpression: string;
}

interface SimpleCronSchedulerProps {
  value?: SimpleCronConfig;
  onChange?: (config: SimpleCronConfig) => void;
  className?: string;
}

const defaultConfig: SimpleCronConfig = {
  type: "daily",
  time: "00:00",
  cronExpression: "0 0 * * *",
};

// 生成周几选项
const weekDayOptions = [
  { label: "周日", value: 0 },
  { label: "周一", value: 1 },
  { label: "周二", value: 2 },
  { label: "周三", value: 3 },
  { label: "周四", value: 4 },
  { label: "周五", value: 5 },
  { label: "周六", value: 6 },
];

// 生成月份日期选项
const monthDayOptions = Array.from({ length: 31 }, (_, i) => ({
  label: `${i + 1}日`,
  value: i + 1,
}));

// 常用时间预设
const commonTimePresets = [
  { label: "上午 9:00", value: "09:00" },
  { label: "中午 12:00", value: "12:00" },
  { label: "下午 2:00", value: "14:00" },
  { label: "下午 6:00", value: "18:00" },
  { label: "晚上 8:00", value: "20:00" },
  { label: "午夜 0:00", value: "00:00" },
];

const SimpleCronScheduler: React.FC<SimpleCronSchedulerProps> = ({
  value = defaultConfig,
  onChange,
  className,
}) => {
  const [config, setConfig] = useState<SimpleCronConfig>(value);

  useEffect(() => {
    setConfig(value || defaultConfig);
  }, [value]);

  // 更新配置并生成 cron 表达式
  const updateConfig = useCallback(
    (updates: Partial<SimpleCronConfig>) => {
      const newConfig = { ...config, ...updates };
      const [hour, minute] = (newConfig.time || "00:00").split(":");
      if (newConfig.type === "weekly" && (newConfig.weekDay === undefined || newConfig.weekDay === null)) {
        newConfig.weekDay = 1;
      }
      if (newConfig.type === "monthly" && (newConfig.monthDay === undefined || newConfig.monthDay === null)) {
        newConfig.monthDay = 1;
      }

      // 根据不同类型生成 cron 表达式
      let cronExpression = "";
      switch (newConfig.type) {
        case "daily":
          cronExpression = `${minute} ${hour} * * *`;
          break;
        case "weekly":
          cronExpression = `${minute} ${hour} * * ${newConfig.weekDay}`;
          break;
        case "monthly":
          cronExpression = `${minute} ${hour} ${newConfig.monthDay} * *`;
          break;
      }

      newConfig.cronExpression = cronExpression;
      setConfig(newConfig);
      onChange?.(newConfig);
    },
    [config, onChange]
  );

  // 处理类型改变
  const handleTypeChange = (type) => {
    const updates: Partial<SimpleCronConfig> = { type };

    // 设置默认值
    if (type === "weekly" && (config.weekDay === undefined || config.weekDay === null)) {
      updates.weekDay = 1; // 默认周一
    } else if (type === "monthly" && (config.monthDay === undefined || config.monthDay === null)) {
      updates.monthDay = 1; // 默认每月1号
    }

    updateConfig(updates);
  };

  // 处理时间改变
  const handleTimeChange = (value: Dayjs | null) => {
    if (value) {
      updateConfig({ time: value.format("HH:mm") });
    }
  };

  // 快速设置预设时间
  const handleTimePreset = (time: string) => {
    updateConfig({ time });
  };

  return (
    <Space direction="vertical" className={`w-full ${className || ""}`}>
      {/* 执行周期选择 */}
      <div className="grid grid-cols-2 gap-4">
        <Form.Item label="执行周期" required>
          <Select value={config.type} onChange={handleTypeChange}>
            <Select.Option value="daily">每天执行</Select.Option>
            <Select.Option value="weekly">每周执行</Select.Option>
            <Select.Option value="monthly">每月执行</Select.Option>
          </Select>
        </Form.Item>

        {/* 周几选择 */}
        {config.type === "weekly" && (
          <Form.Item label="执行日期" required>
            <Select
              className="w-32"
              value={config.weekDay}
              onChange={(weekDay) => updateConfig({ weekDay })}
              placeholder="选择周几"
              options={weekDayOptions}
            ></Select>
          </Form.Item>
        )}

        {/* 月份日期选择 */}
        {config.type === "monthly" && (
          <Form.Item label="执行日期" required>
            <Select
              className="w-32"
              value={config.monthDay}
              onChange={(monthDay) => updateConfig({ monthDay })}
              placeholder="选择日期"
              options={monthDayOptions}
            ></Select>
          </Form.Item>
        )}
      </div>

      {/* 时间选择 */}
      <Form.Item label="执行时间" required>
        <Space wrap>
          <TimePicker
            format="HH:mm"
            value={config.time ? dayjs(config.time, "HH:mm") : null}
            onChange={handleTimeChange}
            placeholder="选择时间"
          />
          <Space wrap className="mt-2">
            {commonTimePresets.map((preset) => (
              <Button
                key={preset.value}
                size="small"
                className={
                  config.time === preset.value ? "ant-btn-primary" : ""
                }
                onClick={() => handleTimePreset(preset.value)}
              >
                {preset.label}
              </Button>
            ))}
          </Space>
        </Space>
      </Form.Item>

      {/* Cron 表达式预览 */}
      {/* <div className="mt-4 pt-4 border-t border-gray-200">
        <Text>生成的 Cron 表达式</Text>
        <Input
          className="mt-2 bg-gray-100"
          value={config.cronExpression}
          readOnly
        />
      </div> */}
    </Space>
  );
};

export default SimpleCronScheduler;
