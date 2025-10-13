import { useState } from "react";
import { Checkbox } from "antd";
import { FilterOutlined } from "@ant-design/icons";
import {
  Brain,
  Code,
  Cpu,
  FileText,
  ImageIcon,
  Music,
  Package,
  Settings,
  Video,
  X,
  Zap,
} from "lucide-react";
import type { Operator } from "@/pages/OperatorMarket/operator.model";
import { mockOperators } from "@/mock/operator";
import React from "react";

const getStatusBadge = (status: string) => {
  const statusConfig = {
    active: {
      label: "活跃",
      color: "green",
      icon: <Zap className="w-3 h-3" />,
    },
    beta: {
      label: "测试版",
      color: "blue",
      icon: <Settings className="w-3 h-3" />,
    },
    deprecated: {
      label: "已弃用",
      color: "gray",
      icon: <X className="w-3 h-3" />,
    },
  };
  return (
    statusConfig[status as keyof typeof statusConfig] || statusConfig.active
  );
};

const getTypeIcon = (type: string) => {
  const iconMap = {
    preprocessing: Code,
    training: Brain,
    inference: Cpu,
    postprocessing: Package,
  };
  const IconComponent = iconMap[type as keyof typeof iconMap] || Code;
  return <IconComponent className="w-4 h-4" />;
};

const getModalityIcon = (modality: string) => {
  const iconMap = {
    text: FileText,
    image: ImageIcon,
    audio: Music,
    video: Video,
  };
  const IconComponent = iconMap[modality as keyof typeof iconMap] || FileText;
  return <IconComponent className="w-3 h-3" />;
};

interface FilterOption {
  key: string;
  label: string;
  count: number;
  icon?: React.ReactNode;
  color?: string;
}

interface FilterSectionProps {
  title: string;
  options: FilterOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  showIcons?: boolean;
  badgeColor?: string;
}

const FilterSection: React.FC<FilterSectionProps> = ({
  title,
  options,
  selectedValues,
  onSelectionChange,
  showIcons = false,
}) => {
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
              <span className="text-gray-600 font-medium">全选</span>
            </div>
            <span className="text-gray-400">({options.length})</span>
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

const Filters = () => {
  const [operators] = useState<Operator[]>(mockOperators);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedModalities, setSelectedModalities] = useState<string[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);

  const clearAllFilters = () => {
    setSelectedCategories([]);
    setSelectedTypes([]);
    setSelectedModalities([]);
    setSelectedStatuses([]);
  };

  const hasActiveFilters =
    selectedCategories.length > 0 ||
    selectedTypes.length > 0 ||
    selectedModalities.length > 0 ||
    selectedStatuses.length > 0;

  // Prepare filter options
  const categoryOptions = Array.from(
    new Set(operators.map((op) => op.category))
  ).map((category) => ({
    key: category,
    label: category,
    count: operators.filter((op) => op.category === category).length,
  }));

  const typeOptions = [
    "preprocessing",
    "training",
    "inference",
    "postprocessing",
  ].map((type) => {
    const typeLabels = {
      preprocessing: "预处理",
      training: "训练",
      inference: "推理",
      postprocessing: "后处理",
    };
    return {
      key: type,
      label: typeLabels[type as keyof typeof typeLabels],
      count: operators.filter((op) => op.type === type).length,
      icon: getTypeIcon(type),
    };
  });

  const modalityOptions = Array.from(
    new Set(operators.flatMap((op) => op.modality))
  ).map((modality) => ({
    key: modality,
    label: modality,
    count: operators.filter((op) => op.modality.includes(modality)).length,
    icon: getModalityIcon(modality),
  }));

  const statusOptions = ["active", "beta", "deprecated"].map((status) => {
    const statusLabels = {
      active: "活跃",
      beta: "测试版",
      deprecated: "已弃用",
    };
    const statusConfig = getStatusBadge(status);
    return {
      key: status,
      label: statusLabels[status as keyof typeof statusLabels],
      count: operators.filter((op) => op.status === status).length,
      color: statusConfig.color,
    };
  });

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      {/* Filter Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900 flex items-center gap-2">
          <FilterOutlined className="w-4 h-4" />
          筛选器
        </h3>
        {hasActiveFilters && (
          <span
            onClick={clearAllFilters}
            className="cursor-pointer text-sm text-gray-500 hover:text-blue-500"
          >
            清除
          </span>
        )}
      </div>

      {/* Filter Sections */}
      <FilterSection
        title="分类"
        options={categoryOptions}
        selectedValues={selectedCategories}
        onSelectionChange={setSelectedCategories}
        badgeColor="bg-blue-100 text-blue-800"
      />

      <FilterSection
        title="类型"
        options={typeOptions}
        selectedValues={selectedTypes}
        onSelectionChange={setSelectedTypes}
        showIcons={true}
        badgeColor="bg-green-100 text-green-800"
      />

      <FilterSection
        title="模态"
        options={modalityOptions}
        selectedValues={selectedModalities}
        onSelectionChange={setSelectedModalities}
        showIcons={true}
        badgeColor="bg-purple-100 text-purple-800"
      />

      <FilterSection
        title="状态"
        options={statusOptions}
        selectedValues={selectedStatuses}
        onSelectionChange={setSelectedStatuses}
        showIcons={true}
        badgeColor="bg-orange-100 text-orange-800"
      />
    </div>
  );
};

export default Filters;
