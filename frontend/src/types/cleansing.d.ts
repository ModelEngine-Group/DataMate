export // 算子类型定义
interface OperatorI {
  id: string;
  name: string;
  type: string;
  category: keyof typeof OPERATOR_CATEGORIES;
  icon: React.ReactNode;
  description: string;
  tags: string[];
  isPopular?: boolean;
  params: {
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

