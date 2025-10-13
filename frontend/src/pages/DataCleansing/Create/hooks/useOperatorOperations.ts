import { useEffect, useState } from "react";
import { CleansingTemplate, OperatorI } from "../../cleansing.model";
import { queryCleaningTemplatesUsingGet } from "../../cleansing.api";

export function useOperatorOperations() {
  const [currentStep, setCurrentStep] = useState(1);
  const [operators, setOperators] = useState<OperatorI[]>([]);
  const [selectedOperator, setSelectedOperator] = useState<string | null>(null);

  const [templates, setTemplates] = useState<CleansingTemplate[]>([]);
  const [currentTemplate, setCurrentTemplate] =
    useState<CleansingTemplate | null>(null);

  const fetchTemplates = async () => {
    const { data } = await queryCleaningTemplatesUsingGet();
    const newTemplates =
      data.content?.map?.((item) => ({
        ...item,
        label: item.name,
        value: item.id,
      })) || [];
    setTemplates(newTemplates);
    if (!currentTemplate && newTemplates.length > 0) {
      setCurrentTemplate(newTemplates[0]);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const toggleOperator = (operator: OperatorI) => {
    const exist = operators.find((op) => op.originalId === operator.id);
    if (exist) {
      setOperators(operators.filter((op) => op.originalId !== operator.id));
    } else {
      const newOperator: OperatorI = {
        ...operator,
        originalId: operator.id,
      };
      setOperators([...operators, newOperator]);
    }
  };

  // 删除算子
  const removeOperator = (id: string) => {
    setOperators(operators.filter((op) => op.id !== id));
    if (selectedOperator === id) setSelectedOperator(null);
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
    setCurrentTemplate,
    setCurrentStep,
    operators,
    setOperators,
    selectedOperator,
    setSelectedOperator,
    toggleOperator,
    removeOperator,
    handleNext,
    handlePrev,
  };
}
