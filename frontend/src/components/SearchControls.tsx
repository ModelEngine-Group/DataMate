
import { Input, Button, Select, Tag, Segmented } from "antd";
import {
  BarsOutlined,
  AppstoreOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";

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

  // View props
  viewMode?: "card" | "list";
  onViewModeChange?: (mode: "card" | "list") => void;

  // Control visibility
  showFilters?: boolean;
  showSort?: boolean;
  showViewToggle?: boolean;

  // Styling
  className?: string;
}

export function SearchControls({
  viewMode,
  searchTerm,
  showFilters = true,
  showViewToggle = true,
  searchPlaceholder = "搜索...",
  filters = [],
  onSearchChange,
  onFiltersChange,
  onViewModeChange,
}: SearchControlsProps) {
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
  };

  const hasActiveFilters = Object.values(selectedFilters).some(
    (values) => values?.[0]?.length > 0
  );

  useEffect(() => {
    onFiltersChange?.(selectedFilters);
  }, [selectedFilters]);

  return (
    <div className="mt-4 mb-4">
      <div className="flex items-center justify-between gap-4">
        {/* Left side - Search and Filters */}
        <div className="flex items-center gap-4 flex-1">
          {/* Search */}
          <div className="relative flex-1">
            <Input
              placeholder={searchPlaceholder}
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

        {/* Right side - View Toggle */}
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
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap flex-1">
              <span className="text-sm font-medium text-gray-700">
                已选筛选:
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
              清除全部
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
