import { useEffect, useState } from "react";
import { CleansingTemplate, OperatorI } from "../../cleansing.model";
import { queryCleaningTemplatesUsingGet } from "../../cleansing.api";
import { queryOperatorsUsingPost } from "@/pages/OperatorMarket/operator.api";

export function useOperatorOperations() {
  const [currentStep, setCurrentStep] = useState(1);

  const [operators, setOperators] = useState<OperatorI[]>([]);
  const [selectedOperators, setSelectedOperators] = useState<OperatorI[]>([]);
  const [configOperator, setConfigOperator] = useState<OperatorI | null>(null);

  const [templates, setTemplates] = useState<CleansingTemplate[]>([]);
  const [currentTemplate, setCurrentTemplate] =
    useState<CleansingTemplate | null>(null);

  // 将后端返回的算子数据映射为前端需要的格式
  const mapOperator = (op: OperatorI) => {
    const configs =
      op.settings && typeof op.settings === "string"
        ? JSON.parse(op.settings)
        : {};
    const defaultParams: Record<string, string> = {};
    Object.keys(configs).forEach((key) => {
      const { value } = configs[key];
      defaultParams[key] = value;
    });
    return {
      ...op,
      defaultParams,
      configs,
    };
  };

  const initOperators = async () => {
    const { data } = await queryOperatorsUsingPost({ page: 0, size: 1000 });
    const operators = data.content.map(mapOperator);
    setOperators(operators || []);
  };

  const initTemplates = async () => {
    const { data } = await queryCleaningTemplatesUsingGet();
    const newTemplates =
      data.content?.map?.((item) => ({
        ...item,
        label: item.name,
        value: item.id,
      })) || [];
    setTemplates(newTemplates);
  };

  useEffect(() => {
    setSelectedOperators(currentTemplate?.instance?.map(mapOperator) || []);
  }, [currentTemplate]);

  useEffect(() => {
    initTemplates();
    initOperators();
  }, []);

  const toggleOperator = (operator: OperatorI) => {
    const exist = selectedOperators.find((op) => op.id === operator.id);
    if (exist) {
      setSelectedOperators(operators.filter((op) => op.id !== operator.id));
    } else {
      const newOperator: OperatorI = {
        ...operator,
      };
      setSelectedOperators([...selectedOperators, newOperator]);
    }
  };

  // 删除算子
  const removeOperator = (id: string) => {
    setSelectedOperators(selectedOperators.filter((op) => op.id !== id));
    if (configOperator?.id === id) setConfigOperator(null);
  };

  // 配置算子参数变化
  const handleConfigChange = (
    operatorId: string,
    paramKey: string,
    value: any
  ) => {
    console.log(operatorId, paramKey, value);
    
    setSelectedOperators((prev) =>
      prev.map((op) =>
        op.id === operatorId
          ? {
              ...op,
              params: {
                ...(op?.params || op?.defaultParams),
                [paramKey]: value,
              },
            }
          : op
      )
    );
  };

  const handleNext = () => {
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return {
    currentStep,
    templates,
    currentTemplate,
    configOperator,
    setConfigOperator,
    setCurrentTemplate,
    setCurrentStep,
    operators,
    setOperators,
    selectedOperators,
    setSelectedOperators,
    handleConfigChange,
    toggleOperator,
    removeOperator,
    handleNext,
    handlePrev,
  };
}
