import { useEffect, useState, useMemo } from "react";
import { OperatorI } from "@/pages/OperatorMarket/operator.model";
import { CleansingTemplate } from "../../cleansing.model";
import {queryCleaningTemplateByIdUsingGet, queryCleaningTemplatesUsingGet} from "../../cleansing.api";
import {
  queryCategoryTreeUsingGet,
  queryOperatorsUsingPost,
} from "@/pages/OperatorMarket/operator.api";
import {useParams} from "react-router";
import i18n from "@/i18n";
import { App } from "antd";

function checkTypeCompatible(
  prevOutputs: string | undefined,
  nextInputs: string | undefined
): boolean {
  if (!prevOutputs || !nextInputs) return true;
  const outputs = prevOutputs.toLowerCase().trim();
  const inputs = nextInputs.toLowerCase().trim();
  if (outputs === "multimodal" || inputs === "multimodal") return true;
  return outputs === inputs;
}

export function useOperatorOperations() {
  const { id = "" } = useParams();
  const { message } = App.useApp();
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
      op.settings
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

  const [categoryOptions, setCategoryOptions] = useState([]);

  const initOperators = async () => {
    const [categoryRes, operatorRes] = await Promise.all([
      queryCategoryTreeUsingGet(),
      queryOperatorsUsingPost({ page: 0, size: 1000 }),
    ]);

    const operators = operatorRes.data.content.map(mapOperator);
    setOperators(operators || []);

    const options = categoryRes.data.content.reduce((acc: any[], item: any) => {
      const cats = item.categories.map((cat) => ({
        ...cat,
        type: item.name,
        label: cat.name,
        value: cat.id,
        icon: cat.icon,
        operators: operators.filter((op) => op[item.name] === cat.name),
      }));
      acc.push(...cats);
      return acc;
    }, [] as { id: string; name: string; icon: React.ReactNode }[]);

    setCategoryOptions(options);
  };

  const initTemplates = async () => {
    if (id) {
      const { data } = await queryCleaningTemplateByIdUsingGet(id);
      const template = {
        ...data,
        label: data.name,
        value: data.id,
      }
      setTemplates([template])
      setCurrentTemplate(template)
    } else {
      const { data } = await queryCleaningTemplatesUsingGet();
      const newTemplates =
        data.content?.map?.((item) => ({
          ...item,
          label: item.name,
          value: item.id,
        })) || [];
      setTemplates(newTemplates);
      setCurrentTemplate(newTemplates?.[0])
    }
  };

  useEffect(() => {
    setSelectedOperators(currentTemplate?.instance?.map(mapOperator) || []);
  }, [currentTemplate]);

  useEffect(() => {
    initTemplates();
    initOperators();
  }, []);

  useEffect(() => {
    const handleLanguageChange = () => {
      initOperators();
    };
    i18n.on('languageChanged', handleLanguageChange);
    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  const toggleOperator = (operator: OperatorI) => {
    const exist = selectedOperators.find((op) => op.id === operator.id);
    if (exist) {
      setSelectedOperators(
        selectedOperators.filter((op) => op.id !== operator.id)
      );
    } else {
      // Validate type compatibility with the last selected operator
      if (selectedOperators.length > 0) {
        const lastOp = selectedOperators[selectedOperators.length - 1];
        if (!checkTypeCompatible(lastOp.outputs, operator.inputs)) {
          message.warning(
            i18n.t("dataCleansing.create.typeMismatch", {
              from: lastOp.outputs,
              to: operator.inputs,
            })
          );
          return;
        }
      }
      setSelectedOperators([...selectedOperators, { ...operator }]);
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
    setSelectedOperators((prev) =>
      prev.map((op) =>
        op.id === operatorId
          ? {
            ...op,
            overrides: {
              ...(op?.overrides || op?.defaultParams),
              [paramKey]: value,
            },
            configs: {
              ...(op?.configs),
              [paramKey]: {
                ...(op?.configs[paramKey]),
                value: value,
              }
            }
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
    categoryOptions,
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
