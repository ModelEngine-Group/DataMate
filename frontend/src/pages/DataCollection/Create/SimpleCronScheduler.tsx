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
import { useTranslation } from "react-i18next";

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

const SimpleCronScheduler: React.FC<SimpleCronSchedulerProps> = ({
  value = defaultConfig,
  onChange,
  className,
}) => {
  const { t } = useTranslation();
  const [config, setConfig] = useState<SimpleCronConfig>(value);

  // 生成周几选项
  const weekDayOptions = [
    { label: t("dataCollection.scheduler.weekdays.sunday"), value: 0 },
    { label: t("dataCollection.scheduler.weekdays.monday"), value: 1 },
    { label: t("dataCollection.scheduler.weekdays.tuesday"), value: 2 },
    { label: t("dataCollection.scheduler.weekdays.wednesday"), value: 3 },
    { label: t("dataCollection.scheduler.weekdays.thursday"), value: 4 },
    { label: t("dataCollection.scheduler.weekdays.friday"), value: 5 },
    { label: t("dataCollection.scheduler.weekdays.saturday"), value: 6 },
  ];

  // 生成月份日期选项
  const monthDayOptions = Array.from({ length: 31 }, (_, i) => ({
    label: `${i + 1}${t("dataCollection.scheduler.monthDaySuffix")}`,
    value: i + 1,
  }));

  // 常用时间预设
  const commonTimePresets = [
    { label: t("dataCollection.scheduler.timePresets.morning9"), value: "09:00" },
    { label: t("dataCollection.scheduler.timePresets.noon12"), value: "12:00" },
    { label: t("dataCollection.scheduler.timePresets.afternoon2"), value: "14:00" },
    { label: t("dataCollection.scheduler.timePresets.afternoon6"), value: "18:00" },
    { label: t("dataCollection.scheduler.timePresets.evening8"), value: "20:00" },
    { label: t("dataCollection.scheduler.timePresets.midnight0"), value: "00:00" },
  ];

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
        <Form.Item label={t("dataCollection.scheduler.labels.executionPeriod")} required>
          <Select value={config.type} onChange={handleTypeChange}>
            <Select.Option value="daily">{t("dataCollection.scheduler.periods.daily")}</Select.Option>
            <Select.Option value="weekly">{t("dataCollection.scheduler.periods.weekly")}</Select.Option>
            <Select.Option value="monthly">{t("dataCollection.scheduler.periods.monthly")}</Select.Option>
          </Select>
        </Form.Item>

        {/* 周几选择 */}
        {config.type === "weekly" && (
          <Form.Item label={t("dataCollection.scheduler.labels.executionDate")} required>
            <Select
              className="w-32"
              value={config.weekDay}
              onChange={(weekDay) => updateConfig({ weekDay })}
              placeholder={t("dataCollection.scheduler.labels.selectWeekday")}
              options={weekDayOptions}
            ></Select>
          </Form.Item>
        )}

        {/* 月份日期选择 */}
        {config.type === "monthly" && (
          <Form.Item label={t("dataCollection.scheduler.labels.executionDate")} required>
            <Select
              className="w-32"
              value={config.monthDay}
              onChange={(monthDay) => updateConfig({ monthDay })}
              placeholder={t("dataCollection.scheduler.labels.selectDate")}
              options={monthDayOptions}
            ></Select>
          </Form.Item>
        )}
      </div>

      {/* 时间选择 */}
      <Form.Item label={t("dataCollection.scheduler.labels.executionTime")} required>
        <Space wrap>
          <TimePicker
            format="HH:mm"
            value={config.time ? dayjs(config.time, "HH:mm") : null}
            onChange={handleTimeChange}
            placeholder={t("dataCollection.scheduler.labels.selectTime")}
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
