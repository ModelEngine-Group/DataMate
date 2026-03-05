import { Input, Button, Select, Tag, Segmented, DatePicker } from "antd";
import {
  BarsOutlined,
  AppstoreOutlined,
  SearchOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";
import React from "react";
import { useTranslation } from "react-i18next";

interface FilterOption {
  key: string;
  label: string;
  mode?: "tags" | "multiple";
  options: { label: string; value: string }[];
}

interface SearchControlsProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;

  // Filter props
  filters?: FilterOption[];
  selectedFilters?: Record<string, string[]>;
  onFiltersChange?: (filters: Record<string, string[]>) => void;
  onClearFilters?: () => void;

  // Date range props
  dateRange?: [Date | null, Date | null] | null;
  onDateChange?: (dates: [Date | null, Date | null] | null) => void;

  // Reload props
  onReload?: () => void;

  // View props
  viewMode?: "card" | "list";
  onViewModeChange?: (mode: "card" | "list") => void;

  // Control visibility
  showFilters?: boolean;
  showSort?: boolean;
  showViewToggle?: boolean;
  showReload?: boolean;
  showDatePicker?: boolean;

  // Styling
  className?: string;
}

export function SearchControls({
  viewMode,
  className,
  searchTerm,
  showFilters = true,
  showViewToggle = true,
  searchPlaceholder,
  filters = [],
  selectedFilters: externalSelectedFilters,
  dateRange: externalDateRange,
  showDatePicker = false,
  showReload = true,
  onReload,
  onDateChange,
  onSearchChange,
  onFiltersChange,
  onViewModeChange,
  onClearFilters,
}: SearchControlsProps) {
  const { t } = useTranslation();

  // 内部状态（如果外部没有传入 selectedFilters）
  const [internalSelectedFilters, setInternalSelectedFilters] = useState<{
    [key: string]: string[];
  }>({});

  // 使用外部传入的 selectedFilters，如果没有则使用内部状态
  const selectedFilters = externalSelectedFilters !== undefined
    ? externalSelectedFilters
    : internalSelectedFilters;

  // 内部 dateRange 状态（用于禁用逻辑）
  const [internalDateRange, setInternalDateRange] = useState<typeof externalDateRange>(externalDateRange);

  // 同步外部 dateRange 到内部状态
  useEffect(() => {
    setInternalDateRange(externalDateRange);
  }, [externalDateRange]);

  // 更新筛选值的函数
  const updateSelectedFilters = (newFilters: Record<string, string[]>) => {
    if (externalSelectedFilters !== undefined) {
      // 受控模式：直接调用 onFiltersChange
      onFiltersChange?.(newFilters);
    } else {
      // 非受控模式：更新内部状态
      setInternalSelectedFilters(newFilters);
      // 同时通知父组件当前的筛选值，避免依赖 useEffect 造成死循环
      onFiltersChange?.(newFilters);
    }
  };

  const filtersMap: Record<string, FilterOption> = filters.reduce(
    (prev, cur) => ({ ...prev, [cur.key]: cur }),
    {}
  );

  // select change
  const handleFilterChange = (filterKey: string, value: string) => {
    const filteredValues = {
      ...selectedFilters,
      [filterKey]: !value || value === 'all' ? [] : [value],
    };
    updateSelectedFilters(filteredValues);
  };

  // 清除已选筛选
  const handleClearFilter = (filterKey: string, value: string | string[]) => {
    const isMultiple = filtersMap[filterKey]?.mode === "multiple";
    if (!isMultiple) {
      updateSelectedFilters({
        ...selectedFilters,
        [filterKey]: [],
      });
    } else {
      const currentValues = selectedFilters[filterKey]?.[0] || [];
      const newValues = currentValues.filter((v) => v !== value);
      updateSelectedFilters({
        ...selectedFilters,
        [filterKey]: [newValues],
      });
    }
  };

  const handleClearAllFilters = () => {
    updateSelectedFilters({});
    onClearFilters?.();
  };

  const hasActiveFilters = Object.values(selectedFilters).some(
    (values) => Array.isArray(values) && values.length > 0 && values[0] !== undefined
  );

  return (
    <div className={className}>
      <div className="flex items-center justify-between gap-8">
        {/* Left side - Search and Filters */}
        <div className="flex items-center gap-2 flex-1">
          {/* Search */}
          <div className="relative flex-1">
            <Input
              allowClear
              placeholder={searchPlaceholder || t('components.searchControls.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              prefix={<SearchOutlined className="w-4 h-4 text-gray-400" />}
            />
          </div>

          {/* Filters */}
          {showFilters && filters.length > 0 && (
            <div className="flex items-center gap-2">
              {filters.map((filter: FilterOption) => (
                <Select
                  maxTagCount="responsive"
                  mode={filter.mode}
                  key={filter.key}
                  placeholder={filter.label}
                  value={selectedFilters[filter.key]?.[0] || undefined}
                  onChange={(value) => handleFilterChange(filter.key, value)}
                  style={{ width: 144 }}
                  allowClear
                >
                  {filter.options.map((option) => (
                    <Select.Option key={option.value} value={option.value}>
                      {option.label}
                    </Select.Option>
                  ))}
                </Select>
              ))}
            </div>
          )}
        </div>

          {showDatePicker && (
            <DatePicker.RangePicker
              value={internalDateRange as any}
              onChange={(date) => {
                setInternalDateRange(date);
                onDateChange?.(date);
              }}
              showTime={{ format: 'HH:mm:ss' }}
              format="YYYY-MM-DD HH:mm:ss"
              style={{ width: 380 }}
              allowClear
              placeholder={[t('components.searchControls.startTime'), t('components.searchControls.endTime')]}
              disabledDate={(current, info) => {
                // 只禁用日期部分，同一天不禁用
                const startDate = info.from;
                if (!startDate) {
                  return false;
                }
                // 如果是同一天，不禁用（让时间选择器处理）
                if (current.isSame(startDate, 'day')) {
                  return false;
                }
                // 禁用早于开始日期的日期
                return current.isBefore(startDate, 'day');
              }}
              disabledTime={(current, partial, info) => {
                // partial 是 'start' 或 'end'，表示当前正在选择哪个
                // info.from 是已选择的开始日期
                const startDate = info.from;

                if (partial !== 'end' || !startDate) {
                  return {
                    disabledHours: () => [],
                    disabledMinutes: () => [],
                    disabledSeconds: () => [],
                  };
                }

                const startHour = startDate.hour();
                const startMinute = startDate.minute();
                const startSecond = startDate.second();

                return {
                  disabledHours: () => {
                    const hours = [];
                    for (let i = 0; i < startHour; i++) {
                      hours.push(i);
                    }
                    return hours;
                  },
                  disabledMinutes: (selectedHour) => {
                    if (selectedHour > startHour) {
                      return [];
                    }
                    const minutes = [];
                    for (let i = 0; i < startMinute; i++) {
                      minutes.push(i);
                    }
                    return minutes;
                  },
                  disabledSeconds: (selectedHour, selectedMinute) => {
                    if (selectedHour > startHour) {
                      return [];
                    }
                    if (selectedHour === startHour && selectedMinute > startMinute) {
                      return [];
                    }
                    const seconds = [];
                    for (let i = 0; i < startSecond; i++) {
                      seconds.push(i);
                    }
                    return seconds;
                  },
                };
              }}
            />
          )}

        {/* Right side */}
        <div className="flex items-center gap-2">
          {showViewToggle && onViewModeChange && (
            <Segmented
              options={[
                { value: "list", icon: <BarsOutlined /> },
                { value: "card", icon: <AppstoreOutlined /> },
              ]}
              value={viewMode}
              onChange={(value) => onViewModeChange(value as "list" | "card")}
            />
          )}

          {showReload && (
            <Button
              icon={<ReloadOutlined />}
              onClick={() => onReload?.()}
            ></Button>
          )}
        </div>
      </div>

      {/* Active Filters Display */}
      {(hasActiveFilters || internalDateRange) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap flex-1">
              <span className="text-sm font-medium text-gray-700">
                {t('components.searchControls.filters.label')}
              </span>
              {Object.entries(selectedFilters).map(([filterKey, values]) =>
                // 只处理数组类型的筛选值
                Array.isArray(values) && values.map((value) => {
                  const filter = filtersMap[filterKey];

                  const getLabeledValue = (item: string) => {
                    const option = filter?.options.find(
                      (o) => o.value === item
                    );
                    return (
                      <Tag
                        key={`${filterKey}-${item}`}
                        closable
                        onClose={() => handleClearFilter(filterKey, item)}
                        color="blue"
                      >
                        {filter?.label}: {option?.label || item}
                      </Tag>
                    );
                  };
                  return Array.isArray(value)
                    ? value.map((item) => getLabeledValue(item))
                    : getLabeledValue(value);
                })
              )}
              {/* 显示时间范围标签 */}
              {internalDateRange && internalDateRange[0] && (
                <Tag closable onClose={() => {
                  setInternalDateRange(null);
                  onDateChange?.(null);
                }} color="blue">
                  {t('components.searchControls.startTime')}: {internalDateRange[0]?.format('YYYY-MM-DD HH:mm:ss')}
                </Tag>
              )}
              {internalDateRange && internalDateRange[1] && (
                <React.Fragment key="time-separator">
                  <span className="text-gray-400 mx-1">~</span>
                  <Tag closable onClose={() => {
                    setInternalDateRange(null);
                    onDateChange?.(null);
                  }} color="blue">
                    {t('components.searchControls.endTime')}: {internalDateRange[1]?.format('YYYY-MM-DD HH:mm:ss')}
                  </Tag>
                </React.Fragment>
              )}
            </div>

            {/* Clear all filters button on the right */}
            <Button
              type="text"
              size="small"
              onClick={() => {
                handleClearAllFilters();
                onDateChange?.(null);
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              {t('components.searchControls.filters.clearAll')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
