export interface OperatorI {
  id: string;
  name: string;
  type: string;
  icon: React.ReactNode;
  description: string;
  tags: string[];
  isStar?: boolean;
  originalId?: string; // 用于标识原始算子ID，便于去重
  categories: number[]; // 分类列表
  settings: string;
  params?: { [key: string]: any }; // 用户配置的参数
  defaultParams?: { [key: string]: any }; // 默认参数
  configs: {
    [key: string]: {
      type: "input" | "select" | "radio" | "checkbox" | "range";
      label: string;
      value: any;
      options?: string[] | { label: string; value: any }[];
      min?: number;
      max?: number;
      step?: number;
    };
  };
}

export interface CategoryI {
  id: string;
  name: string;
  icon: React.ReactNode;
  operators: OperatorI[];
}
