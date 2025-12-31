export interface ConfigI {
  type:
    | "input"
    | "select"
    | "radio"
    | "checkbox"
    | "range"
    | "slider"
    | "inputNumber"
    | "switch"
    | "multiple";
  value?: number | string | boolean | string[] | number[];
  required?: boolean;
  description?: string;
  key: string;
  defaultVal: number | string | boolean | string[];
  options?: string[] | { label: string; value: string }[];
  min?: number;
  max?: number;
  step?: number;
  properties?: ConfigI[]; // 用于嵌套配置
}

export interface OperatorI {
  id: string;
  name: string;
  type: string;
  version: string;
  inputs: string;
  outputs: string;
  icon: React.ReactNode;
  iconColor?: string; // 图标背景色，用于区分不同类型算子
  description: string;
  tags: string[];
  isStar?: boolean;
  originalId?: string; // 用于标识原始算子ID，便于去重
  categories: string[]; // 分类列表
  settings: string;
  overrides?: { [key: string]: any }; // 用户配置的参数
  defaultParams?: { [key: string]: any }; // 默认参数
  configs: {
    [key: string]: ConfigI;
  };
  createdAt?: string;
  updatedAt?: string;
}

export interface CategoryI {
  id: number;
  name: string;
  count: number; // 该分类下的算子数量
  type: string; // e.g., "数据源", "数据清洗", "数据分析", "数据可视化"
  parentId?: number; // 父分类ID，若无父分类则为null
  value: string;
  createdAt: string;
}

export interface CategoryTreeI {
  id: string;
  name: string;
  count: number;
  categories: CategoryI[];
}
