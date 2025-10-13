import React from "react";
import { Tag, Divider, Form } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import ParamConfig from "./ParamConfig";

// OperatorConfig/OperatorTemplate 类型需根据主文件实际导入
interface OperatorConfigProps {
  selectedOp: any; // OperatorConfig
  renderParamConfig?: (
    operator: any,
    paramKey: string,
    param: any
  ) => React.ReactNode;
  onParamChange?: (operatorId: string, paramKey: string, value: any) => void;
}

const OperatorConfig: React.FC<OperatorConfigProps> = ({
  selectedOp,
  renderParamConfig,
  onParamChange,
}) => {
  return (
    <div className="w-1/4 flex flex-col h-screen">
      <div className="px-4 pb-4 border-b border-gray-200">
        <span className="font-semibold text-base flex items-center gap-2">
          <SettingOutlined />
          参数配置
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
              {Object.entries(selectedOp.settings).map(([key, param]) =>
                renderParamConfig ? (
                  renderParamConfig(selectedOp, key, param)
                ) : (
                  <ParamConfig
                    operator={selectedOp}
                    paramKey={key}
                    param={param}
                    onParamChange={onParamChange}
                  />
                )
              )}
            </Form>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <SettingOutlined className="text-5xl mb-4 opacity-50" />
            <div>请选择一个算子进行参数配置</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OperatorConfig;
