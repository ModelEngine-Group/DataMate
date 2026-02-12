import React from "react";
import { Tag, Divider, Form } from "antd";
import ParamConfig from "./ParamConfig";
import { Settings } from "lucide-react";
import { OperatorI } from "@/pages/OperatorMarket/operator.model";
import { useTranslation } from "react-i18next";

// OperatorConfig/OperatorTemplate 类型需根据主文件实际导入
interface OperatorConfigProps {
  selectedOp: OperatorI;
  renderParamConfig?: (
    operator: OperatorI,
    paramKey: string,
    param: any
  ) => React.ReactNode;
  handleConfigChange?: (
    operatorId: string,
    paramKey: string,
    value: any
  ) => void;
}

const OperatorConfig: React.FC<OperatorConfigProps> = ({
  selectedOp,
  renderParamConfig,
  handleConfigChange,
}) => {
  const { t } = useTranslation();
  return (
    <div className="w-1/4 min-w-3xs flex flex-col h-full">
      <div className="px-4 pb-4 border-b border-gray-200">
        <span className="font-semibold text-base flex items-center gap-2">
          <Settings />
          {t("dataCleansing.actions.config")}
        </span>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {selectedOp ? (
          <div>
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium">{selectedOp.name}</span>
              </div>
              <div className="text-sm text-gray-500">
                {selectedOp.description}
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {selectedOp?.tags?.map((tag: string) => (
                  <Tag key={tag} color="default">
                    {tag}
                  </Tag>
                ))}
              </div>
            </div>
            <Divider />
            <Form layout="vertical">
              {Object.entries(selectedOp.configs).map(([key, param]) =>
                renderParamConfig ? (
                  renderParamConfig(selectedOp, key, param)
                ) : (
                  <ParamConfig
                    key={key}
                    operator={selectedOp}
                    paramKey={key}
                    param={param}
                    onParamChange={handleConfigChange}
                  />
                )
              )}
            </Form>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <Settings className="w-full w-10 h-10 mb-4 opacity-50" />
            <div>{t("dataCleansing.actions.selectOperatorConfig")}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OperatorConfig;
