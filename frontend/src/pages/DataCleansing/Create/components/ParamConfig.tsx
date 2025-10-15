import React from "react";
import { Input, Select, Radio, Checkbox, Form, InputNumber, Slider } from "antd";
import { OperatorI } from "../../cleansing.model";

interface ParamConfigProps {
  operator: OperatorI;
  paramKey: string;
  param: any;
  onParamChange?: (operatorId: string, paramKey: string, value: any) => void;
}

const ParamConfig: React.FC<ParamConfigProps> = ({
  operator,
  paramKey,
  param,
  onParamChange,
}) => {
  const [value, setValue] = React.useState(param.value || param.default);
  const updateValue = (newValue: any) => {
    setValue(newValue);
    return onParamChange && onParamChange(operator.id, paramKey, newValue);
  };
  switch (param.type) {
    case "input":
      return (
        <Form.Item label={param.label} key={paramKey}>
          <Input
            value={value}
            onChange={(e) => updateValue(e.target.value)}
            placeholder={`请输入${param.label}`}
          />
        </Form.Item>
      );
    case "select":
      return (
        <Form.Item label={param.label} key={paramKey}>
          <Select
            value={value}
            onChange={updateValue}
            options={(param.options || []).map((option: any) =>
              typeof option === "string"
                ? { label: option, value: option }
                : option
            )}
            placeholder={`请选择${param.label}`}
            className="w-full"
          />
        </Form.Item>
      );
    case "radio":
      return (
        <Form.Item label={param.label} key={paramKey}>
          <Radio.Group
            value={value}
            onChange={(e) => updateValue(e.target.value)}
          >
            {(param.options || []).map((option: any) => (
              <Radio
                key={typeof option === "string" ? option : option.value}
                value={typeof option === "string" ? option : option.value}
              >
                {typeof option === "string" ? option : option.label}
              </Radio>
            ))}
          </Radio.Group>
        </Form.Item>
      );
    case "checkbox":
      return (
        <Form.Item label={param.label} key={paramKey}>
          <Checkbox.Group
            value={value}
            onChange={updateValue}
            options={param.options || []}
          />
        </Form.Item>
      );
    case "slider":
      return (
        <Form.Item label={param.label} key={paramKey}>
          <div className="flex items-center gap-1">
            <Slider
              value={value}
              onChange={updateValue}
              tooltip={{ open: true }}
              marks={{
                [param.min || 0]: param.minLabel || `${param.min || 0}`,
                [param.min + (param.max - param.min) / 2]:
                  param.midLabel || `${(param.min + param.max) / 2}`,
                [param.max || 100]: param.maxLabel || `${param.max || 100}`,
              }}
              min={param.min || 0}
              max={param.max || 100}
              step={param.step || 1}
            />
            <InputNumber
              min={param.min || 0}
              max={param.max || 100}
              step={param.step || 1}
              value={value}
              onChange={updateValue}
              style={{ width: 80 }}
            />
          </div>
        </Form.Item>
      );
    case "range":
      return (
        <Form.Item label={param.label} key={paramKey}>
          <Slider
            value={Array.isArray(value) ? value : [value, value]}
            onChange={(val) =>
              updateValue(Array.isArray(val) ? val : [val, val])
            }
            range
            marks={{
              [param.min || 0]: param.minLabel || `${param.min || 0}`,
              [param.min + (param.max - param.min) / 2]:
                param.midLabel || `${(param.min + param.max) / 2}`,
              [param.max || 100]: param.maxLabel || `${param.max || 100}`,
            }}
            min={param.min || 0}
            max={param.max || 100}
            step={param.step || 1}
          />
        </Form.Item>
      );
    default:
      return null;
  }
};

export default ParamConfig;
