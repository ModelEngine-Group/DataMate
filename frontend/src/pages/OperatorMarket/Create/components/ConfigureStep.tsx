import {Alert, Input, Form} from "antd";
import TextArea from "antd/es/input/TextArea";
import React, {useEffect} from "react";
import ParamConfig from "@/pages/DataCleansing/Create/components/ParamConfig.tsx";

export default function ConfigureStep({
  parsedInfo,
  parseError,
  setParsedInfo,
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(parsedInfo);
  }, [parsedInfo]);

  const handleConfigChange = (
    operatorId: string,
    paramKey: string,
    value: any
  ) => {
    setParsedInfo((op) =>
      op.id === operatorId
        ? {
          ...op,
          overrides: {
            ...(op?.overrides || op?.defaultParams),
            [paramKey]: value,
          },
        }
        : op
    )
  };

  return (
    <>
      {/* 解析结果 */}
      {parseError && (
        <div className="mb-4">
          <Alert
            message="解析过程中发现问题"
            description={parseError}
            type="error"
            showIcon
          />
        </div>
      )}

      {!parseError && parsedInfo && (
        <Form
          form={form}
          layout="vertical"
          initialValues={parsedInfo}
          onValuesChange={(_, allValues) => {
            setParsedInfo({...parsedInfo, ...allValues});
          }}
        >
          {/* 基本信息 */}
          <h3 className="text-lg font-semibold text-gray-900">基本信息</h3>
          <Form.Item label="ID" name="id" rules={[{required: true}]}>
            <Input value={parsedInfo.id} readOnly/>
          </Form.Item>
          <Form.Item label="名称" name="name" rules={[{required: true}]}>
            <Input value={parsedInfo.name}/>
          </Form.Item>
          <Form.Item label="版本" name="version" rules={[{required: true}]}>
            <Input value={parsedInfo.version}/>
          </Form.Item>
          <Form.Item
            label="描述"
            name="description"
            rules={[{required: false}]}
          >
            <TextArea value={parsedInfo.description}/>
          </Form.Item>
          <Form.Item label="输入类型" name="inputs" rules={[{required: true}]}>
            <Input value={parsedInfo.inputs}/>
          </Form.Item>
          <Form.Item label="输出类型" name="outputs" rules={[{required: true}]}>
            <Input value={parsedInfo.outputs}/>
          </Form.Item>

          {parsedInfo.configs && (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mt-10 mb-2">
                高级配置
              </h3>
              <div className="border p-4 rounded-lg grid grid-cols-2 gap-4">
                <Form layout="vertical">
                  {Object.entries(parsedInfo?.configs).map(([key, param]) =>
                    <ParamConfig
                      key={key}
                      operator={parsedInfo}
                      paramKey={key}
                      param={param}
                      onParamChange={handleConfigChange}
                    />
                  )}
                </Form>
              </div>
            </>
          )}

          {/* <h3 className="text-lg font-semibold text-gray-900 mt-8">高级配置</h3> */}
        </Form>
      )}
    </>
  );
}
