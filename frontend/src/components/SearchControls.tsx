import { Input, Button, Select, Tag, Segmented, DatePicker } from "antd";
import {
  BarsOutlined,
  AppstoreOutlined,
  SearchOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";
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
  dateRange,
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
  const [selectedFilters, setSelectedFilters] = useState<{
    [key: string]: string[];
  }>({});

  const filtersMap: Record<string, FilterOption> = filters.reduce(
    (prev, cur) => ({ ...prev, [cur.key]: cur }),
    {}
  );

  // select change
  const handleFilterChange = (filterKey: string, value: string) => {
    const filteredValues = {
      ...selectedFilters,
      [filterKey]: !value ? [] : [value],
    };
    setSelectedFilters(filteredValues);
  };

  // 清除已选筛选
  const handleClearFilter = (filterKey: string, value: string | string[]) => {
    const isMultiple = filtersMap[filterKey]?.mode === "multiple";
    if (!isMultiple) {
      setSelectedFilters({
        ...selectedFilters,
        [filterKey]: [],
      });
    } else {
      const currentValues = selectedFilters[filterKey]?.[0] || [];
      const newValues = currentValues.filter((v) => v !== value);
      setSelectedFilters({
        ...selectedFilters,
        [filterKey]: [newValues],
      });
    }
  };

  const handleClearAllFilters = () => {
    setSelectedFilters({});
    onClearFilters?.();
  };

  const hasActiveFilters = Object.values(selectedFilters).some(
    (values) => values?.[0]?.length > 0
  );

  useEffect(() => {
    if (Object.keys(selectedFilters).length === 0) return;
    onFiltersChange?.(selectedFilters);
  }, [selectedFilters]);

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
              value={dateRange as any}
              onChange={onDateChange}
              style={{ width: 260 }}
              allowClear
              placeholder={[t('components.searchControls.startTime'), t('components.searchControls.endTime')]}
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
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap flex-1">
              <span className="text-sm font-medium text-gray-700">
                {t('components.searchControls.selectedFilters')}
              </span>
              {Object.entries(selectedFilters).map(([filterKey, values]) =>
                values.map((value) => {
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
            </div>

            {/* Clear all filters button on the right */}
            <Button
              type="text"
              size="small"
              onClick={handleClearAllFilters}
              className="text-gray-500 hover:text-gray-700"
            >
              {t('components.searchControls.clearAll')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
