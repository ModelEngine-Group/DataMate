import { Button, Checkbox, Tooltip } from "antd";
import { FilterOutlined } from "@ant-design/icons";
import React from "react";
import { useTranslation } from "react-i18next";
import { CategoryI, CategoryTreeI } from "../../operator.model";

interface FilterOption {
  key: string;
  label: string;
  count: number;
  icon?: React.ReactNode;
  color?: string;
}

interface FilterSectionProps {
  title: string;
  total: number;
  options: FilterOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  showIcons?: boolean;
  badgeColor?: string;
}

const FilterSection: React.FC<FilterSectionProps> = ({
  total,
  title,
  options,
  selectedValues,
  onSelectionChange,
  showIcons = false,
}) => {
  const { t } = useTranslation();
  const handleCheckboxChange = (value: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedValues, value]);
    } else {
      onSelectionChange(selectedValues.filter((v) => v !== value));
    }
  };

  // 全选功能
  const isAllSelected =
    options.length > 0 && selectedValues.length === options.length;
  const isIndeterminate =
    selectedValues.length > 0 && selectedValues.length < options.length;

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      // 全选
      onSelectionChange(options.map((option) => option.key));
    } else {
      // 全不选
      onSelectionChange([]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">{title}</h4>
      </div>

      <div className="space-y-1 text-sm">
        {/* 全选选项 */}
        {options.length > 1 && (
          <label className="flex items-center space-x-2 cursor-pointer border-b border-gray-100 pb-1 ">
            <Checkbox
              checked={isAllSelected}
              indeterminate={isIndeterminate}
              onChange={(e) => handleSelectAll(e.target.checked)}
            />
            <div className="flex items-center gap-1 flex-1 ml-1">
              <span className="text-gray-600 font-medium">{t("operatorMarket.home.filters.selectAll")}</span>
            </div>
            <span className="text-gray-400">({total})</span>
          </label>
        )}

        {/* 各个选项 */}
        {options.map((option) => (
          <label
            key={option.key}
            className="flex items-center space-x-2 cursor-pointer"
          >
            <Checkbox
              checked={selectedValues.includes(option.key)}
              onChange={(e) =>
                handleCheckboxChange(option.key, e.target.checked)
              }
            />
            <div className="flex items-center gap-1 flex-1 ml-1">
              {showIcons && option.icon}
              <span className={`text-gray-700 ${option.color || ""}`}>
                {option.label}
              </span>
            </div>
            <span className="text-gray-400">({option.count})</span>
          </label>
        ))}
      </div>
    </div>
  );
};

interface FiltersProps {
  categoriesTree: CategoryTreeI[];
  selectedFilters: { [key: string]: string[] };
  selectedStar: boolean;
  starCount: number;
  hideFilter: () => void;
  setSelectedFilters: (filters: { [key: string]: string[] }) => void;
  setSelectedStar: (item: boolean) => void;
}

const Filters: React.FC<FiltersProps> = ({
  categoriesTree,
  selectedFilters,
  selectedStar,
  starCount,
  hideFilter,
  setSelectedFilters,
  setSelectedStar,
}) => {
  const { t } = useTranslation();
  const clearAllFilters = () => {
    const newFilters = Object.keys(selectedFilters).reduce((acc, key) => {
      acc[key] = [];
      return acc;
    }, {} as { [key: string]: string[] });
    setSelectedFilters(newFilters);
  };

  const hasActiveFilters = Object.values(selectedFilters).some(
    (filters) => Array.isArray(filters) && filters.length > 0
  );

  const starCategory = {
    id: "starStatus",
    count: starCount,
    name: t("operatorMarket.home.filters.starStatus"),
    categories: [{
      id: "isStar",
      count: starCount,
      name: t("operatorMarket.home.filters.starred")
    }]
  };

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      {/* Filter Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900 flex items-center gap-2">
          <Tooltip title={t("operatorMarket.home.filters.hide")}>
            <Button
              type="text"
              size="small"
              icon={<FilterOutlined />}
              onClick={hideFilter}
              className="cursor-pointer hover:text-blue-500"
            ></Button>
          </Tooltip>
          <span>{t("operatorMarket.home.filters.title")}</span>
        </h3>
        {hasActiveFilters && (
          <span
            onClick={clearAllFilters}
            className="cursor-pointer text-sm text-gray-500 hover:text-blue-500"
          >
            {t("operatorMarket.home.filters.clear")}
          </span>
        )}
      </div>

      {/* Filter Sections */}
      {categoriesTree.map((category: CategoryTreeI) => (
        <FilterSection
          key={category.id}
          total={category.count}
          title={category.name}
          options={category.categories.map((cat: CategoryI) => ({
            key: cat.id.toString(),
            label: cat.name,
            count: cat.count,
          }))}
          selectedValues={selectedFilters[category.id] || []}
          onSelectionChange={(values) =>
            setSelectedFilters({ ...selectedFilters, [category.id]: values })
          }
          showIcons={false}
        />
      ))}

      <FilterSection
        key={starCategory.id}
        total={starCategory.count}
        title={starCategory.name}
        options={starCategory.categories.map(cat => ({
          key: cat.id.toString(),
          label: cat.name,
          count: cat.count,
        }))}
        selectedValues={selectedStar ? ["isStar"] : []}
        onSelectionChange={(values) => {
          values.length > 0 ? setSelectedStar(true) : setSelectedStar(false);
        }}
        showIcons={false}
      />
    </div>
  );
};

export default Filters;
